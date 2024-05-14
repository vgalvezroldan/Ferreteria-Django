from django import forms
from .models import Pedido

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['tipo_entrega', 'rut', 'nombre', 'apellidos', 'email']
        widgets = {
            'tipo_entrega': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su Rut'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su Nombre'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese sus Apellidos'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su Correo Electrónico'}),
        }
