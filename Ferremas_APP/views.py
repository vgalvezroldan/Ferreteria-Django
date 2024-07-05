from django.shortcuts import get_object_or_404, render, redirect
from Ferremas_APP.templatetags.custom_filters import formato_moneda
from .models import Producto, Carrito, CarritoProducto, Pedido, Transaccion, PerfilUsuario
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from decimal import Decimal
from django.urls import reverse
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from django.conf import settings
from transbank.error.transbank_error import TransbankError
import random
from .forms import PedidoForm, RegistroUsuarioForm
from .utils import enviar_correo_confirmacion, obtener_tipo_cambio, SERIES_CODIGOS
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
import logging

logger = logging.getLogger(__name__)


def index(request): # Vista para la página de inicio
    productos = Producto.objects.all() # Se obtienen todos los productos
    return render(request, 'pages/home/index.html', {'productos': productos}) # Se renderiza la plantilla con los productos

@require_POST # Solo se aceptan peticiones POST
def agregar_al_carrito(request, producto_id): # Vista para agregar un producto al carrito
    if request.method == 'POST': # Si la petición es POST
        csrf_token = request.POST.get('csrfmiddlewaretoken') # Se obtiene el token CSRF
        if not csrf_token: # Si no se encuentra el token CSRF
            return JsonResponse({'mensaje': "CSRF token no encontrado."}, status=403) # Se responde con un mensaje de error
        
        carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
        if not carrito_id: # Si no existe un carrito en la sesión
            nuevo_carrito = Carrito.objects.create() # Se crea un nuevo carrito
            request.session["carrito_id"] = nuevo_carrito.id # Se guarda el id del carrito en la sesión
        else: # Si existe un carrito en la sesión
            nuevo_carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
        
        producto = get_object_or_404(Producto, pk=producto_id) # Se obtiene el producto
        if producto.stock > 0: # Si el producto tiene stock
            carrito_producto, created = CarritoProducto.objects.get_or_create( # Se obtiene o crea un CarritoProducto
                carrito=nuevo_carrito, # Se asigna el carrito
                producto=producto, # Se asigna el producto
                defaults={'cantidad': 1} # Se asigna la cantidad inicial
            )
            if not created: # Si el CarritoProducto ya existe
                if carrito_producto.cantidad < producto.stock: # Si la cantidad es menor al stock
                    carrito_producto.cantidad += 1 # Se aumenta la cantidad
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
    return render(request, 'pages/home/construccion.html')

def herramientas(request):
    return render(request, 'pages/home/herramientas.html')

def hogar(request):
    return render(request, 'pages/home/hogar.html')

def piso_y_pared(request):
    return render(request, 'pages/home/piso-y-pared.html')

def registro(request): # Vista para el registro de usuarios
    if request.method == 'POST':   # Si la petición es POST
        form = RegistroUsuarioForm(request.POST) # Se crea un formulario de registro con los datos de la petición
        if form.is_valid(): # Si el formulario es válido
            try:   # Se intenta guardar el usuario
                with transaction.atomic(): # Se inicia una transacción
                    user = form.save() # Se guarda el usuario
                    login(request, user) # Se inicia sesión con el usuario
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Si la petición es una petición AJAX
                        return JsonResponse({'success': True}) # Se responde con un mensaje de éxito
                    else: # Si la petición no es una petición AJAX
                        return redirect('formulario_datos') # Se redirige al formulario de datos
            except IntegrityError as e: # Si ocurre un error de integridad
                form.add_error(None, 'Error al guardar el usuario. Por favor, intente de nuevo.') # Se agrega un error al formulario
                if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Si la petición es una petición AJAX
                    errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()} # Se obtienen los errores del formulario
                    return JsonResponse({'success': False, 'errors': errors}) # Se responde con un mensaje de error
                else:
                    return render(request, 'pages/registration/registro.html', {'form': form, 'errors': form.errors}) # Se renderiza la plantilla con el formulario y los errores
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Si la petición es una petición AJAX
                errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()} # Se obtienen los errores del formulario
                return JsonResponse({'success': False, 'errors': errors}) # Se responde con un mensaje de error
            else:
                return render(request, 'pages/registration/registro.html', {'form': form, 'errors': form.errors}) 
    else:
        form = RegistroUsuarioForm() # Se crea un formulario de registro
    return render(request, 'pages/registration/registro.html', {'form': form}) # Se renderiza la plantilla con el formulario

