from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_producto'),
    ]

    operations = [
        migrations.RenameField(
            model_name='producto',
            old_name='sku',
            new_name='codigo',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='stock',
            new_name='cantidad_existente',
        ),
        migrations.RenameField(
            model_name='producto',
            old_name='fecha_ingreso',
            new_name='fecha_registro',
        ),
        migrations.AddField(
            model_name='producto',
            name='estado',
            field=models.BooleanField(default=True, verbose_name='Estado del Producto'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='categoria',
            field=models.CharField(max_length=100, verbose_name='Categoría'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='marca',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Marca'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='especificaciones',
            field=models.TextField(blank=True, default='', verbose_name='Especificaciones Técnicas'),
        ),
        migrations.AlterField(
            model_name='producto',
            name='stock_minimo',
            field=models.PositiveIntegerField(default=5, verbose_name='Stock Mínimo'),
        ),
        migrations.AlterModelOptions(
            name='chathistory',
            options={'ordering': ['-timestamp'], 'verbose_name': 'Historial de chat / Consulta IA', 'verbose_name_plural': 'Historiales de chat / Consultas IA'},
        ),
    ]
