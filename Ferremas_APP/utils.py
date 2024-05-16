from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import bcchapi
from datetime import datetime, timedelta
from decimal import Decimal
import requests


def enviar_correo_confirmacion(pedido, transaccion): # Función para enviar correo de confirmación de pedido
    asunto = f'Confirmación de Pedido #{pedido.numero_pedido}' # Asunto del correo
    mensaje = render_to_string('correo_confirmacion.html', { # Plantilla del correo
        'pedido': pedido, # Datos del pedido
        'transaccion': transaccion, # Datos de la transacción
    })
    destinatario = pedido.email # Destinatario del correo
    remitente = settings.DEFAULT_FROM_EMAIL # Remitente del correo

    email = EmailMessage(asunto, mensaje, remitente, [destinatario]) # Crear el objeto EmailMessage
    email.content_subtype = 'html'  # Definir el contenido del correo como HTML
    email.send(fail_silently=False) # Enviar el correo


SERIES_CODIGOS = {
    'USD': 'F073.TCO.PRE.Z.D',
    'ARS': 'F072.ARS.USD.N.O.D',
    'CLP': None  # El tipo de cambio para CLP es siempre 1
}

def obtener_tipo_cambio(serie_codigo):
    if serie_codigo is None:
        return Decimal('1')  # El tipo de cambio para CLP es 1

    usuario = "vgalvezroldan@gmail.com"
    contrasena = "K1t31.21"

    fecha_actual = datetime.now().date()
    fecha_inicio = (fecha_actual - timedelta(days=30)).strftime("%Y-%m-%d")
    fecha_fin = fecha_actual.strftime("%Y-%m-%d")

    url = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={usuario}&pass={contrasena}&function=GetSeries&timeseries={serie_codigo}&firstdate={fecha_inicio}&lastdate={fecha_fin}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        datos = response.json()

        if datos['Codigo'] != 0:
            print(f"Error en la respuesta de la API: {datos['Descripcion']}")
            return Decimal('1')

        # Procesar la respuesta para obtener el tipo de cambio más reciente
        observaciones = datos['Series']['Obs']
        if not observaciones:
            print("No se encontraron datos para la serie.")
            return Decimal('1')

        tipo_cambio = None
        for obs in reversed(observaciones):
            valor = Decimal(obs['value'])
            if valor > 0:
                tipo_cambio = valor
                break

        if tipo_cambio is None:
            print("No se encontraron tipos de cambio positivos válidos")
            return Decimal('1')

        return tipo_cambio
    except Exception as e:
        print(f"Error al obtener el tipo de cambio: {e}")
        return Decimal('1')