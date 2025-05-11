
from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem, Table

admin.site.register(Category)
admin.site.register(Table)
admin.site.register(MenuItem)
admin.site.register(Order)
admin.site.register(OrderItem)




# Register your models here.
