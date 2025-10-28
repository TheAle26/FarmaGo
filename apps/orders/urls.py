from django.urls import path
from . import views

urlpatterns = [
    # Cliente
    path("cliente/", views.cliente_panel, name="cliente_panel"),
    path("cliente/carrito/", views.ver_carrito, name="ver_carrito"),
    path("cliente/carrito/finalizar_compra", views.finalizar_compra_view, name="finalizar_compra"),
    
    # Farmacia
    path("farmacia/", views.farmacia_panel, name="farmacia_panel"),
    path("farmacia/pedidos/", views.farmacia_pedidos_entrantes, name="farmacia_pedidos"),
    path("farmacia/aceptar/<int:pedido_id>/", views.farmacia_aceptar, name="farmacia_aceptar"),
    path("farmacia/rechazar/<int:pedido_id>/", views.farmacia_rechazar, name="farmacia_rechazar"),
    path("farmacia/inventario/", views.farmacia_gestionar_inventario, name="gestionar_inventario"),
    path("farmacia/inventario/modificar/<int:stock_id>/", views.farmacia_editar_stock, name="editar_stock"),

    # Repartidor
    path("repartidor/", views.repartidor_panel, name="repartidor_panel"),
    path("repartidor/tomar/<int:pedido_id>/", views.repartidor_tomar, name="repartidor_tomar"),
    path("repartidor/entregado/<int:pedido_id>/", views.repartidor_entregado, name="repartidor_entregado"),
    
    # Panel principal (redirige según tipo de perfil)
    path("panel/", views.panel_principal, name="panel_principal"),
]
