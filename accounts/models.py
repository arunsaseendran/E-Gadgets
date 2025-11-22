from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.text import slugify


# Create your models here.


# ===================================================================
# 🏷️ CATEGORY MODEL
# ===================================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    #slug = models.SlugField(unique=True, blank=True)  # 🆕 added

    def __str__(self):
        return self.name



# ===================================================================
# 📦 PRODUCT MODEL
# ===================================================================
class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product_images/')
    rating = models.FloatField(default=0.0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def final_price(self):
        return self.discount_price if self.discount_price else self.price
    
    def get_discount_percentage(self):
        if self.discount_price and self.price:
            from decimal import Decimal
            discount = ((self.price - self.discount_price) / self.price) * Decimal('100')
            return int(discount)
        return 0
    
    def get_savings(self):
        """Calculate savings amount"""
        if self.discount_price and self.price:
            return self.price - self.discount_price
        return 0


# ===================================================================
# 🖼️ PRODUCT IMAGE MODEL (Multiple Images per Product)
# ===================================================================
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)  # For ordering images
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"




# ===================================================================
# 👤 USER PROFILE MODEL
# ===================================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Enter a valid 10-digit mobile number.")
    phone = models.CharField(validators=[phone_validator], max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username



# ===================================================================
# 💖 WISHLIST MODEL
# ===================================================================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # prevents duplicates

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"



# ===================================================================
# 🛒 CART MODEL
# ===================================================================
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    def total_price(self):
        # Use discount price if available, else regular price
        price = self.product.discount_price if self.product.discount_price else self.product.price
        return price * self.quantity



# ===================================================================
# 📦 ORDER MODEL
# ===================================================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Order Placed', 'Order Placed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment (Razorpay)'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Order Placed')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')
    
    # Razorpay payment fields
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    # ------------------------------------------------------------------
    # 🧩 FUTURE PAYMENT LINK (add later)
    # Uncomment the next line once Payment model is added.
    # payment = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True)
    # ------------------------------------------------------------------

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def payment_status_display(self):
        """Return a readable payment status message."""
        if self.payment_method == 'COD':
            if self.status == 'Delivered':
                return "Paid on Delivery ✅"
            else:
                return "Pending (Cash on Delivery)"
        elif self.status == 'Pending':
            return "Awaiting Payment ⏳"
        else:
            return "Paid 💳"




# ===================================================================
# 📦 ORDER ITEM MODEL
# ===================================================================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_image = models.ImageField(upload_to='order_items/', null=True, blank=True)
    product_description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    def total_price(self):
        return self.price * self.quantity




# ===================================================================
# ⭐ REVIEW MODEL
# ===================================================================
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=1)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"




# ===================================================================
# 🤖 PURCHASE HISTORY MODEL
# ===================================================================
class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} bought {self.product.name}"




# ===================================================================
# ✉️ NOTIFICATION MODEL
# ===================================================================
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification to {self.user.username}"




# ===================================================================
# 📊 PRODUCT VIEW MODEL
# ===================================================================
class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} viewed"


# ===================================================================
# 🔥 SALE MODEL
# ===================================================================
class Sale(models.Model):
    title = models.CharField(max_length=200, default="Mega Sale!")
    description = models.TextField(blank=True, null=True)
    discount_percentage = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, related_name='sales')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



# ===================================================================
# 💳 FUTURE PAYMENT MODEL (COMMENTED OUT FOR LATER USE)
# ===================================================================

"""
class Payment(models.Model):
    # ---------------------------------------------------------------
    # 🔹 PAYMENT METHOD CHOICES
    # ---------------------------------------------------------------
    PAYMENT_METHODS = [
        ('COD', 'Cash on Delivery'),
        ('CARD', 'Credit / Debit Card'),
        ('UPI', 'UPI'),
        ('NETBANK', 'Net Banking'),
        ('WALLET', 'Wallet'),
    ]

    # ---------------------------------------------------------------
    # 🔹 PAYMENT STATUS CHOICES
    # ---------------------------------------------------------------
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),    # Payment created but not confirmed yet
        ('Success', 'Success'),    # Payment completed successfully
        ('Failed', 'Failed'),      # Payment failed or cancelled
    ]

    # ---------------------------------------------------------------
    # 🔹 MAIN FIELDS
    # ---------------------------------------------------------------
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who made the payment
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='payment')  # Which order this belongs to

    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount paid
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='COD')  # Type of payment
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')  # Payment result
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # Gateway reference (if online)
    timestamp = models.DateTimeField(auto_now_add=True)  # When payment happened

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"

    # Optional helper: user-friendly display text
    def payment_summary(self):
        return f"{self.get_method_display()} | {self.get_status_display()} | ₹{self.amount}"
"""

# ✅ You can uncomment this Payment model later when you integrate a real or simulated payment gateway.
# ✅ After uncommenting, run:
#       python manage.py makemigrations
#       python manage.py migrate
# ✅ It will not break any existing data or relationships.
