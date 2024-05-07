from django.shortcuts import render, redirect
from .models import Producto, Carrito, CarritoProducto



def index(request):
    # productos = Producto.objects.all()
    return render(request, 'index.html')   #, {'productos': productos}

def agregar_al_carrito(request, producto_id):
    carrito, _ = Carrito.objects.get_or_create(sesion_id=request.session.session_key or 'default')
    producto = Producto.objects.get(pk=producto_id)
    CarritoProducto.objects.create(carrito=carrito, producto=producto, cantidad=1)
    return redirect('index')

def ver_carrito(request):
    carrito, _ = Carrito.objects.get_or_create(sesion_id=request.session.session_key or 'default')
    items_en_carrito = CarritoProducto.objects.filter(carrito=carrito)
    return render(request, 'carrito.html', {'items': items_en_carrito})


