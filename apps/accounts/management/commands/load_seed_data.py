# apps/orders/management/commands/load_seed_data.py

import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

# Importa todos tus modelos
from apps.accounts.models import User, Cliente, Farmacia, Repartidor,ObraSocial
from apps.orders.models import Medicamento, StockMedicamento, Pedido, DetallePedido

# Define la RUTA a tus archivos CSV
# (Asumimos que crearás una carpeta 'data' en la raíz de tu proyecto)
DATA_DIR = os.path.join(settings.BASE_DIR, 'data')

class Command(BaseCommand):
    help = 'Carga datos de prueba (seed data) desde archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument('--only', type=str, help='Cargar solo uno o varios datasets (coma-separados). Ej: --only=medicamentos or --only=medicamentos,stock')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando carga de datos...'))

        # Map keys a métodos
        steps_map = {
            'users': self.load_users,
            'obras_sociales': self.load_obras_sociales,
            'medicamentos': self.load_medicamentos,
            'clientes': self.load_clientes,
            'farmacias': self.load_farmacias,
            'repartidores': self.load_repartidores,
            'stock': self.load_stock,
            'pedidos': self.load_pedidos,
            'detalles': self.load_detalles,
            'farmacia_obras_sociales': self.load_farmacia_obras_sociales,
        }

        # Orden por defecto (para mantener dependencias FK)
        default_order = [
            'users', 'obras_sociales', 'medicamentos', 'clientes', 'farmacias',
            'repartidores', 'stock', 'pedidos', 'detalles', 'farmacia_obras_sociales'
        ]

        only = options.get('only')
        if only:
            requested = [s.strip() for s in only.split(',') if s.strip()]
            # validar
            invalid = [s for s in requested if s not in steps_map]
            if invalid:
                self.stderr.write(self.style.ERROR(f'Clave(s) inválida(s): {invalid}. Opciones válidas: {list(steps_map.keys())}'))
                return
            order = [s for s in default_order if s in requested]
        else:
            order = default_order

        for key in order:
            steps_map[key]()

        self.stdout.write(self.style.SUCCESS('¡Carga de datos completada!'))

    def load_users(self):
        self.stdout.write('Cargando Usuarios...')
        with open(os.path.join(DATA_DIR, 'users.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Usamos create_user para hashear la contraseña
                User.objects.create_user(
                    #id=row['id'],
                    email=row['email'],
                    password=row['password'],
                    first_name=row['first_name'],
                    last_name=row['last_name']
                )

    def load_medicamentos(self):
        self.stdout.write('Cargando Medicamentos...')
        with open(os.path.join(DATA_DIR, 'medicamentos.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Medicamento.objects.create(
                    #id=row['id'],
                    nombre_comercial=row['nombre_comercial'],
                    principio_activo=row['principio_activo'],
                    concentracion=row['concentracion'],
                    requiere_receta=row['requiere_receta'].lower() == 'true'
                )

    def load_clientes(self):
        self.stdout.write('Cargando Clientes...')
        with open(os.path.join(DATA_DIR, 'clientes.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = User.objects.get(id=row['user_id'])
                Cliente.objects.create(
                    #id=row['id'],
                    user=user,
                    nombre=row['nombre'],
                    apellido=row['apellido'],
                    documento=row['documento'],
                    edad=row['edad'],
                    direccion=row['direccion'],
                    telefono=row['telefono'],
                    terms_cond=True
                )

    def load_farmacias(self):
        self.stdout.write('Cargando Farmacias...')
        with open(os.path.join(DATA_DIR, 'farmacias.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = User.objects.get(id=row['user_id'])
                Farmacia.objects.create(
                    #id=row['id'],
                    user=user,
                    nombre=row['nombre'],
                    direccion=row['direccion'],
                    valido=row['valido'].lower() == 'true',
                    cuit=row['cuit'] # <-- AÑADIR ESTA LÍNEA
                )

    def load_repartidores(self):
        self.stdout.write('Cargando Repartidores...')
        with open(os.path.join(DATA_DIR, 'repartidores.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = User.objects.get(id=row['user_id'])
                
                # Manejar la patente (puede estar vacía si es 'bicicleta')
                patente_val = row['patente'] if row['patente'] else None
                
                Repartidor.objects.create(
                    #id=row['id'],
                    user=user,
                    cuit=row['cuit'], # <-- AÑADIDO
                    vehiculo=row['vehiculo'], # <-- VALOR CORREGIDO
                    patente=patente_val, # <-- AÑADIDO
                    
                    # 💥 SOLUCIÓN para ImageField obligatorio 💥
                    # Asignamos una ruta ficticia para satisfacer 'null=False'
                    antecedentes='antecedentes_repartidores/dummy_seed.png', 
                    
                    disponible=True,
                    valido=row['valido'].lower() == 'true'
                )

    def load_stock(self):
        self.stdout.write('Cargando Stock...')
        with open(os.path.join(DATA_DIR, 'stock.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                farmacia = Farmacia.objects.get(id=row['farmacia_id'])
                medicamento = Medicamento.objects.get(id=row['medicamento_id'])
                StockMedicamento.objects.create(
                    farmacia=farmacia,
                    medicamento=medicamento,
                    # 💥 CONVERTIR A NÚMEROS 💥
                    precio=float(row['precio']),
                    stock_actual=int(row['stock_actual'])
                )

    def load_pedidos(self):
        self.stdout.write('Cargando Pedidos...')
        with open(os.path.join(DATA_DIR, 'pedidos.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                cliente = Cliente.objects.get(id=row['cliente_id'])
                farmacia = Farmacia.objects.get(id=row['farmacia_id'])
                repartidor = Repartidor.objects.get(id=row['repartidor_id']) if row.get('repartidor_id') else None
                
                Pedido.objects.create(
                   # id=row['id'],
                    cliente=cliente,
                    farmacia=farmacia,
                    repartidor=repartidor,
                    estado=row['estado'],
                    # 💥 CONVERTIR A NÚMERO 💥
                    total=float(row['total'])
                )

    def load_detalles(self):
        self.stdout.write('Cargando Detalles de Pedidos...')
        with open(os.path.join(DATA_DIR, 'detalles.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                pedido = Pedido.objects.get(id=row['pedido_id'])
                medicamento = Medicamento.objects.get(id=row['medicamento_id'])
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    medicamento=medicamento,
                    # 💥 CONVERTIR A NÚMEROS 💥
                    cantidad=int(row['cantidad']),
                    precio_unitario_snapshot=float(row['precio_unitario_snapshot'])
                )
                
    def load_obras_sociales(self):
        self.stdout.write('Cargando Obras Sociales...')
        with open(os.path.join(DATA_DIR, 'obras_sociales.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ObraSocial.objects.create(
                    #id=row['id'],
                    nombre=row['nombre']
                )
                
    def load_farmacia_obras_sociales(self):
        self.stdout.write('Cargando relaciones Farmacia-ObraSocial...')
        
        # ¡Importante! Esta es la forma de obtener el modelo
        # de la tabla intermedia automática de Django.
        # Asumimos que el campo en tu modelo Farmacia se llama 'obras_sociales'
        ThroughModel = Farmacia.obras_sociales.through
        
        with open(os.path.join(DATA_DIR, 'farmacia_obrasocial.csv'), 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Creamos la relación usando los IDs directamente
                ThroughModel.objects.create(
                   # id=row['id'],
                    farmacia_id=row['farmacia_id'],
                    obrasocial_id=row['obrasocial_id']
                )