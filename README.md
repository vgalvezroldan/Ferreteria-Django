<h1>Configuración en Archivo .env</h1>

<h2>Edita el Archivo '.env' para Conversión de Monedas</h2>
<p>Agrega tus credenciales de la API al archivo '.env' en la raíz de tu proyecto.</p>
<p>Reemplaza 'tu_correo' y 'tu_contraseña' con tus credenciales reales.</p>
<p>BBCH_API_USER=tu_correo</p>
<p>BCCH_API_PASSWORD=tu_contraseña</p>
<br>


<h2>Configuración Envío de Correos al realizar compra mediante SMTP</h2>
<p>Agrega tus credenciales de correo electrónico al archivo '.env'</p>
<p>DEFAULT_FROM_EMAIL=tu_correo</p>
<p>EMAIL_HOST_USER=tu_correo</p>
<p>EMAIL_HOST_PASSWORD=</p>

<h3>Editar Archivo settings.py</h3>
<p>EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'</p>
<p><b>En este ejemplo se está ocupando Office 365</b></p>
<p>EMAIL_HOST = 'smtp.office365.com' | Cambiar en caso de ocupar otro cliente de correo electrónico</p>
<p>EMAIL_PORT = 587</p>
<p>EMAIL_USE_TLS = True</p>






