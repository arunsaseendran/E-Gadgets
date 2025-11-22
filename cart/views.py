from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Cart, Product
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Create your views here.

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})


@login_required
@require_http_methods(["GET", "POST"])
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if product is in stock
    if product.stock <= 0:
        messages.error(request, f"'{product.name}' is currently out of stock.")
        if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Out of stock'}, status=400)
        return redirect(request.META.get('HTTP_REFERER', 'core:home'))
    
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        # Check if adding one more exceeds stock
        if cart_item.quantity >= product.stock:
            messages.warning(request, f"Cannot add more. Only {product.stock} units available.")
            if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Max quantity reached'}, status=400)
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Increased quantity of '{product.name}' in your cart.")
    else:
        messages.success(request, f"'{product.name}' added to your cart.")
    
    # Return JSON for AJAX requests
    if request.method == 'POST':
        cart_count = Cart.objects.filter(user=request.user).count()
        return JsonResponse({
            'added': True,
            'cart_count': cart_count,
            'message': f"'{product.name}' added to your cart."
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart.objects.filter(user=request.user, product=product).delete()
    messages.warning(request, f"'{product.name}' removed from your cart.")
    return redirect('cart:cart_view')


@login_required
def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(Cart, user=request.user, product_id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            # Check stock availability
            if quantity > cart_item.product.stock:
                messages.error(request, f"Only {cart_item.product.stock} units available for '{cart_item.product.name}'.")
                cart_item.quantity = cart_item.product.stock
                cart_item.save()
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
        else:
            cart_item.delete()
            messages.warning(request, "Item removed from cart.")
    
    return redirect('cart:cart_view')
