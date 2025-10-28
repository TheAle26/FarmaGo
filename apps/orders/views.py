from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Pedido, DetallePedido, StockMedicamento,Farmacia,Cliente
from apps.orders.utils import es_cliente, es_farmacia, es_repartidor
from .forms import PedidoForm, EditStockMedicamentoForm, AddStockMedicamentoForm
from django.db import transaction, IntegrityError
from django.db.models import F
from django.contrib import messages
from django.db.models import Case, When

# ---------- CLIENTE ----------
@login_required
def cliente_panel(request):
    if not es_cliente(request.user): return HttpResponseForbidden("Solo clientes")
    pedidos = Pedido.objects.filter(cliente=request.user.cliente).order_by("-creado")
    return render(request, "cliente/panel.html", {"pedidos": pedidos})

# orders/views.py

@login_required
def add_to_cart(request, stock_id):
    stock_item = get_object_or_404(StockMedicamento, id=stock_id)
    cantidad = int(request.POST.get('cantidad', 1))
    carrito = request.session.get('carrito', {'farmacias': {}, 'total_general': 0.0})


    farmacia_id = str(stock_item.farmacia.id)
    stock_id_str = str(stock_item.id)

    farmacia_data = carrito['farmacias'].get(farmacia_id, {
        'nombre_farmacia': stock_item.farmacia.nombre,
        'subtotal': 0.0,
        'items': {}
    })

    item_data = farmacia_data['items'].get(stock_id_str, {
        'nombre': stock_item.medicamento.nombre_comercial,
        'precio_unitario': float(stock_item.precio),
        'cantidad': 0
    })

    # Actualizar cantidad y subtotales
    item_data['cantidad'] += cantidad

    #  Guardar todo de vuelta en la sesión
    farmacia_data['items'][stock_id_str] = item_data
    carrito['farmacias'][farmacia_id] = farmacia_data
    
    request.session['carrito'] = carrito # Guardar la sesión
    request.session.modified = True # Marcarla como modificada

    messages.success(request, f"Agregado {stock_item.medicamento.nombre_comercial}.")
    return redirect('ver_carrito')
## me gustaria en realidad que dentro de la view de ver/ buscar remedias, al hacer click en el boton,
# la otra view detecte ese post, tome los datos del  stock_id y se los pase a esta funcion,
# y que esta no tenga return, simplemente ponga el mensajito de agregado



@login_required
def ver_carrito(request):
    carrito_session = request.session.get('carrito', {'farmacias': {}})
    
    carrito_contexto = {
        'farmacias': [],
        'total_general': carrito_session.get('total_general', 0.0)
    }
    
    hay_items_con_receta = False

    for farmacia_id, farmacia_data in carrito_session['farmacias'].items():
        items_contexto = []
        for item_id, item_data in farmacia_data['items'].items():
            try:
                # Obtenemos el objeto real del inventario
                stock_item = StockMedicamento.objects.select_related('medicamento').get(id=item_id)
                
                item_data['stock_obj'] = stock_item
                items_contexto.append(item_data)
                
                if stock_item.medicamento.requiere_receta:
                    hay_items_con_receta = True
                    
            except StockMedicamento.DoesNotExist:
                pass 
        
        farmacia_data['items_enriquecidos'] = items_contexto
        carrito_contexto['farmacias'].append(farmacia_data)

    context = {
        'carrito_data': carrito_contexto,
        'total_general': carrito_contexto['total_general'],
        'hay_items_con_receta': hay_items_con_receta 
    }
    
    return render(request, 'cliente/carrito_detalle.html', context)


# orders/views.py

