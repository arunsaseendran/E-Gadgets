from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import *
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import razorpay
import hmac
import hashlib

# Create your views here.


@login_required
def checkout(request):
    # Prevent admin/staff from placing orders
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "Admin and staff users cannot place orders. Please use a regular customer account.")
        return redirect('core:home')
    
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    cart_items = Cart.objects.filter(user=request.user)
    
    # Check if cart is empty
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty!")
        return redirect('core:home')

    if request.method == 'POST':
        # Save or update the user's address details
        profile.full_name = request.POST.get('full_name')
        profile.phone = request.POST.get('phone')
        profile.address = request.POST.get('address')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.postal_code = request.POST.get('postal_code')
        profile.country = request.POST.get('country', 'India')
        profile.save()
        
        # Check stock availability
        insufficient_stock = []
        for item in cart_items:
            if item.product.stock < item.quantity:
                insufficient_stock.append(f"{item.product.name} (Available: {item.product.stock})")
        
        if insufficient_stock:
            messages.error(request, f"Insufficient stock for: {', '.join(insufficient_stock)}")
            return redirect('cart:cart_view')

        # Calculate total with discount prices
        total = sum(item.total_price() for item in cart_items)
        tax = round(total * Decimal('0.18'), 2)  # 18% GST
        grand_total = round(total + tax, 2)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=grand_total,
            payment_method=request.POST.get('payment_method', 'COD')
        )

        # Create OrderItems and update stock & purchase history
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_image=item.product.image,
                product_description=item.product.description,
                quantity=item.quantity,
                price=item.product.final_price()  # Use discount price if available
            )
            
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()
            
            # Add to purchase history
            PurchaseHistory.objects.create(
                user=request.user,
                product=item.product
            )

        # Clear the cart
        cart_items.delete()
        
        # Send order confirmation email
        send_order_confirmation_email(order)

        return redirect('orders:order_success', order_id=order.id)

    # Calculate totals for GET request
    total = sum(item.total_price() for item in cart_items)
    tax = round(total * Decimal('0.18'), 2)  # 18% GST
    grand_total = round(total + tax, 2)
    
    context = {
        'profile': profile,
        'cart_items': cart_items,
        'total': total,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'checkout.html', context)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    
    # Add user review status for each order item
    for order in orders:
        for item in order.items.all():
            if item.product:
                # Check if user has reviewed this product
                item.user_review = Review.objects.filter(user=request.user, product=item.product).first()
    
    return render(request, 'order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    # Staff/superusers can view any order; regular users only their own
    if request.user.is_staff or request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    # Fetch all items in this order
    items = OrderItem.objects.filter(order=order)

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'order_detail.html', context)

###################################################

def process_checkout(request):
    if request.method == 'POST':
        # You can process payment logic here (dummy for now)
        messages.success(request, "Payment successful! Thank you for shopping with E-Gadgets.")
        return redirect('orders:checkout_success')  # Redirect to success page
    return redirect('checkout')

def checkout_success(request):
    return render(request, 'checkout_success.html')


@login_required
def order_tracking(request, order_id):
    """View for tracking order status"""
    if request.user.is_staff or request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)
    items = OrderItem.objects.filter(order=order)
    
    # Define status progression
    status_steps = [
        'Pending',
        'Order Placed',
        'Processing',
        'Shipped',
        'Out for Delivery',
        'Delivered',
    ]
    
    # Get current status index
    try:
        current_index = status_steps.index(order.status)
    except ValueError:
        current_index = 0
    
    context = {
        'order': order,
        'items': items,
        'status_steps': status_steps,
        'current_index': current_index,
    }
    return render(request, 'order_tracking.html', context)


