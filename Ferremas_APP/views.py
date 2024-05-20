from django.shortcuts import get_object_or_404, render, redirect
from .models import Producto, Carrito, CarritoProducto, Pedido, Transaccion
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from decimal import Decimal
from django.urls import reverse
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from django.conf import settings
from transbank.error.transbank_error import TransbankError
import random
from .forms import PedidoForm
from .utils import enviar_correo_confirmacion, obtener_tipo_cambio, SERIES_CODIGOS


def index(request):
    productos = Producto.objects.all()
    return render(request, 'index.html', {'productos': productos})

@require_POST # Solo se aceptan peticiones POST
def agregar_al_carrito(request, producto_id): # Se recibe el id del producto
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    if not carrito_id: # Si no existe un carrito en la sesión
        nuevo_carrito = Carrito.objects.create() # Se crea un nuevo carrito
        request.session["carrito_id"] = nuevo_carrito.id # Se guarda el id del carrito en la sesión
    else:   # Si ya existe un carrito en la sesión
        nuevo_carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito existente
    
    producto = get_object_or_404(Producto, pk=producto_id)  # Se obtiene el producto a agregar al carrito
    if producto.stock > 0: # Si el producto tiene stock
        carrito_producto, created = CarritoProducto.objects.get_or_create( # Se obtiene o crea un CarritoProducto
            carrito=nuevo_carrito, # Se asocia al carrito
            producto=producto, # Se asocia al producto
            defaults={'cantidad': 1} # Se establece la cantidad en 1
        )
        if not created: # Si el CarritoProducto ya existía
            if carrito_producto.cantidad < producto.stock: # Si la cantidad es menor al stock
                carrito_producto.cantidad += 1 # Se incrementa la cantidad
                carrito_producto.save() # Se guarda el CarritoProducto
        return JsonResponse({'mensaje': "Producto agregado al carrito"}) # Se responde con un mensaje
    else: # Si el producto no tiene stock
        return JsonResponse({'mensaje': "Producto sin stock"}, status=400) # Se responde con un mensaje de error
    
def ver_carrito(request): # Vista para ver el contenido del carrito
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    if carrito_id: # Si existe un carrito en la sesión
        carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
        productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito) # Se obtienen los productos del carrito
        productos = [ # Se crea una lista con los productos del carrito
            {'id': cp.producto.id, 'nombre': cp.producto.nombre, 'cantidad': cp.cantidad, 'precio': cp.producto.precioOferta} # Se crea un diccionario con los datos del producto
            for cp in productos_en_carrito # Se recorren los productos del carrito
        ]
        total = sum(cp.cantidad * cp.producto.precioOferta for cp in productos_en_carrito) # Se calcula el total del carrito
        return JsonResponse({'productos': productos, 'total': float(total)}) # Se responde con los productos y el total
    else: # Si no existe un carrito en la sesión
        return JsonResponse({'productos': [], 'total': 0.0}) # Se responde con una lista vacía y total 0.0

@require_POST # Solo se aceptan peticiones POST
def actualizar_carrito(request, producto_id): # Vista para actualizar la cantidad de un producto en el carrito
    try: # Se intenta realizar la operación
        data = json.loads(request.body) # Se obtiene la información del cuerpo de la petición
        cantidad = int(data.get('cantidad', 0)) # Se obtiene la cantidad del producto
        carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión

        if carrito_id: # Si existe un carrito en la sesión
            carrito_producto = get_object_or_404(CarritoProducto, carrito_id=carrito_id, producto_id=producto_id) # Se obtiene el CarritoProducto
            if cantidad > 0 and cantidad <= carrito_producto.producto.stock: # Si la cantidad es mayor a 0 y menor o igual al stock
                carrito_producto.cantidad = cantidad # Se actualiza la cantidad
                carrito_producto.save() # Se guarda el CarritoProducto
            elif cantidad == 0: # Si la cantidad es 0
                carrito_producto.delete() # Se elimina el CarritoProducto
            # Calcular el total del carrito después de actualizar
            productos_en_carrito = CarritoProducto.objects.filter(carrito_id=carrito_id) # Se obtienen los productos del carrito
            total_carrito = sum(item.cantidad * item.producto.precioOferta for item in productos_en_carrito) # Se calcula el total del carrito
            return JsonResponse({'mensaje': 'Cantidad actualizada correctamente', 'totalCarrito': float(total_carrito)}) # Se responde con un mensaje y el total del carrito
        return JsonResponse({'mensaje': 'Error al actualizar el carrito'}, status=400) # Si no existe un carrito en la sesión, se responde con un mensaje de error
    except Exception as e: # Si ocurre un error
        return JsonResponse({'mensaje': str(e)}, status=500) # Se responde con un mensaje de error


