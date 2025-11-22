from django.urls import path
from . import views

# Define the namespace for this app, e.g., {% url 'core:home' %}
app_name = 'products'

urlpatterns = [
    
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),

    path('<int:product_id>/', views.product_detail, name='product_detail'),
    
  

    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('sale/', views.sale_products, name='sale_products'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('review/<int:product_id>/', views.add_review, name='add_review'),

    
]