@login_required
@transaction.atomic
def finalizar_compra_view(request):
    
    if request.method != 'POST':
        return redirect('ver_carrito')

    carrito = request.session.get('carrito')
    
    if not carrito or not carrito.get('farmacias'):
        messages.error(request, "Tu carrito está vacío.")
        return redirect('ver_carrito')

    try:
        pedidos_creados = []
        
        for farmacia_id, farmacia_data in carrito['farmacias'].items():
            farmacia_obj = get_object_or_404(Farmacia, id=farmacia_id)
            
            nuevo_pedido = Pedido.objects.create(
                cliente=request.user,
                farmacia=farmacia_obj,
                estado='PENDIENTE', 
                total=farmacia_data['subtotal']
            )
            
            # Iterar sobre los items de la sesión
            for item_id, item_data in farmacia_data['items'].items():
                stock = StockMedicamento.objects.select_for_update().get(id=item_id)
                
                # (Validación de Stock)
                if stock.stock_actual < item_data['cantidad']:
                    raise Exception(f"Stock insuficiente para {stock.medicamento.nombre_comercial}.")
                
                receta_para_adjuntar = None # Por defecto es Nulo
                
                # 1. Chequear si el medicamento REQUIERE receta
                if stock.medicamento.requiere_receta:
                    # 2. Construir el 'name' del input del formulario
                    file_input_name = f"receta_{item_id}" 
                    
                    # 3. Obtener el archivo de request.FILES
                    receta_file = request.FILES.get(file_input_name)
                    
                    # 4. Validar que el archivo SÍ FUE ENVIADO
                    if not receta_file:
                        raise Exception(f"Falta adjuntar la receta para {stock.medicamento.nombre_comercial}.")
                    
                    receta_para_adjuntar = receta_file


                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    medicamento=stock.medicamento,
                    cantidad=item_data['cantidad'],
                    precio_unitario_snapshot=stock.precio,
                    receta_adjunta=receta_para_adjuntar # <-- Se guarda el archivo
                )
                

                # (Descuento de Stock)
                stock.stock_actual = F('stock_actual') - item_data['cantidad']
                stock.save(update_fields=['stock_actual'])

            pedidos_creados.append(nuevo_pedido.id)

        # (Limpiar sesión y redirigir)
        del request.session['carrito']
        request.session.modified = True
        
        messages.success(request, f"Se generaron {len(pedidos_creados)} pedidos correctamente.")
        return redirect('cliente_panel')

    except Exception as e:
        # Captura "Stock insuficiente" O "Falta adjuntar la receta"
        messages.error(request, str(e))
        return redirect('ver_carrito')
    
    
    
# ---------- FARMACIA ----------
@login_required
def farmacia_panel(request):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    todos_los_pedidos = Pedido.objects.filter(
        farmacia=request.user.farmacia
    )

    pedidos_ordenados = todos_los_pedidos.annotate(
        prioridad_estado=Case(
            When(estado="PENDIENTE", then=0), # Los PENDIENTE van primero
            default=1 # El resto va después
        )
    ).order_by('prioridad_estado', 'creado') # Ordena por prioridad, y luego por fecha

    # Pasa la lista completa y ordenada a la plantilla
    return render(request, "farmacia/farmacia_panel.html", {"pedidos": pedidos_ordenados})

@login_required
def farmacia_aceptar(request, pedido_id):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        estado="PENDIENTE", 
        farmacia=request.user.farmacia 
    )
    pedido.estado = "ACEPTADO"
    pedido.save()
    
    return redirect("farmacia_panel")

@login_required
def farmacia_rechazar(request, pedido_id):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")

    pedido = get_object_or_404(
        Pedido, 
        id=pedido_id, 
        estado="PENDIENTE", 
        farmacia=request.user.farmacia 
    )
    pedido.estado = "RECHAZADO"
    pedido.save()
    
    return redirect("farmacia_panel")

