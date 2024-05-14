from django.contrib import admin
from .models import Producto, Transaccion

class TransaccionAdmin(admin.ModelAdmin):
    list_display = ('token', 'get_cliente_nombre', 'get_cliente_apellidos', 'get_cliente_email', 'amount', 'status', 'transaction_date')   
    search_fields = ('token', 'pedido__nombre', 'pedido__apellidos', 'pedido__email') # Buscar por token, nombre, apellidos y email


admin.site.register(Producto)
admin.site.register(Transaccion, TransaccionAdmin)