from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal
import requests
from .models import PerfilUsuario
import threading

def enviar_correo_confirmacion(pedido, transaccion):
    def enviar_correo():
        try:
            perfil = PerfilUsuario.objects.get(user=pedido.user)
            if not perfil.email:
                raise ValueError("El perfil del usuario no tiene un correo electrónico válido.")

            asunto = f'Confirmación de Pedido #{pedido.numero_pedido}'
            mensaje = render_to_string('pages/cart/correo_confirmacion.html', {
                'pedido': pedido,
                'transaccion': transaccion,
                'perfil': perfil
            })
            destinatario = perfil.email
            remitente = settings.DEFAULT_FROM_EMAIL

            email = EmailMessage(asunto, mensaje, remitente, [destinatario])
            email.content_subtype = 'html'
            email.send(fail_silently=False)
        except Exception as e:
            print(f"Error al enviar el correo de confirmación: {e}")

    threading.Thread(target=enviar_correo).start()


SERIES_CODIGOS = { # Diccionario con los códigos de las series de tipo de cambio
    'USD': 'F073.TCO.PRE.Z.D', # Código de la serie de tipo de cambio de USD a CLP
    'ARS': 'F072.ARS.USD.N.O.D', # Código de la serie de tipo de cambio de ARS a USD
    'CLP': None  # El tipo de cambio para CLP es siempre 1
}

def obtener_tipo_cambio(serie_codigo):
    if serie_codigo is None:
        return Decimal('1')  # El tipo de cambio para CLP es 1

    usuario = settings.BCCH_API_USER  # Usuario de la API del BCCh
    contrasena = settings.BCCH_API_PASSWORD  # Contraseña de la API del BCCh

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