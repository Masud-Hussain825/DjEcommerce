from django.http import request
from django.http.response import HttpResponseRedirect
from core.forms import CheckoutForm
from typing import List
from django.shortcuts import get_object_or_404, redirect, render
from .models import BillingAddress, Item , Order , OrderItem, Payment
from django.views.generic import ListView , DetailView , View
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from core import models
from django.urls import reverse
from sslcommerz_python.payment import SSLCSession
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

class HomePage(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home-page.html'

class ItemDetails(DetailView):
    model = Item
    template_name = 'product-page.html'


class Checkout(View):
    def get(self, *args , **kwargs):
        form = CheckoutForm()
        context = {
            'form' : form
        }
        return render(self.request , "checkout-page.html" , context)

    def post(self, *args , **kwargs):
        form = CheckoutForm(self.request.POST)
        if form.is_valid():
            try:
                order = Order.objects.get(user=self.request.user , ordered = False)
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                zip = form.cleaned_data.get('zip')
                # save_billing_address = form.cleaned_data.get('save_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = models.BillingAddress(
                    user = self.request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    countries = country,
                    zip = zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                return redirect('core:Payment')
            except ObjectDoesNotExist:
                messages.error(self.request , 'You do not have and active order')
                return redirect('/')
        messages.warning(self.request, 'Failed Checkout')
        return redirect('core:Checkout')

class orderSummaryView(View , LoginRequiredMixin):
    def get(self , *args , **kwargs):
        try:
            order = Order.objects.get(user=self.request.user , ordered = False)
            context = {
                'object' : order
            }
            return render(self.request , 'order_summary.html' , context)
        except ObjectDoesNotExist:
            messages.error(self.request , 'You do not have and active order')
            return redirect('/')


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

    return redirect("core:OrderSummary")


def remove_item_from_cart(request , slug):
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
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.warning(request ,'The item quantity was updated')
            return redirect("core:OrderSummary")
        else:
            messages.info(request , 'This item was not added to your cart')
            return redirect("core:ItemDetails")
    else:
        messages.error(request , "you don't have any active order")
        return redirect("core:ItemDetails")


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
            return redirect("core:OrderSummary")
        else:
            messages.info(request , 'This item was not added to your cart')
            return redirect("core:ItemDetails" , slug=slug)
    else:
        messages.error(request , "you don't have any active order")
        return redirect("core:ItemDetails" , slug=slug)

class PaymentView(View):
    def get(self , *args , **kwargs):
        print(self.request.user.email)

        mypayment = SSLCSession(sslc_is_sandbox=True, sslc_store_id='abc61533e83e5f44', sslc_store_pass='abc61533e83e5f44@ssl')
        
        status_url = self.request.build_absolute_uri(reverse("core:Complete"))
        print(status_url)
        mypayment.set_urls(success_url=status_url, fail_url=status_url, cancel_url=status_url, ipn_url=status_url)

        order_qs = Order.objects.filter(user=self.request.user , ordered=False)
        order_item_count = order_qs[0].items.count()
        order_total = order_qs[0].get_total()
        mypayment.set_product_integration(total_amount=Decimal(order_total), currency='BDT', product_category='mixed', product_name='mixed', num_of_item=order_item_count, shipping_method='Courier', product_profile='None')

        saved_address = BillingAddress.objects.filter(user = self.request.user)
        saved_address = saved_address[0]

        mypayment.set_customer_info(name=self.request.user.username, email=self.request.user.email , address1=saved_address.apartment_address, address2=saved_address.street_address, city='none', postcode=saved_address.zip, country='bangladesh', phone='01743873476' )

        mypayment.set_shipping_info(shipping_to=saved_address.user, address=saved_address.apartment_address, city=saved_address.street_address, postcode=saved_address.zip, country = 'bangladesh')

        response_data = mypayment.init_payment()
        print(response_data)


        return redirect(response_data['GatewayPageURL'])

@csrf_exempt
def complete(request):
    if request.method == 'POST' or request.method == 'post':
        payment_data = request.POST
        status = payment_data['status']
        print(payment_data)
        print(status)
        if status == 'VALID':
            tran_id = payment_data['tran_id']
            amount = payment_data['amount']
            messages.success(request , 'Successfully order completed') 
            return HttpResponseRedirect(reverse('core:Purchase' , kwargs={'tran_id':tran_id ,'amount' : amount }))
        elif status == 'FAILED':
            messages.success(request ,'there was an error while doing payment')
    return render(request , 'complete.html' , context={})

def purchase(request , tran_id , amount):
    payment = Payment.objects.create(
        user = request.user,
        tran_id = tran_id,
        amount = amount,
    )
    order_qs = Order.objects.filter(user = request.user)
    order = order_qs[0]
    order.ordered = True
    order.payment = payment
    order.save()
    orderitems = OrderItem.objects.filter(user=request.user, ordered = False)
    orderitems = orderitems[0]
    orderitems.ordered = True
    orderitems.save()
    return HttpResponseRedirect(reverse('core:Home'))