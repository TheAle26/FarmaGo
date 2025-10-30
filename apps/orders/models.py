from django.db import models
from django.conf import settings 
from apps.accounts.models import Farmacia,Repartidor,Cliente



class Medicamento(models.Model):
    # Campos obligatorios para identificación
    nombre_comercial = models.CharField(
        max_length=150, 
        unique=True, 
        help_text="Nombre con el que se vende el medicamento (Ej: Ibuprofeno 600)"
    )
    
    principio_activo = models.CharField(
        max_length=150, 
        help_text="Sustancia química principal (Ej: Ibuprofeno, Paracetamol)"
    )
    
    
    # Detalle de la dosis/contenido
    concentracion = models.CharField(
        max_length=50, 
        help_text="Concentración o cantidad (Ej: 600mg, 200ml, 10%)"
    )
    
    # Clasificación (Ej: Analgésico, Antibiótico, Venta Libre)
    categoria = models.CharField(max_length=100, blank=True)
    
    # Regulación de venta
    requiere_receta = models.BooleanField(
        default=False, 
        help_text="Indica si se necesita receta médica para su venta."
    )
    
    # Código estándar (Ej: SKU o código de barra)
    codigo_barra = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True
    )

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"
        # Asegura que no haya duplicados con la misma concentración
        unique_together = ('nombre_comercial', 'concentracion') 

    def __str__(self):
        return f"{self.nombre_comercial} ({self.concentracion})"
    


class StockMedicamento(models.Model):
    farmacia = models.ForeignKey(
        Farmacia, 
        on_delete=models.CASCADE, 
        related_name='stock_items'
    )
    
    medicamento = models.ForeignKey(
        Medicamento, 
        on_delete=models.CASCADE, 
        related_name='farmacia_stock'
    )
    
    # Campos variables por farmacia
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)

    class Meta:
        # Asegura que una farmacia solo tenga una entrada para cada medicamento
        unique_together = ('farmacia', 'medicamento')
        verbose_name = "Inventario de Medicamento"
        verbose_name_plural = "Inventario de Medicamentos"

    def __str__(self):
        return f"{self.medicamento.nombre_comercial} en {self.farmacia.nombre}"
    
    
    
class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE','Pendiente'),
        ('ACEPTADO','Aceptado por farmacia'),
        ('EN_CAMINO','En camino'),
        ('ENTREGADO','Entregado'),
        ('RECHAZADO','Rechazado'),
    ]
    
    # El cliente SÍ es el User base
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="pedidos_cliente")
    

    farmacia = models.ForeignKey(
        Farmacia,  # <-- Vinculado al perfil Farmacia
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="pedidos_farmacia"
    )
    
 
    repartidor = models.ForeignKey(
        Repartidor, # <-- Vinculado al perfil Repartidor
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="pedidos_repartidor"
    )
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='CARRITO')
    detalles = models.TextField(blank=True, help_text="Notas adicionales del cliente")
    creado = models.DateTimeField(auto_now_add=True)
    
    # Es útil tener un total en el pedido principal
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    direccion = models.CharField(max_length=255)
    def __str__(self):
        return f"Pedido #{self.id} - Estado: {self.get_estado_display()}"


class DetallePedido(models.Model):
    """
    Representa una línea individual dentro de un Pedido.
    (Ej: 2x Ibuprofeno 600mg)
    """
    # A qué pedido pertenece esta línea
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE, 
        related_name='items' # Permite hacer pedido.items.all()
    )
    
    # Qué medicamento se pidió
    medicamento = models.ForeignKey(
        Medicamento, 
        on_delete=models.PROTECT # Proteger para que no se borre el historial si se borra el med
    )
    
    # Cuántas unidades de ese medicamento
    cantidad = models.PositiveIntegerField(default=1)
    
    # Qué precio tenía CADA UNIDAD al momento de la compra
    precio_unitario_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Qué precio total tiene esta línea (cantidad * precio_unitario)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    receta_adjunta = models.FileField(
            upload_to='recetas_pedidos/', 
            null=True, 
            blank=True
        )
    
    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"

    def save(self, *args, **kwargs):
        # Calcula el subtotal automáticamente
        self.subtotal = self.precio_unitario_snapshot * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad}x {self.medicamento.nombre_comercial} (Pedido #{self.pedido.id})"
    
    

