from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Wishlist, Product, Review, PurchaseHistory, Cart, OrderItem
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Avg, Count, Q
from django.contrib import messages
from collections import Counter

# @login_required
# def toggle_wishlist(request):
#     product_id = request.GET.get('product_id')
#     product = Product.objects.get(id=product_id)
#     wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

#     if not created:
#         wishlist_item.delete()
#         return JsonResponse({'status': 'removed'})
#     else:
#         return JsonResponse({'status': 'added'})



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import *

@login_required
def wishlist_page(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.warning(request, f"'{product.name}' removed from your wishlist.")
    return redirect('products:wishlist_page')




# The view for the Homepage
# def sale_listing(request):
#     """
#     Renders the main product listing page.
#     In a real project, this is where you would fetch a list of featured 
#     products from the database and pass them to the template via the context.
#     """
#     # Example data (replace this with a database query later)
#     context = {
#         'featured_products': [
#             # Dummy data to demonstrate loop in template
#             {'id': 1, 'name': 'Pro 15 Max Smartphone', 'price': 999},
#             {'id': 2, 'name': 'EliteBook X1 Pro Laptop', 'price': 1499},
#             # etc.
#         ],
#         'is_mega_sale_active': True # Context for the banner
#     }
    
#     # Renders the 'product_listing_gem.html' template
#     return render(request, 'home.html', context)

# def product_detail(request, product_id):
#     product = Product.objects.get(id=product_id)
#     return render(request, 'product_detail.html', {'product': product})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    in_cart = Cart.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False
    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False
    
    # Get all product images
    product_images = product.images.all()
    
    # Get reviews and calculate average rating
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if user has purchased this product
    has_purchased = False
    user_review = None
    if request.user.is_authenticated:
        has_purchased = PurchaseHistory.objects.filter(user=request.user, product=product).exists()
        user_review = Review.objects.filter(user=request.user, product=product).first()
    
    # Update product rating
    product.rating = round(avg_rating, 1)
    product.save()
    
    # AI Recommendations: "Customers who bought this also purchased..."
    # Find products frequently bought together
    related_products = get_related_products(product)
    similar_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]

    return render(request, 'product_detail.html', {
        'product': product,
        'product_images': product_images,
        'in_cart': in_cart,
        'in_wishlist': in_wishlist,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'has_purchased': has_purchased,
        'user_review': user_review,
        'related_products': related_products,
        'similar_products': similar_products,
    })





@login_required
def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

    if not created:
        wishlist_item.delete()
        return JsonResponse({'removed': True})
    else:
        return JsonResponse({'added': True})



@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    cart_product_ids = Cart.objects.filter(user=request.user).values_list('product_id', flat=True)
    return render(request, 'wishlist.html', {
        'items': wishlist_items,
        'cart_product_ids': cart_product_ids,
    })


@login_required
def toggle_wishlist(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return JsonResponse({'added': False, 'message': 'Removed from wishlist!'})
        else:
            return JsonResponse({'added': True, 'message': 'Added to wishlist!'})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.info(request, f"{product.name} removed from your wishlist ❤️")
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def sale_products(request):
    products = Product.objects.filter(discount_price__isnull=False)
    return render(request, 'sale_page.html', {'products': products})


@login_required
def buy_now(request, product_id):
    # Prevent admin/staff from placing orders
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Admin and staff users cannot place orders. Please use a regular customer account.")
        return redirect('products:product_detail', product_id=product_id)
    
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is in stock
    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock!")
        return redirect('products:product_detail', product_id=product_id)
    
    # Add product to cart with quantity 1
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        # If already in cart, ensure quantity is at least 1
        if cart_item.quantity < 1:
            cart_item.quantity = 1
            cart_item.save()
    
    # Redirect to checkout page
    return redirect('orders:checkout')


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Check if user has purchased this product
    if not PurchaseHistory.objects.filter(user=request.user, product=product).exists():
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'You can only review products you\'ve purchased.'}, status=403)
        messages.error(request, "You can only review products you've purchased.")
        return redirect('products:product_detail', product_id=product_id)
    
    if request.method == 'POST':
        try:
            rating = int(request.POST.get('rating', 0))
            comment = request.POST.get('comment', '').strip()
            
            # Validate rating
            if rating < 1 or rating > 5:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Invalid rating. Please select 1-5 stars.'}, status=400)
                messages.error(request, "Invalid rating")
                return redirect('products:product_detail', product_id=product_id)
            
            # Validate comment
            if not comment:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'Please write a review.'}, status=400)
                messages.error(request, "Please write a review")
                return redirect('products:product_detail', product_id=product_id)
            
            # Update or create review
            review, created = Review.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={'rating': rating, 'comment': comment}
            )
            
            # Recalculate product average rating
            from django.db.models import Avg
            avg_rating = Review.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg'] or 0
            product.rating = round(avg_rating, 1)
            product.save()
            
            # Return JSON for AJAX requests
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you for your review!' if created else 'Your review has been updated!',
                    'rating': product.rating
                })
            
            if created:
                messages.success(request, "Thank you for your review!")
            else:
                messages.success(request, "Your review has been updated!")
            
            return redirect('products:product_detail', product_id=product_id)
        
        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('products:product_detail', product_id=product_id)
    
    return redirect('products:product_detail', product_id=product_id)


def get_related_products(product):
    """
    AI Recommendation: Find products frequently bought together with this product
    """
    # Get all orders containing this product
    orders_with_product = OrderItem.objects.filter(product=product).values_list('order_id', flat=True)
    
    # Get all other products in those orders
    related_items = OrderItem.objects.filter(
        order_id__in=orders_with_product
    ).exclude(product=product).values_list('product_id', flat=True)
    
    # Count frequency of each product
    product_counts = Counter(related_items)
    
    # Get top 4 most frequently bought together products
    top_product_ids = [pid for pid, count in product_counts.most_common(4)]
    
    # Fetch the actual products
    related_products = Product.objects.filter(id__in=top_product_ids, stock__gt=0)
    
    # If not enough related products, fill with same category products
    if related_products.count() < 4:
        additional = Product.objects.filter(
            category=product.category,
            stock__gt=0
        ).exclude(id=product.id).exclude(id__in=top_product_ids)[:4-related_products.count()]
        related_products = list(related_products) + list(additional)
    
    return related_products[:4]

