from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.CharField(max_length=255)
    stock = models.IntegerField()
    image_url = models.CharField(max_length=2083)
    description = models.JSONField()