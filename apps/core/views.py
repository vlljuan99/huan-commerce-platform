"""
Core views: home page and utility views.
"""
from django.views.generic import TemplateView, DetailView


class IndexView(TemplateView):
    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Renombrado a 'modules' para no colisionar con el context processor 'features'
        # (que expone el dict de feature flags de la instancia).
        context['modules'] = [
            {
                'icon': '📦',
                'title': 'Catálogo',
                'description': 'Productos, variantes, categorías y marcas con gestión de stock.',
            },
            {
                'icon': '🛒',
                'title': 'Pedidos',
                'description': 'Gestión completa de pedidos con estados y seguimiento.',
            },
            {
                'icon': '🧾',
                'title': 'Facturación',
                'description': 'Facturas automáticas con series de numeración y PDF.',
            },
            {
                'icon': '💳',
                'title': 'Pagos',
                'description': 'Integración con Redsys y Stripe para pagos online.',
            },
            {
                'icon': '🚚',
                'title': 'Envíos',
                'description': 'Gestión de transportistas y cálculo de tarifas de envío.',
            },
            {
                'icon': '👥',
                'title': 'Clientes',
                'description': 'Perfiles B2B y B2C con datos fiscales y direcciones.',
            },
        ]
        context['api_endpoints'] = [
            {'method': 'GET', 'path': '/api/products/',       'description': 'Listado de productos'},
            {'method': 'GET', 'path': '/api/products/{slug}/', 'description': 'Detalle de producto'},
            {'method': 'GET', 'path': '/api/categories/',     'description': 'Categorías'},
            {'method': 'GET', 'path': '/api/brands/',         'description': 'Marcas'},
        ]
        return context


class CookiePolicyView(TemplateView):
    template_name = "pages/cookie_policy.html"
