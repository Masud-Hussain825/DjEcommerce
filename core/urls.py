from django.contrib import admin
from django.urls import path 
from . import views

app_name = 'core'

urlpatterns = [
    path('' , views.HomePage.as_view() , name='Home'),
    path('products/<slug>/' , views.ItemDetails.as_view() , name='ItemDetails'),
    path('checkout/' , views.checkout , name='Checkout')
]