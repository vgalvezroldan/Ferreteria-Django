from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
]
