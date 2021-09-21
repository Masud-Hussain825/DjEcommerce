from typing import List
from django.shortcuts import get_object_or_404, redirect, render
from .models import Item , Order , OrderItem
from django.views.generic import ListView , DetailView
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages

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

def add_to_cart(request , slug):
    item = get_object_or_404(Item , slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        user = request.user,
        item = item,
        ordered = False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if the item is in the cart
        if order.items.filter(item__slug = item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.success(request ,'quantity of this item was increased successfully')
        else:
            order.items.add(order_item)
            messages.success(request ,'this item was added to your cart successfully')
    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user , ordered_date = order_date)
        order.items.add(order_item)
        messages.success(request ,'this item was added to your cart successfully')

    return redirect("core:ItemDetails" , slug=slug)


def remove_from_cart(request , slug):
    item = get_object_or_404(Item , slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if the item is in the cart
        if order.items.filter(item__slug = item.slug).exists():
            order_item = OrderItem.objects.filter(
                user = request.user,
                item = item,
                ordered = False
            )[0]
            order.items.remove(order_item)
            messages.warning(request , 'This item was removed from your cart')
            return redirect("core:ItemDetails" , slug=slug)
        else:
            messages.info(request , 'This item was not added to your cart')
            return redirect("core:ItemDetails" , slug=slug)
    else:
        messages.error(request , "you don't have any active order")
        return redirect("core:ItemDetails" , slug=slug)