@login_required
def farmacia_gestionar_inventario(request):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")
    farmacia = request.user.farmacia
    stock_items = StockMedicamento.objects.filter(farmacia=farmacia).select_related('medicamento').order_by('medicamento__nombre_comercial')
    add_form = AddStockMedicamentoForm(farmacia=farmacia)
    edit_form = EditStockMedicamentoForm()
    if request.method == 'POST':
        # Procesar el formulario para AÑADIR un nuevo medicamento al stock
        add_form = AddStockMedicamentoForm(farmacia, request.POST)
        if add_form.is_valid():
            medicamento = add_form.cleaned_data['medicamento']
            precio = add_form.cleaned_data['precio']
            stock = add_form.cleaned_data['stock_actual']

            try:
                # Crear el nuevo registro de stock
                StockMedicamento.objects.create(
                    farmacia=farmacia,
                    medicamento=medicamento,
                    precio=precio,
                    stock_actual=stock
                )
                messages.success(request, f"Se agregó {medicamento.nombre_comercial} al inventario.")
                return redirect('gestionar_inventario') # Redirigir para limpiar el form
            except IntegrityError: # Por si acaso intenta agregar uno que ya existe (aunque el form lo evita)
                messages.error(request, f"{medicamento.nombre_comercial} ya existe en tu inventario.")
            except Exception as e:
                 messages.error(request, f"Ocurrió un error al agregar el medicamento: {e}")

        else:
            # Si el form de añadir no es válido, mostramos los errores
             messages.error(request, "Error al agregar el medicamento. Revisa los datos ingresados.")
             edit_form = EditStockMedicamentoForm() # Formulario vacío para editar (contexto)

    else:
        # Si es GET, mostramos un formulario vacío para añadir
        add_form = AddStockMedicamentoForm(farmacia=farmacia)
        edit_form = EditStockMedicamentoForm() # También para el contexto inicial

    context = {
        'stock_items': stock_items,
        'add_form': add_form,
        'edit_form': edit_form, # Usaremos este mismo form para editar en la misma página
    }
    return render(request, "farmacia/inventario.html", context)

@login_required
def farmacia_editar_stock(request, stock_id):
    if not es_farmacia(request.user): 
        return HttpResponseForbidden("Solo farmacias")
    farmacia = request.user.farmacia
    stock_item = get_object_or_404(StockMedicamento, id=stock_id, farmacia=farmacia)

    if request.method == 'POST':
        edit_form = EditStockMedicamentoForm(request.POST, instance=stock_item)
        if edit_form.is_valid():
            edit_form.save()
            messages.success(request, f"Se actualizó el stock de {stock_item.medicamento.nombre_comercial}.")
        else:
            # Si hay errores en el form de edición, volvemos a mostrar la página de inventario
            # con los errores en el formulario de edición.
            messages.error(request, f"Error al actualizar {stock_item.medicamento.nombre_comercial}. Revisa los datos.")
            farmacia_actual = request.user.farmacia
            stock_items = StockMedicamento.objects.filter(farmacia=farmacia_actual).select_related('medicamento').order_by('medicamento__nombre_comercial')
            add_form = AddStockMedicamentoForm(farmacia=farmacia_actual) # Necesario para re-renderizar

            context = {
                'stock_items': stock_items,
                'add_form': add_form,
                'edit_form': edit_form, # Pasamos el form con errores
                'editing_item_id': stock_id # Para saber qué item se estaba editando
            }
            return render(request, 'farmacia/inventario.html', context)

    # Si es GET, redirigimos a la página principal de inventario (la edición se hace in-place)
    return redirect('gestionar_inventario')

# ---------- REPARTIDOR ----------
@login_required
def repartidor_panel(request):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    disponibles = Pedido.objects.filter(estado="ACEPTADO", repartidor__isnull=True)
    # Usar la instancia `Repartidor` asociada al user
    mis = Pedido.objects.filter(repartidor=request.user.repartidor).exclude(estado__in=["ENTREGADO","RECHAZADO"])
    return render(request, "repartidor/panel.html", {"disponibles": disponibles, "mis": mis})

@login_required
def repartidor_tomar(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, estado="ACEPTADO", repartidor__isnull=True)
    # asignar la instancia Repartidor relacionada al user, no el User
    p.repartidor = request.user.repartidor
    p.estado = "EN_CAMINO"
    p.save()
    return redirect("repartidor_panel")

@login_required
def repartidor_entregado(request, pedido_id):
    if not es_repartidor(request.user): return HttpResponseForbidden("Solo repartidores")
    p = get_object_or_404(Pedido, id=pedido_id, repartidor=request.user.repartidor, estado="EN_CAMINO")
    p.estado = "ENTREGADO"
    p.save()
    return redirect("repartidor_panel")


#---------------------pedido----------------


@login_required
def crear_pedido(request):
    form = PedidoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        p = form.save(commit=False)
        p.cliente = request.user
        p.save()
        return redirect("cliente_panel")
    return render(request, "cliente/crearPedido.html", {"form": form})

