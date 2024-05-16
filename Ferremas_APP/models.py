from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    detalleCompleto = models.TextField(default='')
    especificaciones = models.CharField(max_length=100, null=True, blank=True)
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
    precioOferta = models.DecimalField(max_digits=8, decimal_places=2 , null=True, blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.IntegerField()
    imagen = models.ImageField(upload_to='productos', null=True, blank=True)
    

    def __str__(self):
        return self.nombre
    
class Carrito(models.Model):
    sesion_id = models.CharField(max_length=100)

class CarritoProducto(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()

class Pedido(models.Model):
    TIPO_ENTREGA_CHOICES = [
        ('RT', 'Retiro en Tienda'),
        ('DD', 'Despacho a Domicilio')
    ]
    
    tipo_entrega = models.CharField(max_length=2, choices=TIPO_ENTREGA_CHOICES, default='RT')
    rut = models.CharField(max_length=12)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField()
    numero_pedido = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f'Pedido {self.numero_pedido}'

    def get_nombre_completo(self):
        return f'{self.nombre} {self.apellidos}'

    def get_email(self):
        return self.email
    
class Transaccion(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    buy_order = models.CharField(max_length=100)
    session_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    authorization_code = models.CharField(max_length=50, null=True, blank=True)
    payment_type_code = models.CharField(max_length=50, null=True, blank=True)
    response_code = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)

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