def send_order_confirmation_email(order):
    """Send order confirmation email to user"""
    subject = f"Order Confirmation - Order #{order.id}"
    message = f"""
    Dear {order.user.username},
    
    Thank you for your order!
    
    Order ID: #{order.id}
    Order Date: {order.order_date.strftime('%B %d, %Y')}
    Total Amount: ₹{order.total_amount}
    Payment Method: {order.get_payment_method_display()}
    Status: {order.status}
    
    You can track your order at: http://localhost:8000/orders/tracking/{order.id}/
    
    Thank you for shopping with E-Gadgets!
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_order_status_email(order, old_status, new_status):
    """Send email when order status changes"""
    subject = f"Order Status Update - Order #{order.id}"
    
    status_messages = {
        'Processing': 'Your order is being processed.',
        'Shipped': 'Your order has been shipped!',
        'Out for Delivery': 'Your order is out for delivery.',
        'Delivered': 'Your order has been delivered. Thank you for shopping with us!',
        'Cancelled': 'Your order has been cancelled.',
    }
    
    message = f"""
    Dear {order.user.username},
    
    Your order status has been updated.
    
    Order ID: #{order.id}
    Previous Status: {old_status}
    New Status: {new_status}
    
    {status_messages.get(new_status, '')}
    
    Track your order: http://localhost:8000/orders/tracking/{order.id}/
    
    Thank you for shopping with E-Gadgets!
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


# ===================================================================
# RAZORPAY PAYMENT INTEGRATION
# ===================================================================

@login_required
def create_razorpay_order(request):
    """Create Razorpay order and return order details"""
    # Prevent admin/staff from placing orders
    if request.user.is_staff or request.user.is_superuser:
        return JsonResponse({'error': 'Admin and staff users cannot place orders'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Get cart items
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Calculate total
        total = sum(item.total_price() for item in cart_items)
        tax = round(total * Decimal('0.18'), 2)
        grand_total = round(total + tax, 2)
        
        # Convert to paise (Razorpay uses smallest currency unit)
        amount_in_paise = int(grand_total * 100)
        
        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create Razorpay order
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1  # Auto capture payment
        })
        
        # Store order details in session for later use
        request.session['razorpay_order_id'] = razorpay_order['id']
        request.session['order_amount'] = str(grand_total)
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'name': 'E-Gadgets',
            'description': 'Order Payment',
            'prefill': {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def verify_razorpay_payment(request):
    """Verify Razorpay payment signature and create order"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        # Get payment details from request
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        # Get user profile and cart
        profile = UserProfile.objects.get(user=request.user)
        cart_items = Cart.objects.filter(user=request.user)
        
        if not cart_items.exists():
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Verify signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
            payment_verified = True
        except razorpay.errors.SignatureVerificationError:
            payment_verified = False
            return JsonResponse({'error': 'Payment verification failed'}, status=400)
        
        if payment_verified:
            # Check stock availability
            insufficient_stock = []
            for item in cart_items:
                if item.product.stock < item.quantity:
                    insufficient_stock.append(f"{item.product.name} (Available: {item.product.stock})")
            
            if insufficient_stock:
                return JsonResponse({
                    'error': f"Insufficient stock for: {', '.join(insufficient_stock)}"
                }, status=400)
            
            # Calculate total
            total = sum(item.total_price() for item in cart_items)
            tax = round(total * Decimal('0.18'), 2)
            grand_total = round(total + tax, 2)
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                total_amount=grand_total,
                payment_method='ONLINE',
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_signature=razorpay_signature,
                payment_status='SUCCESS',
                status='Order Placed'
            )
            
            # Create OrderItems and update stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_image=item.product.image,
                    product_description=item.product.description,
                    quantity=item.quantity,
                    price=item.product.final_price()
                )
                
                # Reduce stock
                item.product.stock -= item.quantity
                item.product.save()
                
                # Add to purchase history
                PurchaseHistory.objects.create(
                    user=request.user,
                    product=item.product
                )
            
            # Clear cart
            cart_items.delete()
            
            # Send order confirmation email
            send_order_confirmation_email(order)
            
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'message': 'Payment successful!'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_exempt
def razorpay_payment_failed(request):
    """Handle failed Razorpay payment"""
    if request.method == 'POST':
        razorpay_order_id = request.POST.get('razorpay_order_id')
        error_description = request.POST.get('error_description', 'Payment failed')
        
        messages.error(request, f'Payment failed: {error_description}')
        
        return JsonResponse({
            'success': False,
            'message': error_description
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)