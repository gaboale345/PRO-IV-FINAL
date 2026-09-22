from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    """Formulario para registro y actualización de productos con validaciones estrictas (RF-01 y RF-03)."""

    class Meta:
        model = Producto
        fields = [
            'codigo',
            'nombre',
            'descripcion',
            'categoria',
            'precio',
            'cantidad_existente',
            'stock_minimo',
            'estado',
            'marca',
            'especificaciones',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej. P001 o COMP-01'}),
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre completo del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Descripción detallada...'}),
            'categoria': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Categoría (ej. Computadoras, Periféricos, Componentes)'}),
            'precio': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0'}),
            'cantidad_existente': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'marca': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Marca del fabricante (opcional)'}),
            'especificaciones': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Detalles técnicos (opcional)'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo', '').strip()
        if not codigo:
            raise forms.ValidationError("El código del producto es obligatorio.")
        
        # Validar que no se duplique con otro producto
        qs = Producto.objects.filter(codigo__iexact=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(f"El código '{codigo}' ya está registrado con otro producto.")
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise forms.ValidationError("El nombre del producto es obligatorio.")
        return nombre

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria', '').strip()
        if not categoria:
            raise forms.ValidationError("La categoría del producto es obligatoria.")
        return categoria

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is None:
            raise forms.ValidationError("El precio es obligatorio.")
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean_cantidad_existente(self):
        cantidad = self.cleaned_data.get('cantidad_existente')
        if cantidad is None:
            raise forms.ValidationError("La cantidad existente es obligatoria.")
        if cantidad < 0:
            raise forms.ValidationError("La cantidad existente no puede ser negativa.")
        return cantidad

    def clean_stock_minimo(self):
        minimo = self.cleaned_data.get('stock_minimo')
        if minimo is None:
            minimo = 0
        if minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return minimo


class AjusteStockForm(forms.Form):
    """Formulario para aumentar o disminuir existencias con control de no negatividad (RF-05)."""

    ACCION_CHOICES = [
        ('aumentar', 'Aumentar existencia (+)'),
        ('disminuir', 'Disminuir existencia (-)'),
    ]
    accion = forms.ChoiceField(choices=ACCION_CHOICES)
    cantidad = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, producto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.producto = producto

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        cantidad = cleaned_data.get('cantidad') or 0

        if self.producto and accion == 'disminuir':
            if self.producto.cantidad_existente - cantidad < 0:
                raise forms.ValidationError(
                    f"No es posible disminuir {cantidad} unidad(es). La existencia actual es de {self.producto.cantidad_existente}. La cantidad disponible no puede ser negativa."
                )
        return cleaned_data