def login_view(request): # Vista para el inicio de sesión
    if request.method == 'POST':    # Si la petición es POST
        form = AuthenticationForm(data=request.POST)   # Se crea un formulario de autenticación con los datos de la petición
        if form.is_valid(): # Si el formulario es válido
            user = form.get_user() # Se obtiene el usuario
            login(request, user) # Se inicia sesión con el usuario
            # Verificar si el usuario ya tiene datos de cliente guardados
            if Pedido.objects.filter(user=user, datos_completados=True).exists(): 
                pedido = Pedido.objects.filter(user=user, datos_completados=True).first() # Se obtiene el primer pedido con datos completados
                request.session['pedido_id'] = pedido.id # Se guarda el id del pedido en la sesión
                return redirect('carrito') # Se redirige al carrito
            else: # Si el usuario no tiene datos de cliente guardados
                return redirect('formulario_datos') # Se redirige al formulario de datos
    else: # Si la petición no es POST
        form = AuthenticationForm() # Se crea un formulario de autenticación
    return render(request, 'pages/registration/login.html', {'form': form}) # Se renderiza la plantilla con el formulario

def logout_view(request): # Vista para cerrar sesión
    logout(request) # Se cierra la sesión
    return redirect('index') # Se redirige a la página de inicio

@login_required
def formulario_datos(request):  # Vista para el formulario de datos de cliente
    perfil, created = PerfilUsuario.objects.get_or_create(user=request.user) # Se obtiene o crea el perfil de usuario
    if request.method == 'POST': # Si la petición es POST
        form = PedidoForm(request.POST, instance=perfil) # Se crea un formulario de pedido con los datos de la petición
        if form.is_valid():  # Si el formulario es válido
            form.save() # Se guardan los datos del formulario
            pedido, created = Pedido.objects.get_or_create(user=request.user, defaults={ # Se obtiene o crea un pedido
                'rut': perfil.rut, # Se asigna el RUT del perfil
                'nombre': perfil.nombre, # Se asigna el nombre del perfil
                'apellidos': perfil.apellidos, # Se asignan los apellidos del perfil
                'email': perfil.email, # Se asigna el email del perfil
                'numero_pedido': f"{random.randint(1, 999):03d}", # Se asigna un número de pedido aleatorio
                'datos_completados': True, # Se asigna que los datos están completados
            })
            request.session['pedido_id'] = pedido.id  # Guarda el pedido_id en la sesión
            return redirect('carrito') # Se redirige al carrito
    else:
        form = PedidoForm(instance=perfil) # Se crea un formulario de pedido con el perfil de usuario
    return render(request, 'pages/cart/formulario_datos.html', {'form': form}) # Se renderiza la plantilla con el formulario

