from django.urls import path
from . import views

app_name="orders"

urlpatterns=[
    #path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/history/', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),

    path('checkout/', views.checkout, name='checkout'),
    path('process_checkout/', views.process_checkout, name='process_checkout'),
    path('checkout-success/', views.checkout_success, name='checkout_success'),
    path('tracking/<int:order_id>/', views.order_tracking, name='order_tracking'),
    
    # Razorpay payment URLs
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('payment-failed/', views.razorpay_payment_failed, name='razorpay_payment_failed'),
]