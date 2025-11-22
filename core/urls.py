from django.urls import path
from . import views
from . import admin_views

# Define the namespace for this app, e.g., {% url 'core:home' %}
app_name = 'core'

urlpatterns = [
    # path('', views.home, name='home'): This maps the empty path '' (i.e., the root of the app) 
    # to the 'home' view function.
    path('', views.home, name='home'),
    #path('<int:product_id>/', home, name='home'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    
    # Admin URLs
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin-orders/', admin_views.admin_orders, name='admin_orders'),
    path('admin-orders/update/<int:order_id>/', admin_views.update_order_status, name='update_order_status'),
    path('admin-users/', admin_views.admin_users, name='admin_users'),
    path('admin-products/', admin_views.admin_products, name='admin_products'),
    path('admin-products/add/', admin_views.add_product, name='add_product'),
    path('admin-products/edit/<int:product_id>/', admin_views.edit_product, name='edit_product'),
    path('admin-products/quick-update/<int:product_id>/', admin_views.quick_update_product, name='quick_update_product'),
    path('admin-products/delete/<int:product_id>/', admin_views.delete_product, name='delete_product'),
    path('admin-products/delete-image/<int:image_id>/', admin_views.delete_product_image, name='delete_product_image'),
]
