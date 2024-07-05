from django.contrib import admin
from .models import Producto, Transaccion

class TransaccionAdmin(admin.ModelAdmin):   # Clase para mostrar los campos de la transacción en el panel de administración
    list_display = ('token', 'get_cliente_nombre', 'get_cliente_apellidos', 'get_cliente_email', 'amount', 'status', 'transaction_date')    # Mostrar los campos token, nombre, apellidos, email, amount, status y transaction_date
    search_fields = ('token', 'pedido__nombre', 'pedido__apellidos', 'pedido__email') # Buscar por token, nombre, apellidos y email


admin.site.register(Producto)  # Registrar el modelo Producto en el panel de administración
admin.site.register(Transaccion, TransaccionAdmin) # Registrar el modelo Transaccion en el panel de administración