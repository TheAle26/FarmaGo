from django.db import models
from django.conf import settings   # va esto pq cambie el user de default 
# uno propio, para la baja logica

class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE','Pendiente'),
        ('ACEPTADO','Aceptado por farmacia'),
        ('EN_CAMINO','En camino'),
        ('ENTREGADO','Entregado'),
        ('RECHAZADO','Rechazado'),
    ]
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pedidos_cliente")
    farmacia = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="pedidos_farmacia")
    repartidor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="pedidos_repartidor")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    detalles = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
