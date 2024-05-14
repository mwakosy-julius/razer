from django.urls import path, reverse
from .views import (
    remove_from_cart,
    reduce_quantity_item,
    add_to_cart,
    ProductView,
    HomeView,
    OrderSummaryView,
    CheckoutView,
    PaymentView,
    register_user,
    login_user,
    logout_user,
    category,
    search
    
)
app_name ='products'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', login_user, name='login'),
    path('accounts/logout/', logout_user, name='logout'),
    path('category/<str:brand>', category, name = 'category'),
    path('register/', register_user, name='register'),
    path('product/<pk>/', ProductView.as_view(), name='product'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('add-to-cart/<pk>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<pk>/', remove_from_cart, name='remove-from-cart'),
    path('reduce-quantity-item/<pk>/', reduce_quantity_item, name='reduce-quantity-item'),
    path('search/', search, name='searched'),
]