@require_POST # Solo se aceptan peticiones POST
def eliminar_del_carrito(request, producto_id): # Vista para eliminar un producto del carrito
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    if not carrito_id: # Si no existe un carrito en la sesión
        return JsonResponse({'mensaje': "No existe el carrito"}, status=404) # Se responde con un mensaje de error

    try: # Se intenta realizar la operación
        carrito_producto = CarritoProducto.objects.get(carrito_id=carrito_id, producto_id=producto_id) # Se obtiene el CarritoProducto
        carrito_producto.delete() # Se elimina el CarritoProducto
        return JsonResponse({'mensaje': 'Producto eliminado del carrito'}) # Se responde con un mensaje
    except CarritoProducto.DoesNotExist: # Si el CarritoProducto no existe
        return JsonResponse({'mensaje': 'Producto no encontrado en el carrito'}, status=404) # Se responde con un mensaje de error

def construccion(request): 
    return render(request, 'construccion.html')

def herramientas(request):
    return render(request, 'herramientas.html')

def hogar(request):
    return render(request, 'hogar.html')

def piso_y_pared(request):
    return render(request, 'piso-y-pared.html')

def formulario_datos(request): # Vista para el formulario de datos del pedido
    pedido_id = request.session.get("pedido_id") # Se obtiene el id del pedido de la sesión
    if request.method == 'POST': # Si se envió el formulario
        form = PedidoForm(request.POST) # Se crea un formulario con los datos enviados
        if form.is_valid(): # Si el formulario es válido
            if pedido_id: # Si ya existe un pedido
                pedido = Pedido.objects.get(id=pedido_id) # Se obtiene el pedido
                form = PedidoForm(request.POST, instance=pedido) # Se crea un formulario con los datos del pedido
            else: # Si no existe un pedido
                pedido = form.save(commit=False) # Se guarda el formulario sin enviar a la base de datos
                pedido.numero_pedido = f"{random.randint(1, 999):03d}" # Se genera un número de pedido aleatorio
            pedido.save() # Se guarda el pedido
            request.session['pedido_id'] = pedido.id # Se guarda el id del pedido en la sesión
            return redirect('carrito') # Se redirige al carrito
    else: 
        if pedido_id: # Si ya existe un pedido
            pedido = Pedido.objects.get(id=pedido_id)   # Se obtiene el pedido
            form = PedidoForm(instance=pedido) # Se crea un formulario con los datos del pedido
        else:
            form = PedidoForm() # Se crea un formulario vacío

    return render(request, 'formulario_datos.html', {'form': form}) # Se renderiza el formulario


def carrito(request): # Vista para el carrito de compras
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    pedido_id = request.session.get("pedido_id") # Se obtiene el id del pedido de la sesión
    if not pedido_id: # Si no existe un pedido en la sesión
        return redirect('formulario_datos') # Se redirige al formulario de datos
    
    if carrito_id: # Si existe un carrito en la sesión
        carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
        productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito) # Se obtienen los productos del carrito
        productos = [ # Se crea una lista con los productos del carrito
            {
                'id': cp.producto.id,
                'nombre': cp.producto.nombre,
                'descripcion': cp.producto.descripcion,
                'detalleCompleto': cp.producto.detalleCompleto,
                'precio': cp.producto.precioOferta,
                'cantidad': cp.cantidad,
                'imagen': cp.producto.imagen.url if cp.producto.imagen else '',
                'total': cp.cantidad * cp.producto.precioOferta,  # Total para cada producto
            }
            for cp in productos_en_carrito
        ]
        total = sum(cp['total'] for cp in productos) # Total de todos los productos
        iva = total * Decimal('0.19') # IVA del 19%
        total_con_iva = total + iva # Total con IVA

        contexto = { # Se crea un diccionario con los datos a enviar al template
            'productos': productos, 
            'total': total,
            'iva': iva,
            'total_con_iva': total_con_iva,
        }
        return render(request, 'carrito.html', contexto) # Se renderiza el carrito
    else:
        return render(request, 'carrito.html', {'productos': []}) # Si no existe un carrito en la sesión, se renderiza el carrito con una lista vacía

