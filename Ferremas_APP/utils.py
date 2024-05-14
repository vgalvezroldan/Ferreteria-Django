from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

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
