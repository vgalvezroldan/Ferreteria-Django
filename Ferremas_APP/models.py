from django.db import models
from django.contrib.auth.models import User

class Producto(models.Model): # Modelo para los productos
    nombre = models.CharField(max_length=100)  # Campo para el nombre del producto
    descripcion = models.TextField() # Campo para la descripción del producto
    detalleCompleto = models.TextField(default='') # Campo para el detalle completo del producto
    especificaciones = models.CharField(max_length=100, null=True, blank=True) # Campo para las especificaciones del producto
    lista1 = models.CharField(max_length=100, null=True, blank=True) 
    lista2 = models.CharField(max_length=100, null=True, blank=True) 
    lista3 = models.CharField(max_length=100, null=True, blank=True) 
    lista4 = models.CharField(max_length=100, null=True, blank=True)
    lista5 = models.CharField(max_length=100, null=True, blank=True)
    incluye = models.CharField(max_length=100, null=True, blank=True)
    lista6 = models.CharField(max_length=100, null=True, blank=True)
    lista7 = models.CharField(max_length=100, null=True, blank=True)
    lista8 = models.CharField(max_length=100, null=True, blank=True)
    lista9 = models.CharField(max_length=100, null=True, blank=True)
    lista10 = models.CharField(max_length=100, null=True, blank=True)
    precioOferta = models.DecimalField(max_digits=8, decimal_places=2 , null=True, blank=True) # Campo para el precio del producto
    precio = models.DecimalField(max_digits=8, decimal_places=2) # Campo para el precio del producto
    stock = models.IntegerField() # Campo para el stock del producto
    imagen = models.ImageField(upload_to='productos', null=True, blank=True) # Campo para la imagen del producto
    

    def __str__(self):
        return self.nombre
    
class Carrito(models.Model): # Modelo para el carrito de compras
    sesion_id = models.CharField(max_length=100) # Campo para la sesión del carrito

class CarritoProducto(models.Model): # Modelo para los productos del carrito
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE) # Relación con el carrito
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE) # Relación con el producto
    cantidad = models.IntegerField() # Campo para la cantidad de productos

class Pedido(models.Model): # Modelo para los pedidos
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Opcional
    TIPO_ENTREGA_CHOICES = [ # Opciones para el tipo de entrega
        ('RT', 'Retiro en Tienda'), 
        ('DD', 'Despacho a Domicilio')
    ]
     
    tipo_entrega = models.CharField(max_length=2, choices=TIPO_ENTREGA_CHOICES, default='RT') # Campo para el tipo de entrega
    rut = models.CharField(max_length=12) # Campo para el RUT del cliente
    nombre = models.CharField(max_length=100) # Campo para el nombre del cliente
    apellidos = models.CharField(max_length=100) # Campo para los apellidos del cliente
    email = models.EmailField() # Campo para el correo electrónico del cliente
    numero_pedido = models.CharField(max_length=10, unique=True) # Campo para el número de pedido
    datos_completados = models.BooleanField(default=False)  # Nuevo campo para indicar si los datos del cliente han sido completados

    def __str__(self):
        return f'Pedido {self.numero_pedido}'

    def get_nombre_completo(self):
        return f'{self.nombre} {self.apellidos}'

    def get_email(self):
        return self.email
    
class Transaccion(models.Model): # Modelo para las transacciones
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE) # Relación con el pedido
    token = models.CharField(max_length=100) # Campo para el token de la transacción
    buy_order = models.CharField(max_length=100) # Campo para el número de orden de la transacción
    session_id = models.CharField(max_length=100) # Campo para la sesión de la transacción
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Campo para el monto de la transacción
    status = models.CharField(max_length=50) # Campo para el estado de la transacción
    authorization_code = models.CharField(max_length=50, null=True, blank=True) # Campo para el código de autorización
    payment_type_code = models.CharField(max_length=50, null=True, blank=True) # Campo para el código de tipo de pago
    response_code = models.CharField(max_length=50, null=True, blank=True) # Campo para el código de respuesta
    transaction_date = models.DateTimeField(auto_now_add=True) # Campo para la fecha de la transacción

    def __str__(self):
        return f'Transaccion {self.token} - {self.status}'

    def get_cliente_nombre(self):
        return self.pedido.nombre

    def get_cliente_apellidos(self):
        return self.pedido.apellidos

    def get_cliente_email(self):
        return self.pedido.email

    get_cliente_nombre.short_description = 'Nombre'
    get_cliente_apellidos.short_description = 'Apellidos'
    get_cliente_email.short_description = 'Correo Electrónico'

class PerfilUsuario(models.Model): # Modelo para el perfil de usuario
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Relación con el usuario
    rut = models.CharField(max_length=12) # Campo para el RUT del cliente 
    nombre = models.CharField(max_length=100) # Campo para el nombre del cliente
    apellidos = models.CharField(max_length=100) # Campo para los apellidos del cliente
    email = models.EmailField() # Campo para el correo electrónico del cliente

    def __str__(self):
        return f'Perfil de {self.user.username}'