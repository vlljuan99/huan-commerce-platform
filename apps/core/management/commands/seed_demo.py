"""
Management command: seed_demo
Carga datos de prueba realistas para la instancia helvagres_demo.
Distribuidor de materiales cerámicos B2B.

Uso:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # borra todos los datos antes de insertar
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import datetime


class Command(BaseCommand):
    help = 'Carga datos de prueba para helvagres_demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina datos existentes antes de insertar',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        self.stdout.write('Cargando datos de prueba...\n')

        tax_rates = self._seed_tax_rates()
        self._seed_shipping_methods()
        series = self._seed_invoice_series()
        variants = self._seed_catalog(tax_rates)
        customers = self._seed_users_and_customers()
        orders = self._seed_orders(customers, variants)
        self._seed_invoices(customers, orders, series, tax_rates)

        self.stdout.write(self.style.SUCCESS('\n✓ Datos de prueba cargados correctamente.\n'))
        self.stdout.write('  Superusuario:  admin@helvagres.es  /  admin1234\n')
        self.stdout.write('  Clientes B2B:  construcciones.martin@example.com  /  demo1234\n')
        self.stdout.write('                 obra.rodriguez@example.com  /  demo1234\n')
        self.stdout.write('  Cliente B2C:   cliente.retail@example.com  /  demo1234\n')

    # ──────────────────────────────────────────────────────────────────
    # FLUSH
    # ──────────────────────────────────────────────────────────────────

    def _flush(self):
        from apps.invoicing.models import InvoiceLineItem, Invoice, InvoiceSeries
        from apps.orders.models import OrderLineItem, Order
        from apps.customers.models import CustomerAddress, Customer
        from apps.accounts.models import User
        from apps.catalog.models import ProductVariant, Product, ProductBrand, ProductCategory
        from apps.billing.models import TaxRate
        from apps.shipping.models import ShippingMethod

        self.stdout.write('  Eliminando datos existentes...')
        InvoiceLineItem.objects.all().delete()
        Invoice.objects.all().delete()
        InvoiceSeries.objects.all().delete()
        OrderLineItem.objects.all().delete()
        Order.objects.all().delete()
        CustomerAddress.objects.all().delete()
        Customer.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        User.objects.filter(is_superuser=True, email='admin@helvagres.es').delete()
        ProductVariant.objects.all().delete()
        Product.objects.all().delete()
        ProductBrand.objects.all().delete()
        ProductCategory.objects.all().delete()
        TaxRate.objects.all().delete()
        ShippingMethod.objects.all().delete()
        self.stdout.write(self.style.WARNING('  ✓ Flush completado.\n'))

    # ──────────────────────────────────────────────────────────────────
    # TAX RATES
    # ──────────────────────────────────────────────────────────────────

    def _seed_tax_rates(self):
        from apps.billing.models import TaxRate

        data = [
            {'name': 'IVA General 21%',    'rate': Decimal('21.00'), 'code': 'VAT_ES_STANDARD'},
            {'name': 'IVA Reducido 10%',   'rate': Decimal('10.00'), 'code': 'VAT_ES_REDUCED'},
            {'name': 'IVA Superreducido 4%', 'rate': Decimal('4.00'),  'code': 'VAT_ES_SUPER_REDUCED'},
            {'name': 'Exento 0%',          'rate': Decimal('0.00'),  'code': 'VAT_ES_EXEMPT'},
        ]

        created = {}
        for d in data:
            obj, new = TaxRate.objects.get_or_create(code=d['code'], defaults=d)
            created[d['code']] = obj
            status = 'creado' if new else 'ya existía'
            self.stdout.write(f'  TaxRate [{status}]: {obj}')

        return created

    # ──────────────────────────────────────────────────────────────────
    # SHIPPING METHODS
    # ──────────────────────────────────────────────────────────────────

    def _seed_shipping_methods(self):
        from apps.shipping.models import ShippingMethod

        data = [
            {'name': 'Transporte estándar',     'code': 'STANDARD',  'base_cost': Decimal('8.50')},
            {'name': 'Transporte express 24h',  'code': 'EXPRESS',   'base_cost': Decimal('18.00')},
            {'name': 'Recogida en almacén',     'code': 'PICKUP',    'base_cost': Decimal('0.00')},
            {'name': 'Pallet completo',         'code': 'PALLET',    'base_cost': Decimal('45.00')},
        ]

        for d in data:
            obj, new = ShippingMethod.objects.get_or_create(code=d['code'], defaults=d)
            status = 'creado' if new else 'ya existía'
            self.stdout.write(f'  ShippingMethod [{status}]: {obj}')

    # ──────────────────────────────────────────────────────────────────
    # INVOICE SERIES
    # ──────────────────────────────────────────────────────────────────

    def _seed_invoice_series(self):
        from apps.invoicing.models import InvoiceSeries

        obj, new = InvoiceSeries.objects.get_or_create(
            name='FACT 2026',
            defaults={'prefix': 'FACT', 'next_number': 1, 'year': 2026},
        )
        status = 'creada' if new else 'ya existía'
        self.stdout.write(f'  InvoiceSeries [{status}]: {obj}')
        return obj

    # ──────────────────────────────────────────────────────────────────
    # CATALOG
    # ──────────────────────────────────────────────────────────────────

    def _seed_catalog(self, tax_rates):
        from apps.catalog.models import ProductCategory, ProductBrand, Product, ProductVariant

        # ── Categorías ────────────────────────────────────────────────
        cat_data = [
            {'name': 'Gres Porcelánico',        'slug': 'gres-porcelanico',     'display_order': 1},
            {'name': 'Azulejos y Revestimientos','slug': 'azulejos-revestimientos','display_order': 2},
            {'name': 'Morteros y Adhesivos',    'slug': 'morteros-adhesivos',   'display_order': 3},
            {'name': 'Herramientas y Útiles',   'slug': 'herramientas-utiles',  'display_order': 4},
        ]
        categories = {}
        for d in cat_data:
            obj, new = ProductCategory.objects.get_or_create(slug=d['slug'], defaults=d)
            categories[d['slug']] = obj
            self.stdout.write(f'  Category [{("creada" if new else "ya existía")}]: {obj}')

        # ── Marcas ────────────────────────────────────────────────────
        brand_data = [
            {'name': 'Porcelangres',  'slug': 'porcelangres',  'description': 'Fabricante español de gres porcelánico técnico'},
            {'name': 'Butech',        'slug': 'butech',        'description': 'Sistemas de colocación cerámica de Porcelanosa'},
            {'name': 'Ardex',         'slug': 'ardex',         'description': 'Morteros y adhesivos de alta resistencia'},
            {'name': 'Rubi',          'slug': 'rubi',          'description': 'Herramientas profesionales para cerámica'},
        ]
        brands = {}
        for d in brand_data:
            obj, new = ProductBrand.objects.get_or_create(slug=d['slug'], defaults=d)
            brands[d['slug']] = obj
            self.stdout.write(f'  Brand [{("creada" if new else "ya existía")}]: {obj}')

        # ── Productos y variantes ─────────────────────────────────────
        products_spec = [
            {
                'product': {
                    'name': 'Gres Porcelánico Marquina Negro 60x60',
                    'slug': 'gres-porcelanico-marquina-negro-60x60',
                    'description': 'Gres porcelánico rectificado imitación mármol negro marquina. Formato 60×60 cm. Ideal para pavimentos y revestimientos interiores de alta gama.',
                    'category': categories['gres-porcelanico'],
                    'brand': brands['porcelangres'],
                    'sku_base': 'GP-MQ-60',
                    'unit_of_measure': 'm2',
                    'weight': Decimal('20.00'),
                    'is_featured': True,
                },
                'variants': [
                    {'sku': 'GP-MQ-60-MATE',  'name': 'Acabado Mate',  'price_no_tax': Decimal('22.50'), 'stock_quantity': 240},
                    {'sku': 'GP-MQ-60-PORC',  'name': 'Acabado Pulido', 'price_no_tax': Decimal('25.80'), 'stock_quantity': 180},
                ],
            },
            {
                'product': {
                    'name': 'Gres Porcelánico Cemento Gris 45x45',
                    'slug': 'gres-porcelanico-cemento-gris-45x45',
                    'description': 'Pavimento cerámico efecto cemento. Formato 45×45. Muy versátil para usos residenciales y comerciales.',
                    'category': categories['gres-porcelanico'],
                    'brand': brands['porcelangres'],
                    'sku_base': 'GP-CG-45',
                    'unit_of_measure': 'm2',
                    'weight': Decimal('18.50'),
                    'is_featured': False,
                },
                'variants': [
                    {'sku': 'GP-CG-45-GR',   'name': 'Gris Medio',  'price_no_tax': Decimal('14.90'), 'stock_quantity': 520},
                    {'sku': 'GP-CG-45-AN',   'name': 'Antracita',   'price_no_tax': Decimal('14.90'), 'stock_quantity': 310},
                    {'sku': 'GP-CG-45-BL',   'name': 'Blanco Cemento', 'price_no_tax': Decimal('14.90'), 'stock_quantity': 95},
                ],
            },
            {
                'product': {
                    'name': 'Azulejo Hidráulico 20x20',
                    'slug': 'azulejo-hidraulico-20x20',
                    'description': 'Azulejo de pared efecto hidráulico. Colores vivos. Muy usado en cocinas y baños de estilo mediterráneo.',
                    'category': categories['azulejos-revestimientos'],
                    'brand': brands['porcelangres'],
                    'sku_base': 'AZ-HID-20',
                    'unit_of_measure': 'm2',
                    'weight': Decimal('12.00'),
                    'is_featured': True,
                },
                'variants': [
                    {'sku': 'AZ-HID-20-AZ',  'name': 'Azul Cobalto', 'price_no_tax': Decimal('18.40'), 'stock_quantity': 150},
                    {'sku': 'AZ-HID-20-VE',  'name': 'Verde Agua',   'price_no_tax': Decimal('18.40'), 'stock_quantity': 120},
                ],
            },
            {
                'product': {
                    'name': 'Adhesivo C2TE Butech Flex White 25kg',
                    'slug': 'adhesivo-c2te-butech-flex-white-25kg',
                    'description': 'Mortero cola cementoso mejorado con deslizamiento reducido. Apto para grandes formatos y fachadas. Saco 25 kg.',
                    'category': categories['morteros-adhesivos'],
                    'brand': brands['butech'],
                    'sku_base': 'AD-C2TE-25',
                    'unit_of_measure': 'saco',
                    'weight': Decimal('25.00'),
                    'is_featured': False,
                },
                'variants': [
                    {'sku': 'AD-C2TE-25-WH', 'name': 'Blanco 25 kg',  'price_no_tax': Decimal('12.80'), 'stock_quantity': 640},
                    {'sku': 'AD-C2TE-25-GR', 'name': 'Gris 25 kg',    'price_no_tax': Decimal('12.80'), 'stock_quantity': 480},
                ],
            },
            {
                'product': {
                    'name': 'Lechada Junta Ardex FL 5kg',
                    'slug': 'lechada-junta-ardex-fl-5kg',
                    'description': 'Lechada cementosa flexible para juntas de 1-6 mm. Resistente al agua. Disponible en múltiples colores. Saco 5 kg.',
                    'category': categories['morteros-adhesivos'],
                    'brand': brands['ardex'],
                    'sku_base': 'LE-FL-5',
                    'unit_of_measure': 'saco',
                    'weight': Decimal('5.00'),
                    'is_featured': False,
                },
                'variants': [
                    {'sku': 'LE-FL-5-BL',    'name': 'Blanco 5 kg',   'price_no_tax': Decimal('6.90'),  'stock_quantity': 300},
                    {'sku': 'LE-FL-5-GR',    'name': 'Gris 5 kg',     'price_no_tax': Decimal('6.90'),  'stock_quantity': 280},
                    {'sku': 'LE-FL-5-ANT',   'name': 'Antracita 5 kg','price_no_tax': Decimal('7.20'),  'stock_quantity': 140},
                ],
            },
            {
                'product': {
                    'name': 'Cortadora Rubi TX-1020',
                    'slug': 'cortadora-rubi-tx-1020',
                    'description': 'Cortadora manual profesional hasta 1020 mm. Disco widia 22 mm. Para formatos grandes de gres porcelánico.',
                    'category': categories['herramientas-utiles'],
                    'brand': brands['rubi'],
                    'sku_base': 'HE-TX1020',
                    'unit_of_measure': 'unit',
                    'weight': Decimal('9.20'),
                    'is_featured': False,
                },
                'variants': [
                    {'sku': 'HE-TX1020-STD', 'name': 'Estándar',       'price_no_tax': Decimal('189.00'), 'stock_quantity': 12},
                ],
            },
        ]

        all_variants = []
        for spec in products_spec:
            p_defaults = dict(spec['product'])
            slug = p_defaults.pop('slug') if 'slug' in p_defaults else None
            p_defaults['slug'] = slug or p_defaults['name']

            prod, new = Product.objects.get_or_create(
                slug=slug,
                defaults=p_defaults,
            )
            self.stdout.write(f'  Product [{("creado" if new else "ya existía")}]: {prod}')

            for v_data in spec['variants']:
                sku = v_data['sku']
                v, new_v = ProductVariant.objects.get_or_create(
                    sku=sku,
                    defaults={**v_data, 'product': prod},
                )
                all_variants.append(v)
                self.stdout.write(f'    Variant [{("creada" if new_v else "ya existía")}]: {v.sku}')

        return all_variants

    # ──────────────────────────────────────────────────────────────────
    # USERS & CUSTOMERS
    # ──────────────────────────────────────────────────────────────────

    def _seed_users_and_customers(self):
        from apps.accounts.models import User
        from apps.customers.models import Customer, CustomerAddress

        pwd_admin = make_password('admin1234')
        pwd_demo = make_password('demo1234')

        users_spec = [
            {
                'user': {
                    'username': 'admin',
                    'email': 'admin@helvagres.es',
                    'first_name': 'Admin',
                    'last_name': 'Helvagres',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True,
                    'password': pwd_admin,
                },
                'customer': None,
            },
            {
                'user': {
                    'username': 'martin_obras',
                    'email': 'construcciones.martin@example.com',
                    'first_name': 'Jesús',
                    'last_name': 'Martín Sánchez',
                    'role': 'customer',
                    'password': pwd_demo,
                },
                'customer': {
                    'company_name': 'Construcciones Martín S.L.',
                    'fiscal_name': 'CONSTRUCCIONES MARTÍN SÁNCHEZ S.L.',
                    'tax_id': 'B-12345678',
                    'phone': '962 100 200',
                    'contact_email': 'facturacion@construccionesmartin.es',
                    'segment': 'b2b',
                    'notes': 'Cliente desde 2020. Obra habitual en Valencia y provincia. Pago a 30 días.',
                },
                'addresses': [
                    {
                        'name': 'Almacén principal',
                        'address_type': 'shipping',
                        'street_address': 'Polígono Industrial La Fuente, Nave 14',
                        'city': 'Paterna',
                        'postal_code': '46980',
                        'region': 'Valencia',
                        'country': 'España',
                        'is_default': True,
                    },
                    {
                        'name': 'Sede fiscal',
                        'address_type': 'billing',
                        'street_address': 'Calle Mayor, 45, 2º A',
                        'city': 'Valencia',
                        'postal_code': '46001',
                        'region': 'Valencia',
                        'country': 'España',
                        'is_default': True,
                    },
                ],
            },
            {
                'user': {
                    'username': 'rodriguez_alicante',
                    'email': 'obra.rodriguez@example.com',
                    'first_name': 'Ana',
                    'last_name': 'Rodríguez Ferrer',
                    'role': 'customer',
                    'password': pwd_demo,
                },
                'customer': {
                    'company_name': 'Reformas Rodríguez',
                    'fiscal_name': 'ANA RODRÍGUEZ FERRER',
                    'tax_id': '44887766X',
                    'phone': '965 300 400',
                    'contact_email': 'obra.rodriguez@example.com',
                    'segment': 'b2b',
                    'notes': 'Autónoma. Obras de reforma en la Costa Blanca. Pago a la entrega.',
                },
                'addresses': [
                    {
                        'name': 'Dirección de obra / almacén',
                        'address_type': 'both',
                        'street_address': 'Avenida del Mediterráneo, 88',
                        'city': 'Alicante',
                        'postal_code': '03003',
                        'region': 'Alicante',
                        'country': 'España',
                        'is_default': True,
                    },
                ],
            },
            {
                'user': {
                    'username': 'cliente_retail',
                    'email': 'cliente.retail@example.com',
                    'first_name': 'María',
                    'last_name': 'González López',
                    'role': 'customer',
                    'password': pwd_demo,
                },
                'customer': {
                    'company_name': '',
                    'fiscal_name': 'María González López',
                    'tax_id': None,
                    'phone': '600 123 456',
                    'contact_email': 'cliente.retail@example.com',
                    'segment': 'b2c',
                    'notes': 'Particular. Reforma baño vivienda habitual.',
                },
                'addresses': [
                    {
                        'name': 'Domicilio',
                        'address_type': 'both',
                        'street_address': 'Calle Roses, 12, 3º 2ª',
                        'city': 'Castellón de la Plana',
                        'postal_code': '12004',
                        'region': 'Castellón',
                        'country': 'España',
                        'is_default': True,
                    },
                ],
            },
        ]

        customers_out = []
        for spec in users_spec:
            u_data = spec['user']
            user, new = User.objects.get_or_create(
                email=u_data['email'],
                defaults=u_data,
            )
            if not new:
                # Update password so it is always fresh
                user.set_password('admin1234' if user.is_superuser else 'demo1234')
                user.save(update_fields=['password'])
            self.stdout.write(f'  User [{("creado" if new else "ya existía")}]: {user.email}')

            if spec.get('customer'):
                c_data = spec['customer']
                cust, new_c = Customer.objects.get_or_create(
                    user=user,
                    defaults=c_data,
                )
                self.stdout.write(f'    Customer [{("creado" if new_c else "ya existía")}]: {cust}')

                for addr_data in spec.get('addresses', []):
                    addr, new_a = CustomerAddress.objects.get_or_create(
                        customer=cust,
                        name=addr_data['name'],
                        defaults={**addr_data, 'customer': cust},
                    )
                    self.stdout.write(f'      Address [{("creada" if new_a else "ya existía")}]: {addr.name}')

                customers_out.append(cust)

        return customers_out

    # ──────────────────────────────────────────────────────────────────
    # ORDERS
    # ──────────────────────────────────────────────────────────────────

    def _seed_orders(self, customers, variants):
        from apps.orders.models import Order, OrderLineItem

        tz = timezone.get_current_timezone()

        def _dt(year, month, day):
            return timezone.make_aware(
                datetime.datetime(year, month, day, 9, 0, 0), tz
            )

        # variant helpers
        def _v(sku):
            for v in variants:
                if v.sku == sku:
                    return v
            return None

        martin = customers[0]
        rodriguez = customers[1]
        retail = customers[2]

        orders_spec = [
            # ── Pedido 1: Martín, entregado ───────────────────────────
            {
                'order': {
                    'order_number': 'ORD-2026-001',
                    'customer': martin,
                    'status': 'delivered',
                    'shipping_cost': Decimal('45.00'),
                    'notes': 'Obra calle Colón 7. Entregar en planta baja.',
                    'shipping_address_snapshot': 'Polígono Industrial La Fuente, Nave 14\n46980 Paterna (Valencia)\nEspaña',
                    'billing_address_snapshot': 'CONSTRUCCIONES MARTÍN SÁNCHEZ S.L.\nB-12345678\nCalle Mayor, 45, 2º A\n46001 Valencia\nEspaña',
                    'confirmed_at': _dt(2026, 2, 5),
                },
                'lines': [
                    {'variant_sku': 'GP-MQ-60-MATE',  'qty': Decimal('85.00'),  'price': Decimal('22.50'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'AD-C2TE-25-GR',  'qty': Decimal('40.00'),  'price': Decimal('12.80'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'LE-FL-5-GR',     'qty': Decimal('20.00'),  'price': Decimal('6.90'),  'tax_pct': Decimal('21.00')},
                ],
            },
            # ── Pedido 2: Martín, procesando ──────────────────────────
            {
                'order': {
                    'order_number': 'ORD-2026-002',
                    'customer': martin,
                    'status': 'processing',
                    'shipping_cost': Decimal('45.00'),
                    'notes': '',
                    'shipping_address_snapshot': 'Polígono Industrial La Fuente, Nave 14\n46980 Paterna (Valencia)\nEspaña',
                    'billing_address_snapshot': 'CONSTRUCCIONES MARTÍN SÁNCHEZ S.L.\nB-12345678\nCalle Mayor, 45, 2º A\n46001 Valencia\nEspaña',
                    'confirmed_at': _dt(2026, 4, 10),
                },
                'lines': [
                    {'variant_sku': 'GP-CG-45-GR',   'qty': Decimal('120.00'), 'price': Decimal('14.90'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'GP-CG-45-AN',   'qty': Decimal('60.00'),  'price': Decimal('14.90'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'AD-C2TE-25-WH', 'qty': Decimal('60.00'),  'price': Decimal('12.80'), 'tax_pct': Decimal('21.00')},
                ],
            },
            # ── Pedido 3: Rodríguez, confirmado ───────────────────────
            {
                'order': {
                    'order_number': 'ORD-2026-003',
                    'customer': rodriguez,
                    'status': 'confirmed',
                    'shipping_cost': Decimal('18.00'),
                    'notes': 'Entrega preferible por la mañana.',
                    'shipping_address_snapshot': 'Avenida del Mediterráneo, 88\n03003 Alicante (Alicante)\nEspaña',
                    'billing_address_snapshot': 'ANA RODRÍGUEZ FERRER\n44887766X\nAvenida del Mediterráneo, 88\n03003 Alicante\nEspaña',
                    'confirmed_at': _dt(2026, 4, 18),
                },
                'lines': [
                    {'variant_sku': 'AZ-HID-20-AZ',  'qty': Decimal('32.00'),  'price': Decimal('18.40'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'LE-FL-5-BL',    'qty': Decimal('8.00'),   'price': Decimal('6.90'),  'tax_pct': Decimal('21.00')},
                ],
            },
            # ── Pedido 4: Retail B2C, pendiente ───────────────────────
            {
                'order': {
                    'order_number': 'ORD-2026-004',
                    'customer': retail,
                    'status': 'pending',
                    'shipping_cost': Decimal('8.50'),
                    'notes': '',
                    'shipping_address_snapshot': 'Calle Roses, 12, 3º 2ª\n12004 Castellón de la Plana (Castellón)\nEspaña',
                    'billing_address_snapshot': 'María González López\nCalle Roses, 12, 3º 2ª\n12004 Castellón de la Plana\nEspaña',
                    'confirmed_at': None,
                },
                'lines': [
                    {'variant_sku': 'AZ-HID-20-VE',  'qty': Decimal('12.00'),  'price': Decimal('18.40'), 'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'LE-FL-5-ANT',   'qty': Decimal('3.00'),   'price': Decimal('7.20'),  'tax_pct': Decimal('21.00')},
                    {'variant_sku': 'HE-TX1020-STD', 'qty': Decimal('1.00'),   'price': Decimal('189.00'),'tax_pct': Decimal('21.00')},
                ],
            },
        ]

        orders_out = []
        for spec in orders_spec:
            o_data = spec['order']
            order_number = o_data['order_number']

            if Order.objects.filter(order_number=order_number).exists():
                self.stdout.write(f'  Order [ya existía]: {order_number}')
                orders_out.append(Order.objects.get(order_number=order_number))
                continue

            # Calculate totals
            subtotal = Decimal('0.00')
            tax_total = Decimal('0.00')
            for line in spec['lines']:
                line_sub = line['qty'] * line['price']
                line_tax = line_sub * line['tax_pct'] / Decimal('100')
                subtotal += line_sub
                tax_total += line_tax

            total = subtotal + tax_total + o_data['shipping_cost']

            order = Order.objects.create(
                **o_data,
                subtotal=subtotal.quantize(Decimal('0.01')),
                tax_amount=tax_total.quantize(Decimal('0.01')),
                total=total.quantize(Decimal('0.01')),
            )

            for line in spec['lines']:
                v = _v(line['variant_sku'])
                line_sub = (line['qty'] * line['price']).quantize(Decimal('0.01'))
                line_tax = (line_sub * line['tax_pct'] / Decimal('100')).quantize(Decimal('0.01'))
                OrderLineItem.objects.create(
                    order=order,
                    variant=v,
                    product_name=v.product.name if v else '',
                    sku=line['variant_sku'],
                    quantity=line['qty'],
                    unit_price=line['price'],
                    tax_rate_pct=line['tax_pct'],
                    tax_amount=line_tax,
                    line_total=line_sub,
                )

            self.stdout.write(f'  Order [creado]: {order.order_number}  total={order.total} €')
            orders_out.append(order)

        return orders_out

    # ──────────────────────────────────────────────────────────────────
    # INVOICES
    # ──────────────────────────────────────────────────────────────────

    def _seed_invoices(self, customers, orders, series, tax_rates):
        from apps.invoicing.models import Invoice, InvoiceLineItem

        tz = timezone.get_current_timezone()
        iva21 = tax_rates['VAT_ES_STANDARD']

        # Only generate invoice for the first order (delivered)
        invoiceable = [
            (orders[0], '2026-01', customers[0]),  # ORD-2026-001, Martín
            (orders[1], '2026-02', customers[0]),  # ORD-2026-002, Martín
        ]

        for order, suffix, customer in invoiceable:
            inv_number_str = f'FACT-{suffix}'
            if Invoice.objects.filter(invoice_number=inv_number_str).exists():
                self.stdout.write(f'  Invoice [ya existía]: {inv_number_str}')
                continue

            num = series.get_next_number()
            issued = timezone.make_aware(
                datetime.datetime(2026, int(suffix.split('-')[1]), 20, 10, 0), tz
            )
            due = issued.date() + datetime.timedelta(days=30)

            subtotal = order.subtotal
            tax = order.tax_amount
            total = subtotal + tax

            inv = Invoice.objects.create(
                customer=customer,
                order=order,
                series=series,
                number=num,
                invoice_number=inv_number_str,
                issued_at=issued,
                status='issued' if order.status == 'delivered' else 'draft',
                subtotal=subtotal,
                tax_amount=tax,
                total=total,
                billing_name_snapshot=customer.billing_name,
                tax_id_snapshot=customer.tax_id or '',
                billing_address_snapshot=order.billing_address_snapshot,
                due_date=due,
                notes='',
            )

            # Line items mirroring order lines
            for item in order.items.select_related('variant__product'):
                InvoiceLineItem.objects.create(
                    invoice=inv,
                    description=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                    tax_rate=iva21,
                    tax_rate_pct=item.tax_rate_pct,
                    tax_amount=item.tax_amount,
                )

            self.stdout.write(
                f'  Invoice [creada]: {inv.invoice_number}  total={inv.total} €  estado={inv.status}'
            )
