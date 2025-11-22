from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from accounts.models import *
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.contrib import messages
import json


@staff_member_required
def admin_orders(request):
    """
    Admin Orders Management Page
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    orders = Order.objects.all().select_related('user').prefetch_related('items')
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Order by most recent
    orders = orders.order_by('-order_date')
    
    # Calculate statistics
    total_orders = orders.count()
    total_revenue = orders.exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    pending_orders = orders.filter(status='Pending').count()
    delivered_orders = orders.filter(status='Delivered').count()
    
    # Get all statuses for filter dropdown
    all_statuses = Order.objects.values_list('status', flat=True).distinct()
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'all_statuses': all_statuses,
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'admin_orders.html', context)


@staff_member_required
def admin_dashboard(request):
    """
    Admin Dashboard with Analytics
    """
    # Total counts
    total_users = User.objects.count()
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_revenue = Order.objects.exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-order_date')[:10]
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    
    # Sales by category
    sales_by_category = OrderItem.objects.values('product__category__name').annotate(
        total_sales=Sum('price'),
        total_quantity=Sum('quantity')
    ).order_by('-total_sales')
    
    # Most viewed products
    most_viewed = Product.objects.order_by('-views')[:5]
    
    # Best selling products
    best_selling = Product.objects.annotate(
        total_sold=Count('orderitem')
    ).order_by('-total_sold')[:5]
    
    # Monthly revenue (last 6 months)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_revenue = Order.objects.filter(
        order_date__gte=six_months_ago
    ).exclude(status='Cancelled').annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        revenue=Sum('total_amount')
    ).order_by('month')
    
    # Low stock products (stock < 10)
    low_stock_products = Product.objects.filter(stock__lt=10).order_by('stock')
    
    # Recent reviews
    recent_reviews = Review.objects.all().order_by('-created_at')[:5]
    
    # Prepare chart data
    status_labels = [item['status'] for item in orders_by_status]
    status_data = [item['count'] for item in orders_by_status]
    
    category_labels = [item['product__category__name'] or 'Uncategorized' for item in sales_by_category]
    category_data = [float(item['total_sales']) for item in sales_by_category]
    
    month_labels = [item['month'].strftime('%B %Y') for item in monthly_revenue]
    month_data = [float(item['revenue']) for item in monthly_revenue]
    
    context = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'orders_by_status': orders_by_status,
        'sales_by_category': sales_by_category,
        'most_viewed': most_viewed,
        'best_selling': best_selling,
        'low_stock_products': low_stock_products,
        'recent_reviews': recent_reviews,
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'month_labels': json.dumps(month_labels),
        'month_data': json.dumps(month_data),
    }
    
    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def update_order_status(request, order_id):
    """Update order status from admin panel"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order_id} status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect('core:admin_orders')


@staff_member_required
def admin_users(request):
    """View all users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Add order count for each user
    active_customers = 0
    for user in users:
        user.order_count = Order.objects.filter(user=user).count()
        user.total_spent = Order.objects.filter(user=user).exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        if user.order_count > 0:
            active_customers += 1
    
    # Count staff members
    staff_count = User.objects.filter(is_staff=True).count()
    
    context = {
        'users': users,
        'active_customers': active_customers,
        'staff_count': staff_count,
    }
    return render(request, 'admin_users.html', context)


@staff_member_required
def admin_products(request):
    """Manage Products - View, Edit, Delete"""
    # Get filter parameters
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    stock_filter = request.GET.get('stock', '')
    
    # Base queryset
    products = Product.objects.all().select_related('category')
    
    # Apply filters
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if stock_filter == 'low':
        products = products.filter(stock__lt=10)
    elif stock_filter == 'out':
        products = products.filter(stock=0)
    
    # Order by most recent
    products = products.order_by('-created_at')
    
    # Get all categories for filter
    categories = Category.objects.all()
    
    # Statistics
    total_products = products.count()
    low_stock_count = Product.objects.filter(stock__lt=10).count()
    out_of_stock_count = Product.objects.filter(stock=0).count()
    
    context = {
        'products': products,
        'categories': categories,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'current_category': category_filter,
        'search_query': search_query,
        'stock_filter': stock_filter,
    }
    
    return render(request, 'admin_products.html', context)


@staff_member_required
def delete_product(request, product_id):
    """Delete a product"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
    
    return redirect('core:admin_products')


@staff_member_required
def edit_product(request, product_id):
    """Edit product with custom interface"""
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    product_images = product.images.all()
    
    if request.method == 'POST':
        # Update product details
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.stock = request.POST.get('stock')
        product.category_id = request.POST.get('category')
        
        # Handle main image upload
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        product.save()
        
        # Handle multiple images
        if request.FILES.getlist('additional_images'):
            for img_file in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(
                    product=product,
                    image=img_file,
                    alt_text=request.POST.get('alt_text', product.name)
                )
        
        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('core:admin_products')
    
    context = {
        'product': product,
        'categories': categories,
        'product_images': product_images,
    }
    
    return render(request, 'edit_product.html', context)


@staff_member_required
def delete_product_image(request, image_id):
    """Delete a product image"""
    if request.method == 'POST':
        image = get_object_or_404(ProductImage, id=image_id)
        product_id = image.product.id
        image.delete()
        messages.success(request, "Image deleted successfully!")
        return redirect('core:edit_product', product_id=product_id)
    
    return redirect('core:admin_products')


@staff_member_required
def quick_update_product(request, product_id):
    """Quick update product stock and discount price"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            
            # Update stock
            stock = int(request.POST.get('stock', 0))
            product.stock = stock
            
            # Update discount price
            discount_price = request.POST.get('discount_price', '').strip()
            if discount_price:
                discount_price = float(discount_price)
                if discount_price >= product.price:
                    return JsonResponse({'success': False, 'error': 'Discount price must be less than regular price'}, status=400)
                product.discount_price = discount_price
            else:
                product.discount_price = None
            
            product.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Product updated successfully!',
                'stock': product.stock,
                'discount_price': product.discount_price
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@staff_member_required
def add_product(request):
    """Add new product with custom interface"""
    categories = Category.objects.all()
    
    if request.method == 'POST':
        # Create new product
        product = Product()
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.stock = request.POST.get('stock')
        product.category_id = request.POST.get('category')
        
        # Handle main image upload
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        
        product.save()
        
        # Handle multiple images
        if request.FILES.getlist('additional_images'):
            for img_file in request.FILES.getlist('additional_images'):
                ProductImage.objects.create(
                    product=product,
                    image=img_file,
                    alt_text=request.POST.get('alt_text', product.name)
                )
        
        messages.success(request, f"Product '{product.name}' added successfully!")
        return redirect('core:admin_products')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'add_product.html', context)
