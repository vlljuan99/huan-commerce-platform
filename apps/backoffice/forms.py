import secrets

from django import forms
from django.contrib.auth.hashers import make_password

from apps.accounts.models import User
from apps.catalog.models import Product, ProductVariant
from apps.customers.models import Customer, CustomerAddress
from apps.invoicing.models import Invoice, InvoiceSeries
from apps.orders.models import Order

_C = {"class": "bo-form__control"}
_C_MONO = {"class": "bo-form__control bo-form__control--mono"}
_TA = {"class": "bo-form__control", "rows": "4"}
_TA3 = {"class": "bo-form__control", "rows": "3"}


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "notes"]
        widgets = {
            "status": forms.Select(attrs=_C),
            "notes": forms.Textarea(attrs=_TA),
        }
        labels = {
            "status": "Estado",
            "notes": "Notas internas",
        }


# ── Customers ─────────────────────────────────────────────────────────────────

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "segment", "company_name", "fiscal_name", "tax_id",
            "phone", "contact_email", "notes",
        ]
        widgets = {
            "segment":       forms.Select(attrs=_C),
            "company_name":  forms.TextInput(attrs=_C),
            "fiscal_name":   forms.TextInput(attrs=_C),
            "tax_id":        forms.TextInput(attrs=_C),
            "phone":         forms.TextInput(attrs={**_C, "type": "tel", "autocomplete": "tel"}),
            "contact_email": forms.EmailInput(attrs={**_C, "autocomplete": "email"}),
            "notes":         forms.Textarea(attrs=_TA3),
        }
        labels = {
            "segment":       "Segmento",
            "company_name":  "Empresa (nombre comercial)",
            "fiscal_name":   "Razón social (para facturas)",
            "tax_id":        "NIF / CIF",
            "phone":         "Teléfono",
            "contact_email": "Email de contacto (facturas)",
            "notes":         "Notas internas",
        }


