
from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

# Define the namespace for this app, e.g., {% url 'core:home' %}
app_name = 'accounts'

urlpatterns = [
    
    
    # Resolves {% url 'accounts:profile' %}
    path('profile/', profile_settings, name='profile'),
    path('signup/', signup_view, name='signup'),
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('verify-password-otp/', verify_password_otp_view, name='verify_password_otp'),
    path('resend-password-otp/', resend_password_otp_view, name='resend_password_otp'),
    path('reset-password-confirm/', reset_password_confirm_view, name='reset_password_confirm'),
    path('reset/<uidb64>/<token>/', reset_password_view, name='reset_password'),
    path('products/', product_filter_view, name='product_filter'),
   # path('search/', search_products, name='search'),

    
]
