from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

class Category(models.Model):
    name = models.TextField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_photos/', blank=True, null=True)  # NEW
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Table(models.Model):
    table_number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)]  # Ensures table_number is greater than or equal to 1
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number}"

from decimal import Decimal
from django.db import models
from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
    )
    table = models.ForeignKey('Table', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Order #{self.id} - Table {self.table.table_number}"

    def get_total_amount(self):
        # Safe only after related OrderItems exist
        return sum(item.menu_item.price * item.quantity for item in self.items.all())

    def update_total(self):
        self.total_amount = self.get_total_amount()
        self.save(update_fields=['total_amount'])

    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"
