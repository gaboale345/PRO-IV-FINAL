from django.db import models

# Modelos para el ChatBot

class ChatHistory(models.Model):
    user_input = models.TextField(verbose_name="Mensaje del usuario")
    bot_response = models.TextField(verbose_name="Respuesta del asistente")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")

    class Meta:
        verbose_name = "Historial de chat / Consulta IA"
        verbose_name_plural = "Historiales de chat / Consultas IA"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Mensaje ({self.timestamp.strftime('%d/%m/%Y %H:%M')}): {self.user_input[:40]}..."

    @property
    def pregunta(self):
        return self.user_input

    @property
    def respuesta(self):
        return self.bot_response

    @property
    def fecha(self):
        return self.timestamp


# Alias opcional según PDF (Entidad ConsultaIA)
ConsultaIA = ChatHistory


class Producto(models.Model):
    CATEGORIAS = [
        ("Tarjetas Gráficas", "Tarjetas Gráficas (GPU)"),
        ("Procesadores", "Procesadores (CPU)"),
        ("Placas Madre", "Placas Madre (Motherboards)"),
        ("Memorias RAM", "Memorias RAM"),
        ("Almacenamiento", "Almacenamiento (SSD / NVMe / HDD)"),
        ("Fuentes de Poder", "Fuentes de Poder (PSU)"),
        ("Refrigeración", "Sistemas de Refrigeración"),
        ("Gabinetes", "Gabinetes / Chasis"),
        ("Monitores", "Monitores"),
        ("Periféricos", "Periféricos y Accesorios"),
    ]

    # Campos oficiales según Requerimientos del PDF (Sección 5)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código del Producto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.CharField(max_length=100, verbose_name="Categoría")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio ($ USD)")
    cantidad_existente = models.PositiveIntegerField(default=0, verbose_name="Cantidad Existente")
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name="Stock Mínimo")
    estado = models.BooleanField(default=True, verbose_name="Estado del Producto")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    # Campos complementarios para enriquecimiento del catálogo
    marca = models.CharField(max_length=100, blank=True, default="", verbose_name="Marca")
    especificaciones = models.TextField(blank=True, default="", verbose_name="Especificaciones Técnicas")
    destacado = models.BooleanField(default=False, verbose_name="Producto Destacado")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["-precio"]

    def __str__(self):
        estado_txt = "Activo" if self.estado else "Inactivo"
        return f"[{self.codigo}] {self.nombre} - ${self.precio} ({estado_txt})"

    # Compatibilidad hacia atrás con código existente
    @property
    def sku(self):
        return self.codigo

    @sku.setter
    def sku(self, valor):
        self.codigo = valor

    @property
    def stock(self):
        return self.cantidad_existente

    @stock.setter
    def stock(self, valor):
        self.cantidad_existente = valor

    @property
    def fecha_ingreso(self):
        return self.fecha_registro

    @property
    def estado_stock(self):
        if self.cantidad_existente == 0:
            return "Agotado"
        elif self.cantidad_existente <= self.stock_minimo:
            return "Stock Bajo"
        return "En Stock"

    @property
    def badge_class(self):
        if not self.estado:
            return "badge-danger"
        if self.cantidad_existente == 0:
            return "badge-danger"
        elif self.cantidad_existente <= self.stock_minimo:
            return "badge-warning"
        return "badge-success"
