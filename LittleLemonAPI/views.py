from django.contrib.auth.models import Group, User
from rest_framework import viewsets, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import *
from .serializers import *
from . permissions import *

# Create your views here.

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
    filter_fields = ['category', 'price', 'featured'] # Fields to filter by
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