from django.contrib import admin
from django.urls import path 
from . import views

app_name = 'core'

urlpatterns = [
    path('' , views.HomePage.as_view() , name='Home'),
    path('products/<slug>/' , views.ItemDetails.as_view() , name='ItemDetails'),
    path('checkout/' , views.checkout , name='Checkout'),
    path('add-to-cart/<slug>/', views.add_to_cart , name="AddToCart"),
    path('remove-from-cart/<slug>/', views.remove_from_cart , name="RemoveFromCart"),
]