# Generated by Django 5.0.5 on 2024-05-10 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ferremas_APP', '0003_producto_preciooferta'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='descripcionLarga',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='producto',
            name='detalleCompleto',
            field=models.TextField(default=''),
        ),
    ]