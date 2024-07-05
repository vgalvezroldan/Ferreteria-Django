from django import forms
from .models import Pedido, PerfilUsuario
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


# Formulario para la creación de un pedido
class PedidoForm(forms.ModelForm): # Se crea un formulario a partir de un modelo
    class Meta: # Se define la clase Meta para indicar el modelo al que pertenece el formulario
        model = Pedido # Se indica el modelo al que pertenece el formulario
        fields = ['tipo_entrega', 'rut', 'nombre', 'apellidos', 'email'] # Se indican los campos del modelo que se mostrarán en el formulario
        widgets = { # Se definen los widgets para los campos del formulario
            'tipo_entrega': forms.RadioSelect(attrs={'class': 'form-check-input'}), # Se define un widget de tipo RadioSelect para el campo tipo_entrega
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su rut...'}), # Se define un widget de tipo TextInput para el campo rut
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su nombre...'}), # Se define un widget de tipo TextInput para el campo nombre
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese sus apellidos...'}), # Se define un widget de tipo TextInput para el campo apellidos
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su correo electrónico...'}), # Se define un widget de tipo EmailInput para el campo email
        }

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}))
    rut = forms.CharField(max_length=12, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'rut', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(RegistroUsuarioForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control', 'placeholder': fieldname.capitalize()})

    def save(self, commit=True):
        user = super(RegistroUsuarioForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            perfil = PerfilUsuario(
                user=user,
                rut=self.cleaned_data['rut'],
                nombre=self.cleaned_data['first_name'],
                apellidos=self.cleaned_data['last_name'],
                email=self.cleaned_data['email']
            )
            perfil.save()
        return user

class LoginUsuarioForm(AuthenticationForm): # Se crea un formulario para el inicio de sesión de usuarios
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})) # Se define un campo de tipo CharField para el nombre de usuario
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})) # Se define un campo de tipo CharField para la contraseña
