from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
import requests
from .models import PerfilUsuario


def enviar_correo_confirmacion(pedido, transaccion):
    perfil = PerfilUsuario.objects.get(user=pedido.user)
    asunto = f'Confirmación de Pedido #{pedido.numero_pedido}'
    mensaje = render_to_string('correo_confirmacion.html', {
        'pedido': pedido,
        'transaccion': transaccion,
        'perfil': perfil
    })
    destinatario = perfil.email
    remitente = settings.DEFAULT_FROM_EMAIL

    email = EmailMessage(asunto, mensaje, remitente, [destinatario])
    email.content_subtype = 'html'
    email.send(fail_silently=False)


SERIES_CODIGOS = {
    'USD': 'F073.TCO.PRE.Z.D',
    'ARS': 'F072.ARS.USD.N.O.D',
    'CLP': None  # El tipo de cambio para CLP es siempre 1
}

def obtener_tipo_cambio(serie_codigo): # Función para obtener el tipo de cambio
    if serie_codigo is None: # Si no se especifica un tipo de cambio, se retorna 1
        return Decimal('1')  # El tipo de cambio para CLP es 1

    usuario = "vgalvezroldan@gmail.com" # Usuario de la API del BCCh
    contrasena = "K1t31.21" # Contraseña de la API del BCCh

    fecha_actual = datetime.now().date() # Fecha actual
    fecha_inicio = (fecha_actual - timedelta(days=30)).strftime("%Y-%m-%d") # Fecha de inicio (30 días antes de la fecha actual)
    fecha_fin = fecha_actual.strftime("%Y-%m-%d") # Fecha de fin (fecha actual)

    url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={usuario}&pass={contrasena}&function=GetSeries&timeseries={serie_codigo}&firstdate={fecha_inicio}&lastdate={fecha_fin}"
    # URL de la API del BCCh para obtener la serie de tipo de cambio
    try: # Intentar obtener el tipo de cambio
        response = requests.get(url) # Realizar la petición GET a la API
        response.raise_for_status() # Verificar si hubo un error en la petición
        datos = response.json() # Convertir la respuesta a JSON

        if datos['Codigo'] != 0: # Si hay un error en la respuesta de la API, se imprime el mensaje de error y se retorna 1
            print(f"Error en la respuesta de la API: {datos['Descripcion']}") # Imprimir mensaje de error
            return Decimal('1') # Retornar 1

        # Procesar la respuesta para obtener el tipo de cambio más reciente
        observaciones = datos['Series']['Obs']  # Obtener las observaciones de la serie
        if not observaciones: # Si no hay observaciones, se imprime un mensaje y se retorna 1
            print("No se encontraron datos para la serie.") 
            return Decimal('1')

        tipo_cambio = None # Inicializar el tipo de cambio en None
        for obs in reversed(observaciones): # Recorrer las observaciones en orden inverso
            valor = Decimal(obs['value']) # Obtener el valor de la observación
            if valor > 0: # Si el valor es positivo, se asigna a la variable tipo_cambio y se rompe el ciclo
                tipo_cambio = valor # Asignar el valor a la variable tipo_cambio
                break # Romper el ciclo

        if tipo_cambio is None: # Si no se encontraron tipos de cambio positivos válidos, se imprime un mensaje y se retorna 1
            print("No se encontraron tipos de cambio positivos válidos") # Imprimir mensaje de error
            return Decimal('1') # Retornar 1

        return tipo_cambio # Retornar el tipo de cambio
    except Exception as e: # Si hay un error en la petición, se imprime un mensaje y se retorna 1
        print(f"Error al obtener el tipo de cambio: {e}") 
        return Decimal('1')