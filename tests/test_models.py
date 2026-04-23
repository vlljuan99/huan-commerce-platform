"""
Basic model tests using pytest-django.
"""

import pytest
from decimal import Decimal
from apps.accounts.models import User
from apps.customers.models import Customer, CustomerAddress
from apps.catalog.models import Product, ProductVariant, ProductCategory
from apps.orders.models import Order, OrderLineItem
from apps.cart.models import Cart, CartLineItem


@pytest.mark.django_db
class TestUserModel:
    """Test User model."""
    
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_customer()
    
    def test_user_is_admin(self):
        user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass',
            role='admin'
        )
        assert user.is_admin()
    
    def test_user_str(self):
        user = User.objects.create_user(
            username='john',
            email='john@example.com',
            first_name='John',
            last_name='Doe'
        )
        assert 'john@example.com' in str(user)


@pytest.mark.django_db
class TestCustomerModel:
    """Test Customer model."""
    
    def test_create_b2c_customer(self):
        user = User.objects.create_user(
            username='retail',
            email='retail@example.com'
        )
        customer = Customer.objects.create(
            user=user,
            segment='b2c'
        )
        assert customer.is_b2c()
        assert not customer.is_b2b()
    
    def test_create_b2b_customer(self):
        user = User.objects.create_user(
            username='business',
            email='business@example.com'
        )
        customer = Customer.objects.create(
            user=user,
            company_name='Acme Corp',
            tax_id='ES12345678A',
            segment='b2b'
        )
        assert customer.is_b2b()
        assert 'Acme Corp' in str(customer)
    
    def test_customer_address(self):
        user = User.objects.create_user(
            username='customer',
            email='customer@example.com'
        )
        customer = Customer.objects.create(user=user)
        address = CustomerAddress.objects.create(
            customer=customer,
            name='Office',
            street_address='123 Main St',
            city='Madrid',
            postal_code='28001',
            country='Spain',
            is_default=True
        )
        assert address.is_default
        assert '123 Main St' in address.full_address()


@pytest.mark.django_db
class TestCatalogModels:
    """Test catalog models."""
    
    def test_create_product_category(self):
        category = ProductCategory.objects.create(
            name='Tiles',
            description='Ceramic tiles'
        )
        assert category.slug == 'tiles'
        assert category.is_active
    
    def test_create_product_with_variants(self):
        category = ProductCategory.objects.create(name='Tiles')
        product = Product.objects.create(
            name='Ceramic Tile 30x30',
            category=category,
            sku_base='TILE-001',
            description='Beautiful ceramic tile'
        )
        variant1 = ProductVariant.objects.create(
            product=product,
            sku='TILE-001-RED',
            name='Red',
            price_no_tax=Decimal('25.00'),
            stock_quantity=100
        )
        variant2 = ProductVariant.objects.create(
            product=product,
            sku='TILE-001-BLUE',
            name='Blue',
            price_no_tax=Decimal('25.00'),
            stock_quantity=50
        )
        
        assert product.variants.count() == 2
        assert variant1.is_in_stock()
        assert variant2.is_in_stock()
    
    def test_product_variant_stock_reduction(self):
        category = ProductCategory.objects.create(name='Tiles')
        product = Product.objects.create(
            name='Tile',
            category=category,
            sku_base='TILE-001'
        )
        variant = ProductVariant.objects.create(
            product=product,
            sku='TILE-001-RED',
            name='Red',
            price_no_tax=Decimal('25.00'),
            stock_quantity=10
        )
        
        variant.reduce_stock(3)
        assert variant.stock_quantity == 7


@pytest.mark.django_db
class TestOrderModel:
    """Test Order model."""
    
    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com'
        )
        self.customer = Customer.objects.create(user=self.user)
    
    def test_create_order(self):
        order = Order.objects.create(
            order_number='ORD-001',
            customer=self.customer,
            subtotal=Decimal('100.00'),
            tax_amount=Decimal('21.00'),
            total=Decimal('121.00')
        )
        assert order.status == 'draft'
        assert str(order) == 'Order ORD-001'
    
    def test_order_status_change(self):
        order = Order.objects.create(
            order_number='ORD-002',
            customer=self.customer
        )
        order.status = 'confirmed'
        order.save()
        
        order.refresh_from_db()
        assert order.status == 'confirmed'


@pytest.mark.django_db
class TestCartModel:
    """Test Cart model."""
    
    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='shopper',
            email='shopper@example.com'
        )
        self.category = ProductCategory.objects.create(name='Tiles')
        self.product = Product.objects.create(
            name='Tile',
            category=self.category,
            sku_base='TILE-001'
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TILE-001',
            name='Default',
            price_no_tax=Decimal('10.00')
        )
    
    def test_create_cart(self):
        cart = Cart.objects.create(user=self.user)
        assert cart.user == self.user
    
    def test_add_to_cart(self):
        cart = Cart.objects.create(user=self.user)
        item = CartLineItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=5
        )
        assert item.quantity == 5
        assert cart.items.count() == 1
    
    def test_cart_total(self):
        cart = Cart.objects.create(user=self.user)
        CartLineItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=10
        )
        total = cart.get_total()
        assert total == Decimal('100.00')  # 10 * 10.00
