"""
Public views for the Services section.
"""

from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Service, ServiceCategory, Company


class ServiceListView(View):
    template_name = "services/service_list.html"
    paginate_by = 24

    def get(self, request):
        qs = Service.objects.filter(is_active=True).select_related(
            "category", "company"
        )

        category_slug = request.GET.get("categoria", "").strip()
        company_slug = request.GET.get("empresa", "").strip()
        q = request.GET.get("q", "").strip()

        active_category = None
        active_company = None

        if category_slug:
            cat = ServiceCategory.objects.filter(
                slug=category_slug, is_active=True
            ).first()
            if cat:
                active_category = cat
                qs = qs.filter(category=cat)

        if company_slug:
            comp = Company.objects.filter(slug=company_slug, is_active=True).first()
            if comp:
                active_company = comp
                qs = qs.filter(company=comp)

        if q:
            qs = qs.filter(name__icontains=q) | qs.filter(description__icontains=q)
            qs = qs.distinct()

        # Pagination
        from django.core.paginator import Paginator

        paginator = Paginator(qs, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        return render(
            request,
            self.template_name,
            {
                "services": page_obj,
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": paginator.num_pages > 1,
                "categories": ServiceCategory.objects.filter(is_active=True),
                "companies": Company.objects.filter(is_active=True),
                "active_category": active_category,
                "active_company": active_company,
                "q": q,
            },
        )


class ServiceDetailView(View):
    template_name = "services/service_detail.html"

    def get(self, request, slug):
        service = get_object_or_404(Service, slug=slug, is_active=True)
        related = Service.objects.filter(
            category=service.category, is_active=True
        ).exclude(pk=service.pk)[:4]
        return render(
            request,
            self.template_name,
            {
                "service": service,
                "related": related,
            },
        )
