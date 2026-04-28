"""
Contracts (abstract base classes) for engines and plugins.
Define the boundaries between core and strategies/extensions.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Dict


class PricingEngine(ABC):
    """
    Pricing strategy interface.
    Implementations: DefaultPricingEngine, B2BPricingEngine, VolumeBasedPricingEngine, etc.
    """

    @abstractmethod
    def calculate_line_price(
        self, variant, quantity: Decimal, customer=None
    ) -> Decimal:
        """
        Calculate the unit price after applying pricing logic.
        Args:
            variant: ProductVariant instance
            quantity: Quantity being purchased
            customer: Customer instance (may be None)
        Returns:
            Decimal: Unit price (in base currency units, e.g., euros)
        """
        pass

    @abstractmethod
    def calculate_total_price(self, cart) -> Dict[str, Decimal]:
        """
        Calculate total price for a cart.
        Returns dict with 'subtotal', 'discount', 'total' keys.
        """
        pass


class TaxEngine(ABC):
    """
    Tax calculation strategy interface.
    Implementations: SpanishTaxEngine, EUTaxEngine, B2BTaxEngine, etc.
    """

    @abstractmethod
    def calculate_tax(self, subtotal: Decimal, tax_rate) -> Decimal:
        """
        Calculate tax amount from subtotal.
        """
        pass

    @abstractmethod
    def get_applicable_rates(self, customer=None) -> list:
        """
        Get applicable tax rates for a customer or region.
        """
        pass


class CheckoutStrategy(ABC):
    """
    Checkout flow strategy interface.
    Implementations: StandardCheckout, SimplifiedCheckout, B2BCheckoutWithApproval, etc.
    """

    @abstractmethod
    def validate_cart(self, cart) -> tuple[bool, Optional[str]]:
        """
        Validate cart before proceeding to payment.
        Returns (is_valid, error_message)
        """
        pass

    @abstractmethod
    def process_checkout(
        self, cart, shipping_address, billing_address
    ) -> "Order":  # noqa: F821
        """
        Process the checkout and return an Order.
        """
        pass


class PaymentProvider(ABC):
    """
    Payment provider interface.
    Implementations: RedsysPaymentProvider, StripePaymentProvider, ManualPaymentProvider, etc.
    """

    @abstractmethod
    def charge(self, order, amount: Decimal) -> "PaymentTransaction":  # noqa: F821
        """
        Charge the customer for the order.
        Returns PaymentTransaction with status.
        """
        pass

    @abstractmethod
    def refund(self, payment_transaction, amount: Decimal = None) -> bool:
        """
        Refund a payment (fully or partially).
        """
        pass

    @abstractmethod
    def get_status(self, payment_transaction) -> str:
        """
        Get current status of a payment.
        """
        pass


class ShippingCalculator(ABC):
    """
    Shipping cost calculator interface.
    Implementations: FlatRateShipping, WeightBasedShipping, ZoneBasedShipping, etc.
    """

    @abstractmethod
    def calculate_cost(self, order, destination_address) -> Decimal:
        """
        Calculate shipping cost for an order.
        """
        pass

    @abstractmethod
    def get_available_methods(self, order, destination_address) -> list:
        """
        Get available shipping methods for an order.
        """
        pass


class InvoicingEngine(ABC):
    """
    Invoicing strategy interface.
    Handles invoice generation, numbering, rendering, and notification.
    """

    @abstractmethod
    def create_invoice(self, order) -> "Invoice":  # noqa: F821
        """
        Create an invoice from an order.
        """
        pass

    @abstractmethod
    def assign_number(self, invoice) -> str:
        """
        Assign invoice number according to series and rules.
        """
        pass

    @abstractmethod
    def render_pdf(self, invoice) -> bytes:
        """
        Render invoice as PDF bytes.
        """
        pass

    @abstractmethod
    def send_invoice(self, invoice, recipient_email: str) -> bool:
        """
        Send invoice to customer via email.
        """
        pass


class ErpConnector(ABC):
    """
    ERP integration interface.
    Implementations: HoledConnector, SapConnector, OdooConnector, etc.
    """

    @abstractmethod
    def sync_inventory(self) -> bool:
        """
        Sync inventory from ERP.
        """
        pass

    @abstractmethod
    def sync_order(self, order) -> bool:
        """
        Send order to ERP.
        """
        pass

    @abstractmethod
    def sync_invoice(self, invoice) -> bool:
        """
        Send invoice to ERP (accounting).
        """
        pass
