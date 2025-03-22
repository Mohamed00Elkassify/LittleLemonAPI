from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import *
from .serializers import *
from .permissions import *

# ViewSet for Menu Items
class MenuItemViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Menu Items.
    - Managers and Admins can create, update, and delete menu items.
    - All authenticated users can view menu items.
    - Supports filtering by category, price, and featured status.
    - Supports sorting by price and title.
    - Supports searching by title.
    """
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter] # Enable filtering, ordering, and searching
    filterset_fields = ['category', 'price', 'featured'] # Fields to filter by
    ordering_fields = ['price', 'title'] # Fields to sort by
    search_fields = ['title'] # Fields to search by

    def get_permissions(self):
        """
        Customize permissions based on the action:
        - Only Managers and Admins can create, update, or delete menu items.
        - All authenticated users can view menu items.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsManager | IsAdminUser] # Restrict to Managers and Admins
        else:
            permission_classes = [IsAuthenticated] # Allow all authenticated users
        return [permission() for permission in permission_classes]

# ViewSet for Categories
class CategoryViewSet(viewsets.ViewSet):
    """
    Handles CRUD operations for Categories.
    - Managers and Admins can create, update, and delete categories.
    - All authenticated users can view categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        """
        Customize permissions based on the action:
        - Only Managers and Admins can create, update, or delete categories.
        - All authenticated users can view categories.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsManager | IsAdminUser] # Restrict to Managers and Admins
        else:
            permission_classes = [IsAuthenticated] # Allow all authenticated users
        return [permission() for permission in permission_classes]

# View for Cart operations
class cartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    """
    Handles operations for the user's shopping cart:
    - Customers can view, add, and delete items in their cart.
    - Automatically calculates unit_price and total_price when adding items.
    """
    serializer_class = CartSerializer
    permission_classes = [IsCustomer] # Only customers can access the cart

    def get_queryset(self):
        """
        Fetch cart items for the current user.
        """
        return Cart.objects.all().filter(user = self.request.user)
    
    def perform_create(self, serializer):
        """
        Custom logic for adding items to the cart:
        - Calculate unit_price and total_price based on the menu item's price and quantity.
        - Automatically set the user to the current user.
        """
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']
        unit_price = menuitem.price
        total_price = quantity * unit_price
        serializer.save(user=self.request.user, unit_price=unit_price, total_price=total_price)
    
    def delete(self, request, *args, **kwargs):
        """
        Delete all items in the cart for the current user.
        """
        self.get_queryset().delete()
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)

# ViewSet of Orders
class OrderViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Orders.
    - Managers and Admins can view all orders.
    - Delivery Crew can view orders assigned to them.
    - Customers can view and create their own orders.
    - Supports filtering by status and date.
    - Supports sorting by date and total.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated] # Only authenticated users can access orders
    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Enable filtering and sorting
    filterset_fields = ['status', 'date']  # Fields to filter by
    ordering_fields = ['date', 'total']  # Fields to sort by

    def get_queryset(self):
        """
        Fetch orders based on the user's role:
        - Managers and Admins can view all orders.
        - Delivery Crew can view orders assigned to them.
        - Customers can view their own orders.
        """
        user = self.request.user
        if IsManager().has_permission(self.request, self) or IsAdminUser().has_permission(self.request, self):
            return Order.objects.all()  # Managers and Admins see all orders
        elif IsDeliveryCrew().has_permission(self.request, self):
            return Order.objects.filter(delivery_crew=user)  # Delivery Crew see orders assigned to them
        else:
            return Order.objects.filter(user=user)  # Customers see their own orders

    def perform_create(self, serializer):
        """
        Custom logic for creating an order:
        - Create an order from the items in the cart.
        - Calculate the total price and create OrderItem records.
        - Delete the cart items after the order is created.
        """
        cart_items = Cart.objects.filter(user=self.request.user)  # Get cart items for the current user
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        total = sum(item.total_price for item in cart_items)
        order = serializer.save(user=self.request.user, total=total)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
            )
        cart_items.delete() # Delete all cart items for the user
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Custom logic for updating an order:
        - Only managers can update the delivery_crew field.
        - Customers and delivery crew can only update the status field.
        """
        instance = self.get_object()
        user = request.user

        # Check if the user is trying to update the delivery_crew field
        if 'delivery_crew' in request.data and not (IsManager().has_permission(request, self) or IsAdminUser().has_permission(request, self)):
            return Response(
                {'error': 'Only managers can update the delivery crew.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if the user is trying to update the status field
        if 'status' in request.data and not (IsManager().has_permission(request, self) or IsAdminUser().has_permission(request, self) or IsDeliveryCrew().has_permission(request, self)):
            return Response(
                {'error': 'Only managers, admins, or delivery crew can update the status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
# View for Manager Group operations
class ManagerGroupview(APIView):
    """
    Handles operations for the Manager group.
    - Admins and Managers can list, add, and remove users from the Manager group.
    """
    permission_classes = [IsManager | IsAdminUser] # Only Admins and Managers can access this view
    def get(self, request):
        """
        List all users in the Manager group.
        """
        managers = Group.objects.get(name='Manager').user_set.all()
        serializer = UserSerializer(managers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """
        Add a user to the Manager group.
        """
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.add(user)
        return Response({'message': f'{username} added to Manager group'}, status=status.HTTP_201_CREATED)
    
    def delete(self, request, userId):
        """
        Remove a user from the Manager group.
        """
        user = get_object_or_404(User, id=userId)
        manager_group = Group.objects.get(name='Manager')
        manager_group.user_set.remove(user)
        return Response({'message': f'{user.username} removed from Manager group'}, status=status.HTTP_200_OK)

# View for the Delivery Crew Group operations
class DeliveryCrewGroup(APIView):
    """
    Handles operations for the Delivery Crew group.
    - Admins and Managers can list, add, and remove users from the Delivery Crew group.
    """
    permission_classes = [IsAdminUser | IsManager]  # Only Admins and Managers can access this view
    
    def get(self, request):
        """
        List all users in the Delivery Crew group.
        """
        delivery_crew = Group.objects.get(name='Delivery Crew').user_set.all()
        serializer = UserSerializer(delivery_crew, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Add a user to the Delivery Crew group.
        """
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
        delivery_crew_group.user_set.add(user)
        return Response({'message': f'{username} added to Delivery Crew group'}, status=status.HTTP_201_CREATED)

    def delete(self, request, userId):
        """
        Remove a user from the Delivery Crew group.
        """
        user = get_object_or_404(User, id=userId)
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
        delivery_crew_group.user_set.remove(user)
        return Response({'message': f'{user.username} removed from Delivery Crew group'}, status=status.HTTP_200_OK)