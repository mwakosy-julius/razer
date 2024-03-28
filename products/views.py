from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from .forms import CheckoutForm
from .forms import SignUpForm
from .models import (
    Item,
    Order,
    OrderItem,
    CheckoutAddress,
    Payment,
    Category
)

import stripe
stripe.api_key = settings.STRIPE_KEY

# Create your views here.
class HomeView(ListView):
    model = Item
    template_name = "home.html"
    context_object_name = 'items'  # Specify the context object name for the template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items_list = context['items']  # Retrieve items queryset from the context

        # Number of items per page
        items_per_page = 12

        # Get the queryset
        items_list = Item.objects.all()

        print("Number of items before pagination:", len(items_list))#debugging

        paginator = Paginator(items_list, items_per_page)

        page_number = self.request.GET.get('page')
        try:
            items = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            items = paginator.page(paginator.num_pages)

        context['items'] = items  # Update context with paginated items
        return context


class ProductView(DetailView):
    model = Item
    template_name = "product.html"

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an order")
            return redirect("/")

class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'form': form,
            'order': order
        }
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                # TODO: add functionaly for these fields
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')

                checkout_address = CheckoutAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip
                )
                checkout_address.save()
                order.checkout_address = checkout_address
                order.save()

                if payment_option == 'S':
                    return redirect('cproducts:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('products:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid Payment option")
                    return redirect('products:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an order")
            return redirect("products:order-summary")

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'order': order
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total_price() * 100)  #cents

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token
            )

            # create payment
            payment = Payment()
            payment.stripe_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total_price()
            payment.save()

            # assign payment to order
            order.ordered = True
            order.payment = payment
            order.save()

            messages.success(self.request, "Success make an order")
            return redirect('/')

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f"{err.get('message')}")
            return redirect('/')

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "To many request error")
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid Parameter")
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Authentication with stripe failed")
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Network Error")
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong")
            return redirect('/')
        
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "Not identified error")
            return redirect('/')
        
def search(request):
    query = request.GET.get('query')
    if query:
        items = Item.objects.filter(item_name__icontains=query)
    else:
        items = Item.objects.all()
    return render(request, 'search.html', {'items': items, 'query': query})


def category(request, brand):

    #lookup the brand from the url
    try:
        category = Category.objects.get(name=brand)
        brands = Item.objects.filter(category=category)
        return render(request, 'category.html', {'brands':brands,'category':category})
    
    except:
        messages.success(request, ("That category doesn't exist...."))
        return redirect('/')

def login_user(request):
    if request.method == "post":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None: 
           login(request, user) 
           messages.info(request, "You have been logged in.")
           return redirect('/')

    else:
           
     return render(request, 'registration/login.html', {})
        
def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out."))
    return redirect('/')

def register_user(request):
    form = SignUpForm()
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save() 
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']

            user = authenticate(username= username, password =  password )
            login(request,user)
            messages.success(request, ("You have been registered successfully!!"))
            return redirect('/')
        else:
            messages.success(request, ("Whoops! There was a problem, please try again!"))
            return redirect('products:register')
    else:
        return render(request, 'registration/register.html', {'form':form})

@login_required
def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk )
    order_item, created = OrderItem.objects.get_or_create(
        item = item,
        user = request.user,
        ordered = False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]

        if order.items.filter(item__pk=item.pk).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Added quantity Item")
            return redirect("products:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to your cart")
            return redirect("products:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item added to your cart")
        return redirect("products:order-summary")

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(Item, pk=pk )
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order_item.delete()
            messages.info(request, "Item \""+order_item.item.item_name+"\" remove from your cart")
            return redirect("products:order-summary")
        else:
            messages.info(request, "This Item not in your cart")
            return redirect("products:product", pk=pk)
    else:
        #add message doesnt have order
        messages.info(request, "You do not have an Order")
        return redirect("products:product", pk = pk)


@login_required
def reduce_quantity_item(request, pk):
    item = get_object_or_404(Item, pk=pk )
    order_qs = Order.objects.filter(
        user = request.user, 
        ordered = False
    )
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists() :
            order_item = OrderItem.objects.filter(
                item = item,
                user = request.user,
                ordered = False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Item quantity was updated")
            return redirect("products:order-summary")
        else:
            messages.info(request, "This Item not in your cart")
            return redirect("products:order-summary")
    else:
        #add message doesnt have order
        messages.info(request, "You do not have an Order")
        return redirect("products:order-summary")