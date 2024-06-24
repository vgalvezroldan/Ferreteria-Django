from django import forms
from .models import Pedido, PerfilUsuario
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['tipo_entrega', 'rut', 'nombre', 'apellidos', 'email']
        widgets = {
            'tipo_entrega': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su rut...'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su nombre...'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese sus apellidos...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese su correo electrónico...'}),
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

class LoginUsuarioForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))
