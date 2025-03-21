from django.contrib.auth.models import Group, User
from rest_framework import viewsets
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