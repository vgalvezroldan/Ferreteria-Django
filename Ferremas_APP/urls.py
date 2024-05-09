from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', views.index, name='index'),
    path('agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('construccion/', views.construccion, name='construccion'),
    path('herramientas/', views.herramientas, name='herramientas'),
    path('hogar/', views.hogar, name='hogar'),
    path('piso_y_pared/', views.piso_y_pared, name='piso_y_pared'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)