@login_required
def carrito(request): # Vista para el carrito de compras
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    perfil = PerfilUsuario.objects.get(user=request.user) # Se obtiene el perfil de usuario
    if carrito_id: # Si existe un carrito en la sesión
        carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
        productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito) # Se obtienen los productos del carrito
        productos = [ # Se crea una lista con los productos del carrito
            {
                'id': cp.producto.id, # Se asigna el id del producto
                'nombre': cp.producto.nombre, # Se asigna el nombre del producto
                'descripcion': cp.producto.descripcion, # Se asigna la descripción del producto
                'detalleCompleto': cp.producto.detalleCompleto, # Se asigna el detalle completo del producto
                'precio': cp.producto.precioOferta, # Se asigna el precio del producto
                'cantidad': cp.cantidad, # Se asigna la cantidad del producto
                'imagen': cp.producto.imagen.url if cp.producto.imagen else '', # Se asigna la URL de la imagen del producto
                'total': cp.cantidad * cp.producto.precioOferta, # Se asigna el total del producto
            }
            for cp in productos_en_carrito # Se recorren los productos del carrito
        ]
        total = sum(cp['total'] for cp in productos) if productos else Decimal('0.00') # Se calcula el total del carrito
        iva = total * Decimal('0.19') # Se calcula el IVA
        total_con_iva = total + iva # Se calcula el total con IVA

        contexto = { # Se crea el contexto
            'productos': productos, # Se asignan los productos
            'total': total, # Se asigna el total
            'iva': iva, # Se asigna el IVA
            'total_con_iva': total_con_iva, # Se asigna el total con IVA
            'perfil': perfil  # Incluir perfil en el contexto
        }
        return render(request, 'pages/cart/carrito.html', contexto)    # Se renderiza la plantilla con el contexto
    else:
        contexto = {
            'productos': [],
            'total': Decimal('0.00'),
            'iva': Decimal('0.00'),
            'total_con_iva': Decimal('0.00'),
            'perfil': perfil,
        }
        return render(request, 'pages/cart/carrito.html', contexto) # Se renderiza la plantilla con una lista vacía de productos

    
def agregar_al_carrito(request, producto_id): # Vista para agregar un producto al carrito
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    if not carrito_id: # Si no existe un carrito en la sesión
        nuevo_carrito = Carrito.objects.create() # Se crea un nuevo carrito
        request.session["carrito_id"] = nuevo_carrito.id # Se guarda el id del carrito en la sesión
    else: # Si existe un carrito en la sesión
        nuevo_carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
    
    producto = get_object_or_404(Producto, pk=producto_id) # Se obtiene el producto
    if producto.stock > 0: # Si el producto tiene stock
        carrito_producto, created = CarritoProducto.objects.get_or_create( # Se obtiene o crea un CarritoProducto
            carrito=nuevo_carrito, # Se asigna el carrito
            producto=producto,  # Se asigna el producto
            defaults={'cantidad': 1} # Se asigna la cantidad inicial
        )
        if not created: # Si el CarritoProducto ya existe
            if carrito_producto.cantidad < producto.stock: # Si la cantidad es menor al stock
                carrito_producto.cantidad += 1 # Se aumenta la cantidad
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

@require_POST
def actualizar_carrito(request, producto_id): # Vista para actualizar la cantidad de un producto en el carrito
    try: # Se intenta realizar la operación
        data = json.loads(request.body) # Se obtiene la información del cuerpo de la petición
        cantidad = int(data.get('cantidad', 0)) # Se obtiene la cantidad del producto
        carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión

        if carrito_id:  # Si existe un carrito en la sesión
            carrito_producto = get_object_or_404(CarritoProducto, carrito_id=carrito_id, producto_id=producto_id) # Se obtiene el CarritoProducto
            if cantidad > 0 and cantidad <= carrito_producto.producto.stock: # Si la cantidad es mayor a 0 y menor o igual al stock
                carrito_producto.cantidad = cantidad # Se actualiza la cantidad
                carrito_producto.save() # Se guarda el CarritoProducto
            elif cantidad == 0: # Si la cantidad es 0
                carrito_producto.delete() # Se elimina el CarritoProducto
            productos_en_carrito = CarritoProducto.objects.filter(carrito_id=carrito_id) # Se obtienen los productos del carrito
            total_carrito = sum(item.cantidad * item.producto.precioOferta for item in productos_en_carrito) # Se calcula el total del carrito
            return JsonResponse({'mensaje': 'Cantidad actualizada correctamente', 'totalCarrito': float(total_carrito)}) # Se responde con un mensaje y el total del carrito
        return JsonResponse({'mensaje': 'Error al actualizar el carrito'}, status=400) # Si no existe un carrito en la sesión, se responde con un mensaje de error
    except Exception as e: # Si ocurre un error
        return JsonResponse({'mensaje': str(e)}, status=500) # Se responde con un mensaje de error

