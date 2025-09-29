from django.urls import path
from . import views

urlpatterns = [
    # Cliente
    path("cliente/", views.cliente_panel, name="cliente_panel"),
    path("cliente/crear/", views.crear_pedido, name="crear_pedido"),

    # Farmacia
    path("farmacia/", views.farmacia_panel, name="farmacia_panel"),
    path("farmacia/aceptar/<int:pedido_id>/", views.farmacia_aceptar, name="farmacia_aceptar"),
    path("farmacia/rechazar/<int:pedido_id>/", views.farmacia_rechazar, name="farmacia_rechazar"),

    # Repartidor
    path("repartidor/", views.repartidor_panel, name="repartidor_panel"),
    path("repartidor/tomar/<int:pedido_id>/", views.repartidor_tomar, name="repartidor_tomar"),
    path("repartidor/entregado/<int:pedido_id>/", views.repartidor_entregado, name="repartidor_entregado"),
]
