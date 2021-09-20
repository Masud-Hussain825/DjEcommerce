from typing import List
from django.shortcuts import render
from .models import Item , Order , OrderItem
from django.views.generic import ListView , DetailView

from core import models
# Create your views here.

class HomePage(ListView):
    model = Item
    template_name = 'home-page.html'

class ItemDetails(DetailView):
    model = Item
    template_name = 'product-page.html'

def checkout(request):
    return render(request , 'checkout-page.html' )
