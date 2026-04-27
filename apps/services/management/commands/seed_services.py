"""
Management command: seed initial service categories, companies, and services.

Usage:
    python manage.py seed_services
"""

from django.core.management.base import BaseCommand
from apps.services.models import Company, ServiceCategory, Service


CATEGORIES = [
    {"name": "Instalación y montaje",   "slug": "instalacion-montaje",   "display_order": 1},
    {"name": "Alicatado y solado",       "slug": "alicatado-solado",       "display_order": 2},
    {"name": "Fontanería",               "slug": "fontaneria",             "display_order": 3},
    {"name": "Pintura y acabados",       "slug": "pintura-acabados",       "display_order": 4},
    {"name": "Electricidad",             "slug": "electricidad",           "display_order": 5},
]

SERVICES = [
    # Instalación y montaje
    {
        "name": "Montaje de baño completo",
        "slug": "montaje-bano-completo",
        "sku": "SRV-MON-001",
        "description": "Montaje e instalación completa de baño: inodoro, lavabo, ducha o bañera, grifería y accesorios. Incluye conexión a fontanería existente.",
        "category_slug": "instalacion-montaje",
        "price": "850.00",
        "unit": "ud",
        "is_featured": True,
    },
    {
        "name": "Montaje de cocina",
        "slug": "montaje-cocina",
        "sku": "SRV-MON-002",
        "description": "Montaje de muebles de cocina, encimera e instalación de electrodomésticos encastrados.",
        "category_slug": "instalacion-montaje",
        "price": "450.00",
        "unit": "ud",
        "is_featured": False,
    },
    # Alicatado y solado
    {
        "name": "Alicatado de cocina",
        "slug": "alicatado-cocina",
        "sku": "SRV-ALI-001",
        "description": "Colocación de azulejos o revestimiento cerámico en cocina. Precio por metro cuadrado, incluye material de agarre y rejuntado.",
        "category_slug": "alicatado-solado",
        "price": "35.00",
        "unit": "m2",
        "is_featured": True,
    },
    {
        "name": "Alicatado de baño",
        "slug": "alicatado-bano",
        "sku": "SRV-ALI-002",
        "description": "Alicatado de paredes de baño. Incluye cortes especiales para huecos y esquinas. Precio por m².",
        "category_slug": "alicatado-solado",
        "price": "40.00",
        "unit": "m2",
        "is_featured": True,
    },
    {
        "name": "Solado de terraza o exterior",
        "slug": "solado-terraza-exterior",
        "sku": "SRV-SOL-001",
        "description": "Colocación de pavimento cerámico antideslizante en terrazas y exteriores. Incluye impermeabilización base.",
        "category_slug": "alicatado-solado",
        "price": "28.00",
        "unit": "m2",
        "is_featured": False,
    },
    {
        "name": "Pavimento interior",
        "slug": "pavimento-interior",
        "sku": "SRV-SOL-002",
        "description": "Colocación de pavimento cerámico o porcelánico en espacios interiores. Precio por m².",
        "category_slug": "alicatado-solado",
        "price": "25.00",
        "unit": "m2",
        "is_featured": False,
    },
    # Fontanería
    {
        "name": "Instalación de grifería",
        "slug": "instalacion-griferia",
        "sku": "SRV-FON-001",
        "description": "Instalación de grifo monomando o termostático en lavabo, fregadero o ducha. Precio por unidad.",
        "category_slug": "fontaneria",
        "price": "120.00",
        "unit": "ud",
        "is_featured": False,
    },
    {
        "name": "Instalación de inodoro",
        "slug": "instalacion-inodoro",
        "sku": "SRV-FON-002",
        "description": "Instalación de inodoro en suelo o suspendido (pared). Incluye conexión a desagüe y agua.",
        "category_slug": "fontaneria",
        "price": "95.00",
        "unit": "ud",
        "is_featured": False,
    },
    {
        "name": "Instalación de plato de ducha o bañera",
        "slug": "instalacion-plato-ducha-banera",
        "sku": "SRV-FON-003",
        "description": "Colocación e instalación de plato de ducha o bañera. Incluye conexión de desagüe y sellado.",
        "category_slug": "fontaneria",
        "price": "150.00",
        "unit": "ud",
        "is_featured": False,
    },
    # Pintura
    {
        "name": "Pintura de habitación",
        "slug": "pintura-habitacion",
        "sku": "SRV-PIN-001",
        "description": "Pintado de paredes y techo de habitación. Incluye imprimación, dos manos de pintura y protección de suelos.",
        "category_slug": "pintura-acabados",
        "price": "12.00",
        "unit": "m2",
        "is_featured": False,
    },
    {
        "name": "Pintura de piso completo",
        "slug": "pintura-piso-completo",
        "sku": "SRV-PIN-002",
        "description": "Pintado completo de vivienda. Precio por m² de superficie útil. Incluye preparación de superficies.",
        "category_slug": "pintura-acabados",
        "price": "10.00",
        "unit": "m2",
        "is_featured": False,
    },
    # Electricidad
    {
        "name": "Sustitución de enchufe o interruptor",
        "slug": "sustitucion-enchufe-interruptor",
        "sku": "SRV-ELE-001",
        "description": "Cambio de enchufe, interruptor o conmutador. Precio por punto eléctrico.",
        "category_slug": "electricidad",
        "price": "45.00",
        "unit": "ud",
        "is_featured": False,
    },
    {
        "name": "Instalación de punto de luz",
        "slug": "instalacion-punto-luz",
        "sku": "SRV-ELE-002",
        "description": "Instalación de nuevo punto de luz (aplique, downlight o superficie). Incluye cableado hasta cuadro.",
        "category_slug": "electricidad",
        "price": "85.00",
        "unit": "ud",
        "is_featured": False,
    },
]


class Command(BaseCommand):
    help = "Seed initial service categories, companies, and services"

    def handle(self, *args, **options):
        # Own company
        company, created = Company.objects.get_or_create(
            is_own=True,
            defaults={
                "name": "Nuestros instaladores",
                "slug": "nuestros-instaladores",
                "description": "Equipo de instaladores propios con más de 10 años de experiencia en reformas del hogar.",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(f"  Empresa creada: {company}")

        # Categories
        cats = {}
        for data in CATEGORIES:
            cat, created = ServiceCategory.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "display_order": data["display_order"],
                    "is_active": True,
                },
            )
            cats[data["slug"]] = cat
            if created:
                self.stdout.write(f"  Categoría creada: {cat}")

        # Services
        for data in SERVICES:
            svc, created = Service.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "sku": data["sku"],
                    "description": data["description"],
                    "category": cats[data["category_slug"]],
                    "company": company,
                    "price": data["price"],
                    "unit": data["unit"],
                    "is_featured": data.get("is_featured", False),
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(f"  Servicio creado: {svc}")

        self.stdout.write(self.style.SUCCESS("Servicios iniciales cargados correctamente."))