class CustomerCreateForm(forms.Form):
    """Creates a User + Customer together from the backoffice."""

    first_name = forms.CharField(
        max_length=150, label="Nombre",
        widget=forms.TextInput(attrs={**_C, "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=150, label="Apellidos", required=False,
        widget=forms.TextInput(attrs={**_C, "autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        label="Email (acceso)",
        widget=forms.EmailInput(attrs={**_C, "autocomplete": "email"}),
    )

    segment = forms.ChoiceField(
        choices=Customer.SEGMENT_CHOICES, label="Segmento",
        widget=forms.Select(attrs=_C),
    )
    company_name  = forms.CharField(max_length=255, label="Empresa", required=False, widget=forms.TextInput(attrs=_C))
    fiscal_name   = forms.CharField(max_length=255, label="Razón social", required=False, widget=forms.TextInput(attrs=_C))
    tax_id        = forms.CharField(max_length=50,  label="NIF / CIF", required=False, widget=forms.TextInput(attrs=_C))
    phone         = forms.CharField(max_length=20,  label="Teléfono", required=False, widget=forms.TextInput(attrs={**_C, "type": "tel"}))
    contact_email = forms.EmailField(label="Email de contacto (facturas)", required=False, widget=forms.EmailInput(attrs=_C))
    notes         = forms.CharField(label="Notas internas", required=False, widget=forms.Textarea(attrs=_TA3))

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email

    def save(self):
        d = self.cleaned_data
        user = User.objects.create(
            first_name=d["first_name"],
            last_name=d.get("last_name", ""),
            email=d["email"],
            username=d["email"],
            role="customer",
            password=make_password(secrets.token_urlsafe(16)),
        )
        return Customer.objects.create(
            user=user,
            segment=d["segment"],
            company_name=d.get("company_name", ""),
            fiscal_name=d.get("fiscal_name", ""),
            tax_id=d.get("tax_id") or None,
            phone=d.get("phone", ""),
            contact_email=d.get("contact_email", ""),
            notes=d.get("notes", ""),
        )


class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = [
            "name", "address_type", "street_address",
            "city", "postal_code", "region", "country", "is_default",
        ]
        widgets = {
            "name":           forms.TextInput(attrs=_C),
            "address_type":   forms.Select(attrs=_C),
            "street_address": forms.TextInput(attrs={**_C, "autocomplete": "street-address"}),
            "city":           forms.TextInput(attrs={**_C, "autocomplete": "address-level2"}),
            "postal_code":    forms.TextInput(attrs={**_C, "autocomplete": "postal-code", "inputmode": "numeric"}),
            "region":         forms.TextInput(attrs=_C),
            "country":        forms.TextInput(attrs={**_C, "autocomplete": "country-name"}),
        }
        labels = {
            "name":           "Nombre de la dirección",
            "address_type":   "Tipo",
            "street_address": "Dirección",
            "city":           "Ciudad",
            "postal_code":    "Código postal",
            "region":         "Provincia / Región",
            "country":        "País",
            "is_default":     "Dirección por defecto",
        }


# ── Catalog ───────────────────────────────────────────────────────────────────

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name", "description", "category", "brand",
            "sku_base", "unit_of_measure", "weight",
            "is_featured", "is_active",
            "seo_title", "seo_description",
        ]
        widgets = {
            "name":            forms.TextInput(attrs=_C),
            "description":     forms.Textarea(attrs=_TA),
            "category":        forms.Select(attrs=_C),
            "brand":           forms.Select(attrs=_C),
            "sku_base":        forms.TextInput(attrs=_C_MONO),
            "unit_of_measure": forms.TextInput(attrs=_C),
            "weight":          forms.NumberInput(attrs={**_C, "step": "0.01", "inputmode": "decimal"}),
            "seo_title":       forms.TextInput(attrs=_C),
            "seo_description": forms.TextInput(attrs=_C),
        }
        labels = {
            "name":            "Nombre del producto",
            "description":     "Descripción",
            "category":        "Categoría",
            "brand":           "Marca",
            "sku_base":        "SKU base",
            "unit_of_measure": "Unidad de medida (unit, m2, caja…)",
            "weight":          "Peso (kg)",
            "is_featured":     "Producto destacado",
            "is_active":       "Activo (visible en catálogo)",
            "seo_title":       "Título SEO",
            "seo_description": "Meta descripción SEO",
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["sku", "name", "price_no_tax", "stock_quantity", "is_active"]
        widgets = {
            "sku":            forms.TextInput(attrs=_C_MONO),
            "name":           forms.TextInput(attrs=_C),
            "price_no_tax":   forms.NumberInput(attrs={**_C, "step": "0.01", "inputmode": "decimal"}),
            "stock_quantity": forms.NumberInput(attrs={**_C, "inputmode": "numeric"}),
        }
        labels = {
            "sku":            "SKU",
            "name":           "Nombre de la variante (color, talla…)",
            "price_no_tax":   "Precio sin IVA (€)",
            "stock_quantity": "Stock (-1 = ilimitado)",
            "is_active":      "Activa",
        }


# ── Invoices ──────────────────────────────────────────────────────────────────

class InvoiceStatusForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["status", "due_date", "notes"]
        widgets = {
            "status":   forms.Select(attrs=_C),
            "due_date": forms.DateInput(attrs={**_C, "type": "date"}),
            "notes":    forms.Textarea(attrs=_TA3),
        }
        labels = {
            "status":   "Estado",
            "due_date": "Fecha de vencimiento",
            "notes":    "Notas",
        }


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["customer", "order", "series", "issued_at", "due_date", "notes"]
        widgets = {
            "customer":  forms.Select(attrs=_C),
            "order":     forms.Select(attrs=_C),
            "series":    forms.Select(attrs=_C),
            "issued_at": forms.DateInput(attrs={**_C, "type": "date"}),
            "due_date":  forms.DateInput(attrs={**_C, "type": "date"}),
            "notes":     forms.Textarea(attrs=_TA3),
        }
        labels = {
            "customer":  "Cliente",
            "order":     "Pedido relacionado (opcional)",
            "series":    "Serie de facturación",
            "issued_at": "Fecha de emisión",
            "due_date":  "Fecha de vencimiento",
            "notes":     "Notas",
        }


# ── Orders create ─────────────────────────────────────────────────────────────

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["customer", "notes"]
        widgets = {
            "customer": forms.Select(attrs=_C),
            "notes":    forms.Textarea(attrs=_TA),
        }
        labels = {
            "customer": "Cliente",
            "notes":    "Notas / descripción del pedido",
        }
