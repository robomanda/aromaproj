from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import Order, Table, MenuItem, Category, OrderItem
from .forms import MenuItemForm, TableForm, CategoryForm

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('main_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# Main dashboard
@login_required(login_url='/')
def main_dashboard(request):
    tables = Table.objects.all()
    return render(request, 'main.html', {'tables': tables})

# Item management
def item_management_view(request):
    selected_category = request.GET.get('category')
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(category_id=selected_category) if selected_category else MenuItem.objects.all()
    return render(request, 'qrmenu/item_management.html', {
        'menu_items': menu_items,
        'categories': categories,
        'selected_category': selected_category,
    })

def add_item(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
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

# Table management
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
    if request.method == 'POST':
        table = get_object_or_404(Table, id=table_id)
        table.delete()
        messages.success(request, f"Table {table.table_number} deleted.")
    return redirect('main_dashboard')

# Category management
@login_required(login_url='/')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect('item_management')
    else:
        form = CategoryForm()
    return render(request, 'qrmenu/add_category.html', {'form': form})

def add_category_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            category, _ = Category.objects.get_or_create(name=name)
            return JsonResponse({'success': True, 'id': category.id, 'name': category.name})
        return JsonResponse({'success': False, 'error': 'Name is required'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Mobile menu & order collection

def mob_menu(request, table_number):
    table = get_object_or_404(Table, table_number=table_number)
    selected_category_id = request.GET.get('category')
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(category_id=selected_category_id) if selected_category_id else MenuItem.objects.all()
    return render(request, 'qrmenu/mob_menu.html', {
        'table': table,
        'categories': categories,
        'menu_items': menu_items,
        'selected_category_id': selected_category_id,
    })

def submit_order(request, table_number):
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get(f'quantity_{item_id}', 1))
    item = get_object_or_404(MenuItem, id=item_id)

    order_items = request.session.get('order_items', [])
    order_items.append({
        'item_id': item.id,
        'name': item.name,
        'quantity': quantity,
        'price': float(item.price),
        'total_price': float(item.price * quantity),
    })
    request.session['order_items'] = order_items
    request.session.modified = True

    return redirect('order_collection', table_number=table_number)

def order_collection(request, table_number):
    table = get_object_or_404(Table, table_number=table_number)
    order_items = request.session.get('order_items', [])
    total_amount = sum(Decimal(item['total_price']) for item in order_items)
    return render(request, 'qrmenu/order_collection.html', {
        'table': table,
        'order_items': order_items,
        'total_amount': total_amount,
    })

# views.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def order_success(request, table_number):
    table = get_object_or_404(Table, table_number=table_number)
    order_items = request.session.get('order_items', [])

    if not order_items:
        return redirect('mob_menu', table_number=table_number)

    total_amount = sum(Decimal(item['total_price']) for item in order_items)
    order = Order.objects.create(table=table)

    for item in order_items:
        menu_item = get_object_or_404(MenuItem, id=item['item_id'])
        OrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=item['quantity']
        )

    # ✅ WebSocket notification
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "orders",
        {
            "type": "send_order_notification",
            "message": f"🔔 New order from Table {table.table_number}"
        }
    )

    # Clear session items
    del request.session['order_items']

    return render(request, 'qrmenu/order_success.html', {
        'table': table,
        'order': order,
    })


@csrf_exempt
def remove_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        order_items = request.session.get('order_items', [])
        order_items = [item for item in order_items if str(item['item_id']) != item_id]
        request.session['order_items'] = order_items
        request.session.modified = True
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


from django.utils import timezone
from django.shortcuts import render
from .models import Order

def order_dashboard(request):
    # Get today's date
    today = timezone.now().date()

    # Get the selected date from the query parameters, default to today
    selected_date = request.GET.get('date', today)

    # If the selected_date is a string, convert it to a date object
    if isinstance(selected_date, str):
        try:
            selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today  # If the date is invalid, use today's date

    # Filter orders by confirmed status and selected date
    confirmed_orders = Order.objects.filter(status='confirmed', timestamp__date=selected_date).order_by('-timestamp')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Optional: Return JSON data of confirmed orders
        confirmed_orders_data = list(confirmed_orders.values())
        return JsonResponse({'orders': confirmed_orders_data})

    return render(request, 'qrmenu/order_dashboard.html', {
        'orders': confirmed_orders,
        'selected_date': selected_date,
        'today': today,  # Pass today's date to limit the date selection to today's date
    })





from django.shortcuts import render, get_object_or_404
from .models import Table, Order

def view_table_orders(request, table_number):
    table = Table.objects.get(table_number=table_number)
    orders = Order.objects.filter(table=table, status='pending')  # Filter by table and 'Pending' only
    return render(request, 'qrmenu/view_orders.html', {'orders': orders, 'table': table})


def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('view_orders', table_number=order.table.table_number)  # Redirect back to the table's orders view


from django.shortcuts import render, get_object_or_404
from .models import Order

def order_details(request, order_id):
    # Fetch the order using the provided order_id
    order = get_object_or_404(Order, id=order_id)
    # Optionally, calculate any other details for the order if needed
    return render(request, 'qrmenu/order_details.html', {'order': order})
from django.shortcuts import render, get_object_or_404, redirect
from .models import Order

def confirm_order(request, order_id):
    # Fetch the order using the provided order_id
    order = get_object_or_404(Order, id=order_id)
    # Change the order status to 'Confirmed'
    order.status = 'confirmed'  # Assuming you have a status field like 'Confirmed', 'Pending', etc.
    order.save()
    # Redirect to a relevant page, e.g., order dashboard
    return redirect('view_orders', table_number=order.table.table_number)



def order_management(request):
    orders = Order.objects.exclude(status='confirmed')  # show only pending orders
    return render(request, 'view_orders.html', {'orders': orders})



def delete_order_item(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    table_number = request.GET.get('table_number')  # Get table number from query string
    item.delete()
    return redirect('view_orders', table_number=table_number)


