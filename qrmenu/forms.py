from django import forms
from .models import MenuItem, Table, Category

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'available', 'image', 'category']


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['table_number', 'is_active']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

