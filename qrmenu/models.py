from django.db import models

class Order(models.Model):
    # Example fields — adjust to what you expect
    table = models.CharField(max_length=10)
    items = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - Table {self.table}"

class Category(models.Model):
    name = models.TextField(max_length=100)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_photos/', blank=True, null=True)  # 👈 NEW
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # ✅ works now
    #category = models.TextField(max_length=30)

    def __str__(self):
        return self.name

class Table(models.Model):
    table_number = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.table_number}"


