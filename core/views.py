from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from accounts.models import *
from django.db.models import Q

# Create your views here.

def home(request):
    categories = Category.objects.all()
    products = Product.objects.filter(stock__gt=0)  # Only show in-stock products
    user_wishlist = []
    cart_count = 0
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'newest')  # Default sort
    
    # Apply category filter
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    # Apply price range filter
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Apply search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-rating')
    elif sort_by == 'popular':
        products = products.order_by('-views')
    else:  # newest
        products = products.order_by('-created_at')

    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        cart_count = Cart.objects.filter(user=request.user).count()
    
    # Add review count to each product
    for product in products:
        product.review_count = Review.objects.filter(product=product).count()

    return render(request, 'home.html', {
        'products': products,
        'user_wishlist': user_wishlist,
        'cart_count': cart_count,
        'categories': categories,
        'selected_category': category_filter,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search_query,
        'sort_by': sort_by,
    })



def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    
    # Add review count to each product
    for product in products:
        product.review_count = Review.objects.filter(product=product).count()
    
    return render(request, 'category_products.html', {'category': category, 'products': products})


