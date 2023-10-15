from django.urls import path
from . import views


urlpatterns = [
    #path('', views.home, name='home'),
    path('', views.index, name=''),
    path('<int:product_id>/', views.description, name='description'),
]