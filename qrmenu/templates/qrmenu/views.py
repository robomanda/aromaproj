from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Table, MenuItem, Order, OrderItem, Category
from .forms import MenuItemForm, TableForm, CategoryForm

# (your order model and form, etc.)

@login_required(login_url='/')
def main_dashboard(request):
    tables = Table.objects.all()
    return render(request, 'main.html', {'tables': tables})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('main_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')



def item_management_view(request):
    selected_category = request.GET.get('category')
    categories = Category.objects.all()
    
    if selected_category:
        menu_items = MenuItem.objects.filter(category_id=selected_category)
    else:
        menu_items = MenuItem.objects.all()
    
    return render(request, 'qrmenu/item_management.html', {
        'menu_items': menu_items,
        'categories': categories,
        'selected_category': selected_category,
    })



def add_item(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)  # <-- ADD request.FILES here
        #form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('item_management')
    else:
        form = MenuItemForm()
    return render(request, 'qrmenu/add_item.html', {'form': form})

def edit_item(request, id):
    item = get_object_or_404(MenuItem, id=id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        #form = MenuItemForm(request.POST, request.FILES)  # <-- ADD request.FILES here
        #form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('item_management')
    else:
        
        form = MenuItemForm(instance=item)
    return render(request, 'qrmenu/edit_item.html', {'form': form, 'item': item})

def delete_item(request, id):
    item = get_object_or_404(MenuItem, id=id)
    if request.method == 'POST':
        item.delete()
        return redirect('item_management')
    return render(request, 'qrmenu/confirm_delete.html', {'item': item})

@login_required(login_url='/')
def add_table(request):
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_dashboard')
    else:
        form = TableForm()
    return render(request, 'qrmenu/addtables.html', {'form': form})


def delete_table(request, table_id):
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        table.delete()
        messages.success(request, f"Table {table.table_number} deleted.")
    return redirect('main_dashboard')  # replace 'main' with your main page view name


@login_required(login_url='/')  # Ensure only logged-in users can access
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect('item_management')  # Redirect to item management after adding
    else:
        form = CategoryForm()

    return render(request, 'qrmenu/add_category.html', {'form': form})

def add_category_ajax(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            category, created = Category.objects.get_or_create(name=name)
            return JsonResponse({'success': True, 'id': category.id, 'name': category.name})
        return JsonResponse({'success': False, 'error': 'Name is required'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def menu_view(request, table_number):
    table = get_object_or_404(Table, table_number=table_number)
    categories = Category.objects.all()

    selected_category_id = request.GET.get('category')
    
    if selected_category_id:
        menu_items = MenuItem.objects.filter(category_id=selected_category_id)
    else:
        menu_items = None

    return render(request, 'qrmenu/mob_menu.html', {
        'table': table,
        'categories': categories,
        'menu_items': menu_items,
        'selected_category_id': selected_category_id,
    })


def submit_order(request, table_id):
    if request.method == "POST":
        table = get_object_or_404(Table, id=table_id)
        order = Order.objects.create(table=table)

        for key, value in request.POST.items():
            if key.startswith('item_') and value:
                try:
                    menu_item_id = int(key.split('_')[1])
                    quantity = int(value)

                    if quantity > 0:
                        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
                        notes = request.POST.get(f'note_{menu_item_id}', '')

                        OrderItem.objects.create(
                            order=order,
                            menu_item=menu_item,
                            quantity=quantity,
                            notes=notes
                        )
                except Exception as e:
                    print(f"Error processing item: {e}")
                    continue

        # ✅ Send WebSocket notification to "orders" group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "orders",
            {
                "type": "send_order_notification",
                "message": f"New order placed for Table {table.table_number}",
            }
        )

        messages.success(request, "Your order has been submitted!")
        return redirect('order_success')

    return redirect('menu_view', table_id=table_id)

def order_success(request):
    return render(request, 'qrmenu/order_success.html')




from django.shortcuts import render
from qrmenu.models import Order

def order_dashboard(request):
    # Fetch orders with status 'confirmed'
    orders = Order.objects.filter(status='confirmed')
    
    # Debugging print to ensure the orders are being fetched
    print(f"Orders: {orders}")
    
    return render(request, 'order_dashboard.html', {'orders': orders})




def view_table_orders(request, table_number):
    # Get the table object by table_number
    table = get_object_or_404(Table, table_number=table_number)
    orders = Order.objects.filter(table=table).order_by('timestamp')

    # Pre-calculate total price for each item
    for order in orders:
        for item in order.items.all():
            item.total_price = item.quantity * item.menu_item.price  # Add this line

    return render(request, 'qrmenu/view_orders.html', {'table': table, 'orders': orders})

def delete_order(request, order_id):
    # Get the order object by order_id and delete it
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('view_orders', table_number=order.table.table_number)  # Redirect back to the table's orders view

def confirm_order(request, order_id):
    # Get the order object by order_id and mark it as confirmed
    order = get_object_or_404(Order, id=order_id)
    order.status = 'Confirmed'  # Assuming you have a status field like 'Confirmed', 'Pending', etc.
    order.save()
    return redirect('view_orders', table_number=order.table.table_number)  # Redirect back to the table's orders view


