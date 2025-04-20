from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # 👈 Root URL now shows login page
    path('dashboard/', views.main_dashboard, name='main_dashboard'),
    path('add-table/', views.add_table, name='add_table'),
    #path('item-management/', views.item_management, name='item_management'),
    path('item-management/', views.item_management_view, name='item_management'),  # Corrected the view name
    path('add-item/', views.add_item, name='add_item'),
    path('edit-item/<int:id>/', views.edit_item, name='edit_item'),
    path('delete-item/<int:id>/', views.delete_item, name='delete_item'),
    path('delete_table/<int:table_id>/', views.delete_table, name='delete_table'),
    path('add-category/', views.add_category, name='add_category'),
    path('ajax/add-category/', views.add_category_ajax, name='add_category_ajax'),
]