def iniciar_pago(request): # Vista para iniciar el proceso de pago
    if request.method == "POST": # Si se envió el formulario 
        total_con_iva = request.POST.get("total_con_iva") # Se obtiene el total con IVA
        total_con_iva = total_con_iva.replace('.', '').replace(',', '.')  # Eliminar separadores de miles y ajustar el separador decimal
        total_con_iva = int(float(total_con_iva))  # Convertir a entero

        carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
        
        if carrito_id and total_con_iva: # Si existe un carrito en la sesión y el total con IVA
            carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
            tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, settings.WEBPAY_PLUS_INTEGRATION_TYPE)) # Se crea una transacción

            response = tx.create( # Se crea la transacción
                buy_order=str(carrito.id), # Usar el id del carrito como orden de compra
                session_id=request.session.session_key, # Usar el id de sesión de Django
                amount=total_con_iva,  # Usar total con IVA como entero
                return_url=request.build_absolute_uri(reverse('webpay_confirmacion')) # URL de confirmación
            )

            return redirect(response['url'] + '?token_ws=' + response['token']) # Redirigir a la URL de Webpay con el token
        else:
            return redirect('carrito') # Si no existe un carrito en la sesión o el total con IVA, redirigir al carrito

def webpay_confirmacion(request): # Vista para confirmar el pago
    token = request.GET.get('token_ws') # Se obtiene el token de la URL

    if not token: # Si no se recibe el token
        return render(request, 'pago_fallido.html', {'mensaje': 'Token no recibido'}) # Se renderiza una página de error

    try: # Se intenta realizar la operación
        tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, IntegrationType.TEST)) # Se crea una transacción
        response = tx.commit(token=token) # Se confirma la transacción

        if response['status'] == 'AUTHORIZED': 
            # Vaciar el carrito y actualizar el stock
            carrito_id = response['buy_order'] # El id del carrito es el buy_order
            carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
            productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito) # Se obtienen los productos del carrito

            for cp in productos_en_carrito: # Se recorren los productos del carrito
                producto = cp.producto # Se obtiene el producto
                producto.stock -= cp.cantidad # Se resta la cantidad del producto al stock
                producto.save() # Se guarda el producto

            productos_en_carrito.delete() # Se eliminan los productos del carrito

            pedido_id = request.session.get('pedido_id') # Se obtiene el id del pedido de la sesión
            pedido = Pedido.objects.get(id=pedido_id) # Se obtiene el pedido

            # Registrar la transacción
            transaccion = Transaccion.objects.create( # Se crea una transacción
                pedido=pedido, 
                token=token, 
                buy_order=response['buy_order'],
                session_id=response['session_id'],
                amount=response['amount'],
                status=response['status'],
                authorization_code=response.get('authorization_code'),
                payment_type_code=response.get('payment_type_code'),
                response_code=response.get('response_code')
            )

            # Enviar correo de confirmación
            enviar_correo_confirmacion(pedido, transaccion)

            # Limpiar la sesión
            request.session.pop('carrito_id', None)
            request.session.pop('pedido_id', None)

            return render(request, 'pago_exitoso.html', {'response': response, 'pedido': pedido}) 
        else:
            return render(request, 'pago_fallido.html', {'response': response})
    except TransbankError as e:
        return render(request, 'pago_fallido.html', {'mensaje': str(e)})

def pago_fallido(request):
    # Limpiar la sesión en caso de pago fallido
    request.session.pop('carrito_id', None) # Eliminar el carrito de la sesión
    request.session.pop('pedido_id', None) # Eliminar el pedido de la sesión
    return render(request, 'pago_fallido.html', {'mensaje': 'Hubo un problema con el pago. Por favor, inténtelo de nuevo.'})

    
def detalle(request, producto_id): # Vista para ver el detalle de un producto
    producto = get_object_or_404(Producto, pk=producto_id) # Se obtiene el producto
    
    if request.method == 'POST': # Si se envió el formulario
        moneda = request.POST.get('moneda') # Se obtiene la moneda seleccionada
    else: # Si no se envió el formulario
        moneda = 'CLP' # Se establece la moneda por defecto en pesos chilenos

    print(f"Moneda seleccionada: {moneda}") # Se imprime la moneda seleccionada
    serie_codigo = SERIES_CODIGOS.get(moneda) # Se obtiene el código de la serie
    tipo_cambio = obtener_tipo_cambio(serie_codigo) # Se obtiene el tipo de cambio

    print(f"Tipo de cambio para {moneda}: {tipo_cambio}") # Se imprime el tipo de cambio

    if tipo_cambio != Decimal('1'): # Si el tipo de cambio es distinto de 1
        precio_convertido = producto.precioOferta / tipo_cambio # Se convierte el precio
    else: # Si el tipo de cambio es 1
        precio_convertido = producto.precioOferta # Se mantiene el precio original

    print(f"Precio convertido: {precio_convertido}") # Se imprime el precio convertido

    context = { # Se crea un diccionario con los datos a enviar al template
        'producto': producto,
        'moneda': moneda,
        'precio_convertido': precio_convertido,
        'tipo_cambio': tipo_cambio
    }
    return render(request, 'detalle-producto.html', context) 