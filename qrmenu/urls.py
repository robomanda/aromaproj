from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Root URL now shows login page
    path('dashboard/', views.main_dashboard, name='main_dashboard'),
    
    # Table management
    path('add-table/', views.add_table, name='add_table'),
    path('delete_table/<int:table_id>/', views.delete_table, name='delete_table'),

    # Item management
    path('item-management/', views.item_management_view, name='item_management'),
    path('add-item/', views.add_item, name='add_item'),
    path('edit-item/<int:id>/', views.edit_item, name='edit_item'),
    path('delete-item/<int:id>/', views.delete_item, name='delete_item'),

    # Category management
    path('add-category/', views.add_category, name='add_category'),
    path('ajax/add-category/', views.add_category_ajax, name='add_category_ajax'),

    # QR Menu and Orders
    path('mob_menu/<int:table_number>/', views.mob_menu, name='mob_menu'),
    path('submit_order/<int:table_number>/', views.submit_order, name='submit_order'),
    path('qrmenu/order_success/<int:table_number>/', views.order_success, name='order_success'),
    path('order_collection/<int:table_number>/', views.order_collection, name='order_collection'),  # This seems to refer to the customer's order management
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),

    # Admin side
    path('order_dashboard/', views.order_dashboard, name='order_dashboard'),
    path('remove_item/', views.remove_item, name='remove_item'),  # Looks like a helper for item removal, ensure it's needed

    # Order management (for admin side or orders overview)
    path('view_orders/<int:table_number>/', views.view_table_orders, name='view_orders'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('confirm_order/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('order/item/delete/<int:item_id>/', views.delete_order_item, name='delete_order_item'),
    path('order-management/', views.order_management, name='order_management'),
    

]
