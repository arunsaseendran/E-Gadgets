from django.contrib import admin
from .models import *
# Register your models here.


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'discount_price', 'stock', 'rating', 'views', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['price', 'discount_price', 'stock']
    readonly_fields = ['views', 'rating', 'created_at', 'updated_at']
    inlines = [ProductImageInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'phone', 'city', 'state']
    search_fields = ['user__username', 'user__email', 'full_name', 'phone']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'order_date', 'total_amount', 'status', 'payment_method']
    list_filter = ['status', 'payment_method', 'order_date']
    search_fields = ['user__username', 'user__email']
    list_editable = ['status']
    date_hierarchy = 'order_date'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'total_price']
    search_fields = ['product_name', 'order__id']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'product__name', 'comment']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['title', 'discount_percentage', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    filter_horizontal = ['products']


admin.site.register(Wishlist)
admin.site.register(Cart)
admin.site.register(PurchaseHistory)
admin.site.register(Notification)
admin.site.register(ProductView)












