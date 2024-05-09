from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
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