@require_POST
def eliminar_del_carrito(request, producto_id): # Vista para eliminar un producto del carrito
    carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
    if not carrito_id: # Si no existe un carrito en la sesión
        return JsonResponse({'mensaje': "No existe el carrito"}, status=404) # Se responde con un mensaje de error

    try:    # Se intenta realizar la operación
        carrito_producto = CarritoProducto.objects.get(carrito_id=carrito_id, producto_id=producto_id) # Se obtiene el CarritoProducto
        carrito_producto.delete() # Se elimina el CarritoProducto
        return JsonResponse({'mensaje': 'Producto eliminado del carrito'}) # Se responde con un mensaje
    except CarritoProducto.DoesNotExist: # Si el CarritoProducto no existe
        return JsonResponse({'mensaje': 'Producto no encontrado en el carrito'}, status=404) # Se responde con un mensaje de error

def iniciar_pago(request): 
    if request.method == "POST": # Si la petición es POST
        total_con_iva = request.POST.get("total_con_iva") # Se obtiene el total con IVA
        total_con_iva = total_con_iva.replace('.', '').replace(',', '.')  # Eliminar separadores de miles y ajustar el separador decimal
        total_con_iva = int(float(total_con_iva))  # Convertir a entero

        carrito_id = request.session.get("carrito_id") # Se obtiene el id del carrito de la sesión
 
        if carrito_id and total_con_iva: # Si existe un carrito en la sesión y el total con IVA
            carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
            tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, settings.WEBPAY_PLUS_INTEGRATION_TYPE)) # Se crea una transacción

            try:
                response = tx.create( # Se crea la transacción
                    buy_order=str(carrito.id), # Se asigna el id del carrito como buy_order
                    session_id=request.session.session_key, # Se asigna el id de la sesión
                    amount=total_con_iva, # Se asigna el total con IVA
                    return_url=request.build_absolute_uri(reverse('webpay_confirmacion')) # Se asigna la URL de retorno
                )
                logger.info(f"Webpay create response: {response}") # Se registra la respuesta en el log
                return redirect(response['url'] + '?token_ws=' + response['token']) # Se redirige a la URL de Webpay con el token
            except TransbankError as e: # Si ocurre un error de Transbank
                logger.error(f"TransbankError in iniciar_pago: {str(e)}") # Se registra el error en el log
                return render(request, 'pages/cart/pago_fallido.html', {'mensaje': str(e)}) # Se renderiza la plantilla de pago fallido con el mensaje de error
        else:
            return redirect('carrito')  # Si no existe un carrito en la sesión o el total con IVA, se redirige al carrito
        
