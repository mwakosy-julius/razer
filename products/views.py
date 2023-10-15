from django.http import HttpResponse
from django.shortcuts import render
from .models import Product

def home(request):
    return render(request, 'home.html')

def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})

def description(request, product_id):
    product = Product.objects.get(pk=product_id)
    return render(request, 'description.html', {'product': product})