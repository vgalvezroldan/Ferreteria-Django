from django.shortcuts import get_object_or_404, render, redirect

from Ferremas_APP.templatetags.custom_filters import formato_moneda
from .models import Producto, Carrito, CarritoProducto, Pedido, Transaccion, PerfilUsuario
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
import json
from decimal import Decimal
from django.urls import reverse
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.common.integration_type import IntegrationType
from django.conf import settings
from transbank.error.transbank_error import TransbankError
import random
from .forms import PedidoForm, RegistroUsuarioForm, LoginUsuarioForm
from .utils import enviar_correo_confirmacion, obtener_tipo_cambio, SERIES_CODIGOS
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required




def index(request):
    productos = Producto.objects.all()
    return render(request, 'index.html', {'productos': productos})

@require_POST
def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        csrf_token = request.POST.get('csrfmiddlewaretoken')
        if not csrf_token:
            return JsonResponse({'mensaje': "CSRF token no encontrado."}, status=403)
        
        carrito_id = request.session.get("carrito_id")
        if not carrito_id:
            nuevo_carrito = Carrito.objects.create()
            request.session["carrito_id"] = nuevo_carrito.id
        else:
            nuevo_carrito = Carrito.objects.get(id=carrito_id)
        
        producto = get_object_or_404(Producto, pk=producto_id)
        if producto.stock > 0:
            carrito_producto, created = CarritoProducto.objects.get_or_create(
                carrito=nuevo_carrito,
                producto=producto,
                defaults={'cantidad': 1}
            )
            if not created:
                if carrito_producto.cantidad < producto.stock:
                    carrito_producto.cantidad += 1
                    carrito_producto.save()
            return JsonResponse({'mensaje': "Producto agregado al carrito"})
        else:
            return JsonResponse({'mensaje': "Producto sin stock"}, status=400)

    
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

def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('formulario_datos')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Verificar si el usuario ya tiene datos de cliente guardados
            if Pedido.objects.filter(user=user, datos_completados=True).exists():
                pedido = Pedido.objects.filter(user=user, datos_completados=True).first()
                request.session['pedido_id'] = pedido.id
                return redirect('carrito')
            else:
                return redirect('formulario_datos')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def formulario_datos(request):
    perfil, created = PerfilUsuario.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = PedidoForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            # Guardar el pedido en la sesión si se necesita para la confirmación
            pedido, created = Pedido.objects.get_or_create(user=request.user, defaults={
                'rut': perfil.rut,
                'nombre': perfil.nombre,
                'apellidos': perfil.apellidos,
                'email': perfil.email,
                'numero_pedido': f"{random.randint(1, 999):03d}",
                'datos_completados': True,
            })
            request.session['pedido_id'] = pedido.id
            return redirect('carrito')
    else:
        form = PedidoForm(instance=perfil)
    return render(request, 'formulario_datos.html', {'form': form})

@login_required
def carrito(request):
    carrito_id = request.session.get("carrito_id")
    perfil = PerfilUsuario.objects.get(user=request.user)

    if carrito_id:
        carrito = Carrito.objects.get(id=carrito_id)
        productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito)
        productos = [
            {
                'id': cp.producto.id,
                'nombre': cp.producto.nombre,
                'descripcion': cp.producto.descripcion,
                'detalleCompleto': cp.producto.detalleCompleto,
                'precio': cp.producto.precioOferta,
                'cantidad': cp.cantidad,
                'imagen': cp.producto.imagen.url if cp.producto.imagen else '',
                'total': cp.cantidad * cp.producto.precioOferta,
            }
            for cp in productos_en_carrito
        ]
        total = sum(cp['total'] for cp in productos)
        iva = total * Decimal('0.19')
        total_con_iva = total + iva

        contexto = {
            'productos': productos,
            'total': total,
            'iva': iva,
            'total_con_iva': total_con_iva,
            'perfil': perfil  # Incluir perfil en el contexto
        }
        return render(request, 'carrito.html', contexto)
    else:
        return render(request, 'carrito.html', {'productos': [], 'perfil': perfil})

    
def agregar_al_carrito(request, producto_id):
    carrito_id = request.session.get("carrito_id")
    if not carrito_id:
        nuevo_carrito = Carrito.objects.create()
        request.session["carrito_id"] = nuevo_carrito.id
    else:
        nuevo_carrito = Carrito.objects.get(id=carrito_id)
    
    producto = get_object_or_404(Producto, pk=producto_id)
    if producto.stock > 0:
        carrito_producto, created = CarritoProducto.objects.get_or_create(
            carrito=nuevo_carrito,
            producto=producto,
            defaults={'cantidad': 1}
        )
        if not created:
            if carrito_producto.cantidad < producto.stock:
                carrito_producto.cantidad += 1
                carrito_producto.save()
        return JsonResponse({'mensaje': "Producto agregado al carrito"})
    else:
        return JsonResponse({'mensaje': "Producto sin stock"}, status=400)

def ver_carrito(request):
    carrito_id = request.session.get("carrito_id")
    if carrito_id:
        carrito = Carrito.objects.get(id=carrito_id)
        productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito)
        productos = [
            {'id': cp.producto.id, 'nombre': cp.producto.nombre, 'cantidad': cp.cantidad, 'precio': cp.producto.precioOferta}
            for cp in productos_en_carrito
        ]
        total = sum(cp.cantidad * cp.producto.precioOferta for cp in productos_en_carrito)
        return JsonResponse({'productos': productos, 'total': float(total)})
    else:
        return JsonResponse({'productos': [], 'total': 0.0})