def webpay_confirmacion(request):  # Vista para
    token = request.GET.get('token_ws') # Se obtiene el token de la URL

    if not token: # Si no se recibe el token
        return render(request, 'pages/cart/pago_fallido.html', {'mensaje': 'Token no recibido'}) # Se renderiza la plantilla de pago fallido con un mensaje de error

    try:
        tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, settings.WEBPAY_PLUS_INTEGRATION_TYPE)) # Se crea una transacción
        response = tx.commit(token=token)   

        if response['status'] == 'AUTHORIZED':   # Si el estado de la transacción es 'AUTHORIZED'
            carrito_id = response['buy_order'] # Se obtiene el id del carrito
            carrito = Carrito.objects.get(id=carrito_id) # Se obtiene el carrito
            productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito) # Se obtienen los productos del carrito

            for cp in productos_en_carrito: # Se recorren los productos del carrito
                producto = cp.producto  # Se obtiene el producto
                producto.stock -= cp.cantidad # Se resta la cantidad del producto al stock
                producto.save() # Se guarda el producto

            productos_en_carrito.delete() # Se eliminan los productos del carrito

            pedido_id = request.session.get('pedido_id') # Se obtiene el id del pedido de la sesión
            if not pedido_id: # Si no existe un pedido en la sesión
                return render(request, 'pages/cart/pago_fallido.html', {'mensaje': 'Pedido no encontrado en la sesión'}) # Se renderiza la plantilla de pago fallido con un mensaje de error

            try:
                pedido = Pedido.objects.get(id=pedido_id) # Se obtiene el pedido
            except Pedido.DoesNotExist: # Si el pedido no existe
                return render(request, 'pages/cart/pago_fallido.html', {'mensaje': 'Pedido no encontrado'}) # Se renderiza la plantilla de pago fallido con un mensaje de error
 
            transaccion = Transaccion.objects.create( # Se crea una transacción
                pedido=pedido, # Se asigna el pedido
                token=token, # Se asigna el token
                buy_order=response['buy_order'], # Se asigna el buy_order
                session_id=response['session_id'], # Se asigna el session_id
                amount=response['amount'], # Se asigna el amount
                status=response['status'], # Se asigna el status
                authorization_code=response.get('authorization_code'), # Se asigna el authorization_code
                payment_type_code=response.get('payment_type_code'), # Se asigna el payment_type_code
                response_code=response.get('response_code') # Se asigna el response_code
            )

            enviar_correo_confirmacion(pedido, transaccion)  # Enviar el correo de manera asincrónica

            request.session.pop('carrito_id', None)
            request.session.pop('pedido_id', None)  # Eliminar el pedido_id de la sesión
            return render(request, 'pages/cart/pago_exitoso.html', {'response': response, 'pedido': pedido}) # Se renderiza la plantilla de pago exitoso con la respuesta y el pedido
        else:
            return render(request, 'pages/cart/pago_fallido.html', {'response': response}) # Se renderiza la plantilla de pago fallido con la respuesta
    except TransbankError as e:
        return render(request, 'pages/cart/pago_fallido.html', {'mensaje': str(e)}) # Se renderiza la plantilla de pago fallido con el mensaje de error
 
def pago_fallido(request): # Vista para el pago fallido
    request.session.pop('carrito_id', None) # Se elimina el id del carrito de la sesión
    request.session.pop('pedido_id', None) # Se elimina el id del pedido de la sesión
    return render(request, 'pages(cart/pago_fallido.html', {'mensaje': 'Hubo un problema con el pago. Por favor, inténtelo de nuevo.'}) # Se renderiza la plantilla con un mensaje de error

def detalle(request, producto_id): # Vista para el detalle de un producto
    producto = get_object_or_404(Producto, pk=producto_id) # Se obtiene el producto

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest': # Si la petición es POST y es una petición AJAX
        data = json.loads(request.body) # Se obtiene la información del cuerpo de la petición
        moneda = data.get('moneda', 'CLP') # Se obtiene la moneda
    else: # Si la petición no es POST o no es una petición AJAX
        moneda = 'CLP' # Se asigna la moneda por defecto
        
    serie_codigo = SERIES_CODIGOS.get(moneda) # Se obtiene el código de la serie de tipo de cambio
    tipo_cambio = obtener_tipo_cambio(serie_codigo) # Se obtiene el tipo de cambio

    if tipo_cambio != Decimal('1'): # Si el tipo de cambio no es 1
        precio_convertido = producto.precioOferta / tipo_cambio # Se convierte el precio a la moneda seleccionada
    else: # Si el tipo de cambio es 1
        precio_convertido = producto.precioOferta # Se asigna el precio original

    if request.headers.get('x-requested-with') == 'XMLHttpRequest': # Si la petición es una petición AJAX
        data = { # Se crea un diccionario con los datos
            'precio_convertido': formato_moneda(precio_convertido, moneda), # Se formatea el precio convertido
            'tipo_cambio': formato_moneda(tipo_cambio, 'CLP') if tipo_cambio != Decimal('1') else None, # Se formatea el tipo de cambio
            'moneda': moneda # Se asigna la moneda
        }
        return JsonResponse(data) # Se responde con los datos
    
    context = { # Se crea el contexto
        'producto': producto, # Se asigna el producto
        'moneda': moneda, # Se asigna la moneda
        'precio_convertido': precio_convertido,     # Se asigna el precio convertido
        'tipo_cambio': tipo_cambio  # Se asigna el tipo de cambio
    }

    return render(request, 'pages/home/detalle-producto.html', context) # Se renderiza la plantilla con el contexto