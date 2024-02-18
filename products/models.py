from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField

CATEGORY = (
    ('A', 'Apple'),
    ('HP', 'HP'),
    ('acer', 'Acer'),
    ('MS', 'Microsoft'),
    ('R', 'Razer'),
    ('Huaw', 'Huawei'),
    ('Del', 'Dell'),
    ('Ln', 'Lenovo'),
    ('AS', 'Asus'),
    ('Thin', 'ThinkPad'),
)

LABEL = (
    ('N', 'New'),
    ('BS', 'Best deal')
)

class Item(models.Model):
    item_name = models.CharField(max_length=100)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=11)
    discount_price = models.DecimalField(default=0, decimal_places=2, max_digits=11, blank=True, null=True)
    category = models.CharField(choices=CATEGORY, max_length=10)
    label = models.CharField(choices=LABEL, max_length=10)
    description = models.TextField(default='', blank=True,null=True)
    image = models.ImageField(upload_to='uploads/product/')

    def __str__(self):
        return self.item_name

    def get_absolute_url(self):
        return reverse("products:product", kwargs={
            "pk" : self.pk
        
        })

    def get_add_to_cart_url(self):
        return reverse("products:add-to-cart", kwargs={
            "pk" : self.pk
        })

    def get_remove_from_cart_url(self):
        return reverse("products:remove-from-cart", kwargs={
            "pk" : self.pk
        })

class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.item_name}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_discount_item_price()
        return self.get_total_item_price()
    
    

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    checkout_address = models.ForeignKey(
        'CheckoutAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    def get_total_price(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total


class CheckoutAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username
    
class Payment(models.Model):
    stripe_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(default=0, decimal_places=2, max_digits=11)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    