@require_POST
def actualizar_carrito(request, producto_id):
    try:
        data = json.loads(request.body)
        cantidad = int(data.get('cantidad', 0))
        carrito_id = request.session.get("carrito_id")

        if carrito_id:
            carrito_producto = get_object_or_404(CarritoProducto, carrito_id=carrito_id, producto_id=producto_id)
            if cantidad > 0 and cantidad <= carrito_producto.producto.stock:
                carrito_producto.cantidad = cantidad
                carrito_producto.save()
            elif cantidad == 0:
                carrito_producto.delete()
            productos_en_carrito = CarritoProducto.objects.filter(carrito_id=carrito_id)
            total_carrito = sum(item.cantidad * item.producto.precioOferta for item in productos_en_carrito)
            return JsonResponse({'mensaje': 'Cantidad actualizada correctamente', 'totalCarrito': float(total_carrito)})
        return JsonResponse({'mensaje': 'Error al actualizar el carrito'}, status=400)
    except Exception as e:
        return JsonResponse({'mensaje': str(e)}, status=500)

@require_POST
def eliminar_del_carrito(request, producto_id):
    carrito_id = request.session.get("carrito_id")
    if not carrito_id:
        return JsonResponse({'mensaje': "No existe el carrito"}, status=404)

    try:
        carrito_producto = CarritoProducto.objects.get(carrito_id=carrito_id, producto_id=producto_id)
        carrito_producto.delete()
        return JsonResponse({'mensaje': 'Producto eliminado del carrito'})
    except CarritoProducto.DoesNotExist:
        return JsonResponse({'mensaje': 'Producto no encontrado en el carrito'}, status=404)

def iniciar_pago(request):
    if request.method == "POST":
        total_con_iva = request.POST.get("total_con_iva")
        total_con_iva = total_con_iva.replace('.', '').replace(',', '.')  # Eliminar separadores de miles y ajustar el separador decimal
        total_con_iva = int(float(total_con_iva))  # Convertir a entero

        carrito_id = request.session.get("carrito_id")
        
        if carrito_id and total_con_iva:
            carrito = Carrito.objects.get(id=carrito_id)
            tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, settings.WEBPAY_PLUS_INTEGRATION_TYPE))

            try:
                response = tx.create(
                    buy_order=str(carrito.id),
                    session_id=request.session.session_key,
                    amount=total_con_iva,
                    return_url=request.build_absolute_uri(reverse('webpay_confirmacion'))
                )
                return redirect(response['url'] + '?token_ws=' + response['token'])
            except TransbankError as e:
                return render(request, 'pago_fallido.html', {'mensaje': str(e)})
        else:
            return redirect('carrito')
        
def webpay_confirmacion(request):
    token = request.GET.get('token_ws')

    if not token:
        return render(request, 'pago_fallido.html', {'mensaje': 'Token no recibido'})

    try:
        tx = Transaction(WebpayOptions(settings.WEBPAY_PLUS_COMMERCE_CODE, settings.WEBPAY_PLUS_API_KEY, settings.WEBPAY_PLUS_INTEGRATION_TYPE))
        response = tx.commit(token=token)

        if response['status'] == 'AUTHORIZED':
            carrito_id = response['buy_order']
            carrito = Carrito.objects.get(id=carrito_id)
            productos_en_carrito = CarritoProducto.objects.filter(carrito=carrito)

            for cp in productos_en_carrito:
                producto = cp.producto
                producto.stock -= cp.cantidad
                producto.save()

            productos_en_carrito.delete()

            pedido_id = request.session.get('pedido_id')
            if not pedido_id:
                return render(request, 'pago_fallido.html', {'mensaje': 'Pedido no encontrado en la sesión'})

            try:
                pedido = Pedido.objects.get(id=pedido_id)
            except Pedido.DoesNotExist:
                return render(request, 'pago_fallido.html', {'mensaje': 'Pedido no encontrado'})

            transaccion = Transaccion.objects.create(
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

            enviar_correo_confirmacion(pedido, transaccion)

            request.session.pop('carrito_id', None)
            return render(request, 'pago_exitoso.html', {'response': response, 'pedido': pedido})
        else:
            return render(request, 'pago_fallido.html', {'response': response})
    except TransbankError as e:
        return render(request, 'pago_fallido.html', {'mensaje': str(e)})


def pago_fallido(request):
    request.session.pop('carrito_id', None)
    request.session.pop('pedido_id', None)
    return render(request, 'pago_fallido.html', {'mensaje': 'Hubo un problema con el pago. Por favor, inténtelo de nuevo.'})

def detalle(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        moneda = data.get('moneda', 'CLP')
    else:
        moneda = 'CLP'
        
    serie_codigo = SERIES_CODIGOS.get(moneda)
    tipo_cambio = obtener_tipo_cambio(serie_codigo)

    if tipo_cambio != Decimal('1'):
        precio_convertido = producto.precioOferta / tipo_cambio
    else:
        precio_convertido = producto.precioOferta

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'precio_convertido': formato_moneda(precio_convertido, moneda),
            'tipo_cambio': formato_moneda(tipo_cambio, 'CLP') if tipo_cambio != Decimal('1') else None,
            'moneda': moneda
        }
        return JsonResponse(data)
    
    context = {
        'producto': producto,
        'moneda': moneda,
        'precio_convertido': precio_convertido,
        'tipo_cambio': tipo_cambio
    }

    return render(request, 'detalle-producto.html', context)