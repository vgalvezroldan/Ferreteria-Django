from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),
    path('construccion/', views.construccion, name='construccion'),
    path('herramientas/', views.herramientas, name='herramientas'),
    path('hogar/', views.hogar, name='hogar'),
    path('piso_y_pared/', views.piso_y_pared, name='piso_y_pared'),
    path('detalle/<int:producto_id>/', views.detalle, name='detalle'), 
    path('agregar_al_carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'), 
    path('eliminar_del_carrito/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'), 
    path('ver_carrito/', views.ver_carrito, name='ver_carrito'),
    path('actualizar_carrito/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/', views.carrito, name='carrito'), 
    path('iniciar_pago/', views.iniciar_pago, name='iniciar_pago'),
    path('webpay_confirmacion/', views.webpay_confirmacion, name='webpay_confirmacion'),
    path('formulario_datos/', views.formulario_datos, name='formulario_datos'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
