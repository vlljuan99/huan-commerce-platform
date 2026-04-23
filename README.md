# Huan Commerce Platform

Plataforma de comercio electrónico modular construida con Django, orientada a B2C/B2B de materiales de construcción.

**Documentación completa:** Ver `../DOCUMENTACION_TECNICA.md` (versión 2.0 con diagramas)

## Estructura del proyecto

```
huan-commerce-platform/
├── manage.py                 # Django management
├── requirements.txt          # Dependencias Python
├── config/                   # Configuración Django
│   ├── settings/
│   │   └── base.py          # Settings base (SQLite para dev)
│   ├── urls/
│   │   └── base.py          # URLs base
│   └── wsgi.py
├── apps/                     # Django apps por dominio
│   ├── core/                # Contratos, modelos base, utilidades
│   ├── accounts/            # Autenticación y usuarios
│   ├── customers/           # Clientes, direcciones
│   ├── catalog/             # Productos, variantes, categorías
│   ├── cart/                # Carrito de compra
│   ├── orders/              # Pedidos
│   ├── billing/             # Fiscalidad, impuestos
│   ├── invoicing/           # Facturas, PDF, descarga
│   ├── payments/            # Transacciones de pago
│   ├── shipping/            # Envíos, transportistas
│   ├── notifications/       # Emails transaccionales
│   ├── seo/                 # SEO técnico
│   ├── backoffice/          # Panel administrativo
│   └── media/               # Gestión de archivos
├── engines/                  # Estrategias intercambiables
│   ├── pricing/             # Cálculo de precios
│   ├── taxes/               # Cálculo de impuestos
│   ├── checkout/            # Flujo de checkout
│   ├── invoicing/           # Generación de facturas
│   └── shipping/            # Cálculo de envíos
├── plugins/                  # Integraciones externas
│   ├── payment_redsys/
│   ├── payment_stripe/
│   ├── erp_holded/
│   └── carrier_seur/
├── themes/                   # Personalización visual
│   ├── default/
│   ├── industrial/
│   └── premium_showroom/
├── instances/                # Configuración por cliente
│   ├── client_a/
│   │   ├── settings.py
│   │   ├── branding.json
│   │   ├── features.json
│   │   └── profile.json
│   └── ...
├── templates/                # Django templates base
├── static/                    # CSS, JS, assets
└── tests/                     # Tests pytest
```

## Setup rápido (desarrollo local)

### 1. Clonar y entrar en la carpeta
```bash
cd huan-commerce-platform
```

### 2. Crear virtual environment
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Migraciones iniciales
```bash
python manage.py migrate
```

### 5. Crear superusuario
```bash
python manage.py createsuperuser
```

### 6. Ejecutar servidor
```bash
python manage.py runserver
```

Accede a http://localhost:8000/admin

## Estructura de modelos

### Clientes
- **User** - Usuario autenticado (extender auth.User)
- **Customer** - Perfil de cliente (B2B/B2C, datos fiscales)
- **CustomerAddress** - Direcciones de envío/facturación

### Catálogo
- **Product** - Producto base
- **ProductVariant** - Variante (color, talla, etc.)
- **ProductCategory** - Categoría
- **ProductBrand** - Marca
- **ProductImage** - Imágenes

### Transaccional
- **Cart** - Carrito de compra
- **CartLineItem** - Línea del carrito
- **Order** - Pedido
- **OrderLineItem** - Línea del pedido
- **PaymentTransaction** - Transacción de pago
- **Shipment** - Envío

### Facturación
- **Invoice** - Factura
- **InvoiceLineItem** - Línea de factura
- **InvoiceSeries** - Serie de numeración
- **TaxRate** - Tipo impositivo

## Contratos (Interfaces)

El core define interfaces que los engines/plugins deben implementar:

- **PricingEngine** - Cálculo de precios
- **TaxEngine** - Cálculo de impuestos
- **CheckoutStrategy** - Flujo de checkout
- **PaymentProvider** - Proveedor de pago
- **ShippingCalculator** - Cálculo de envíos
- **InvoicingEngine** - Generación de facturas
- **ErpConnector** - Integración ERP

Ver `apps/core/contracts.py` para detalles.

## Features (flags)

Configurables en `config/settings/base.py`:

```python
FEATURES = {
    'ENABLE_ONLINE_PAYMENTS': True,
    'ENABLE_PUBLIC_STOCK': False,
    'ENABLE_RECTIFICATIVE_INVOICES': False,
    'ENABLE_B2B_PRICING': False,
    'ENABLE_SIMPLIFIED_CHECKOUT': False,
}
```

## Settings por instancia

Cada cliente tendrá su carpeta `instances/client_name/`:

```
instances/cliente_a/
├── settings.py              # Settings específicas del cliente
├── branding.json            # Logo, colores, textos
├── features.json            # Features activos
└── profile.json             # Perfil del cliente (arquetipos)
```

## Testing

### Ejecutar tests
```bash
pytest tests/
```

### Con cobertura
```bash
pytest --cov=apps tests/
```

## Desarrollo

### Crear app nueva
```bash
python manage.py startapp apps.nombre_app
```

### Ejecutar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### Crear migraciones iniciales (first run)
```bash
python manage.py makemigrations core accounts catalog customers cart orders invoicing billing payments shipping
python manage.py migrate
```

## Próximos pasos

- [ ] Generar fixtures de datos de prueba (factories con factory_boy)
- [ ] Crear primeras vistas y endpoints (API REST)
- [ ] Tests unitarios para modelos críticos
- [ ] Admin de Django (admin.py)
- [ ] Autenticación JWT (DRF authentication)
- [ ] Documentación de API (drf-spectacular)
- [ ] CI/CD con GitHub Actions

## Decisiones técnicas recomendadas

(Ver documento técnico, apartado 26)

1. **Frontend**: Django Templates + Tailwind CSS
2. **Primera pasarela de pago**: Redsys
3. **Stock inicial**: Orientativo (no cantidades exactas)
4. **Checkout**: Estándar completo
5. **Fiscalidad MVP**: Solo IVA estándar
6. **Pedido ↔ Factura**: 1:1 en MVP, modelo preparado para N:M
7. **Renderizado PDF**: WeasyPrint
8. **Automatización**: Manual en MVP, script a partir del 3er cliente

## Troubleshooting

### "No module named 'apps'"
Asegúrate de estar en la raíz del proyecto y ejecutar con `python manage.py ...`

### "django.db.utils.ProgrammingError" en migraciones
Asegúrate de haber ejecutado `python manage.py migrate` primero.

### SQLite en producción
No uses SQLite en producción. Cambiar a PostgreSQL en `config/settings/base.py` para despliegue.

## Contribuyentes

Este proyecto ha sido scaffolded según la arquitectura definida en "Documentación Técnica — Huan Commerce Platform v2.0".

## Licencia

Privado (TBD)
