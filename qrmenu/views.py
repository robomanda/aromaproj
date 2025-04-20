from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, Table, MenuItem, Category
from django.shortcuts import render, get_object_or_404, redirect
from .forms import MenuItemForm, TableForm, CategoryForm
from django.contrib import messages
from django.http import JsonResponse

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


def place_order(request):
    if request.method == 'POST':
        table_id = request.POST.get('table')  # or get it from QR URL
        items = request.POST.getlist('items')  # however you're posting items

        # Save the order in your DB
        Order.objects.create(table=table_id, items=items)

        # 🔔 NOW TRIGGER THE WEBSOCKET ALERT HERE:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "orders",
            {
                "type": "send_order_alert",
                "table": table_id
            }
        )

        return redirect('order_success')  # or render confirmation

    return render(request, 'menu.html')


from .models import MenuItem, Category

from django.shortcuts import render


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



from django.contrib.auth.decorators import login_required

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
