from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuItemViewSet,
    CategoryViewSet,
    cartView,
    OrderViewSet,
    ManagerGroupview,
    DeliveryCrewGroup,
)

# Create a router for ViewSets
router = DefaultRouter()

# Register ViewSets with the router
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'orders', OrderViewSet, basename='order')


urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),

    # Cart endpoints
    path('cart/menu-items/', cartView.as_view(), name='cart'),

    # Manager group endpoints
    path('groups/manager/users/', ManagerGroupview.as_view(), name='manager-group'),
    path('groups/manager/users/<int:userId>/', ManagerGroupview.as_view(), name='manager-group-detail'),

    # Delivery Crew group endpoints
    path('groups/delivery-crew/users/', DeliveryCrewGroup.as_view(), name='delivery-crew-group'),
    path('groups/delivery-crew/users/<int:userId>/', DeliveryCrewGroup.as_view(), name='delivery-crew-group-detail'),
]