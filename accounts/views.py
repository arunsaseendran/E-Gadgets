from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.db.models import Q
from .models import *
from .forms import *


# Create your views here.

# Placeholder views for the 'accounts' app.

#def user_login(request):
#   """Placeholder for the user sign-in page."""
#    # In a real app, this would handle authentication logic
#    return render(request, 'accounts/login.html')

#def user_signup(request):
#    """Placeholder for the user sign-up page."""
#    # In a real app, this would handle user registration logic
#    return render(request, 'accounts/signup.html')

#def user_logout(request):
#    """Placeholder for the user logout logic."""
    # In a real app, this would log the user out and redirect to home
#    return render(request, 'accounts/logout.html')

#def user_profile(request):
#    """Placeholder for the user profile settings page."""
    # In a real app, this would show user details
#    return render(request, 'profile.html')


# ✅ SIGNUP VIEW WITH OTP VERIFICATION
from django.http import JsonResponse
import json
from .otp_utils import generate_otp, send_otp_email, store_otp, store_registration_data, send_password_reset_otp_email

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        if password1 != password2:
            return JsonResponse({'success': False, 'message': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists.'})
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists.'})

        # Generate and send OTP
        otp = generate_otp()
        
        # Store OTP and registration data temporarily
        store_otp(email, otp)
        store_registration_data(email, {
            'username': username,
            'email': email,
            'password': password1
        })
        
        # Send OTP email
        if send_otp_email(email, otp):
            return JsonResponse({
                'success': True, 
                'message': 'OTP sent to your email. Please verify to complete registration.'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Failed to send OTP. Please check your email configuration.'
            })

    return render(request, 'signup.html')


# ✅ VERIFY OTP VIEW
from .otp_utils import verify_otp, get_registration_data

def verify_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        
        if verify_otp(email, otp):
            # Get stored registration data
            reg_data = get_registration_data(email)
            
            if reg_data:
                # Create the user
                user = User.objects.create_user(
                    username=reg_data['username'],
                    email=reg_data['email'],
                    password=reg_data['password']
                )
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account created successfully! Please login.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Registration data expired. Please register again.'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired OTP. Please try again.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# ✅ RESEND OTP VIEW
def resend_otp_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            # Check if registration data exists
            reg_data = get_registration_data(email)
            if reg_data:
                # Re-store the registration data
                store_registration_data(email, reg_data)
            
            # Generate and send new OTP
            otp = generate_otp()
            store_otp(email, otp)
            
            if send_otp_email(email, otp):
                return JsonResponse({
                    'success': True,
                    'message': 'OTP resent successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send OTP.'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# ✅ LOGIN VIEW
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)  # check credentials

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            # Admins go to admin dashboard, customers to home
            if user.is_staff or user.is_superuser:
                return redirect('core:admin_dashboard')
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'login.html')
    return render(request, 'login.html')


# ✅ LOGOUT VIEW
def logout_view(request):
    # Clear all existing messages before logout
    storage = messages.get_messages(request)
    storage.used = True
    
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')

User = get_user_model()

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            # Generate and send OTP
            otp = generate_otp()
            store_otp(f'password_reset_{email}', otp)
            
            # Send OTP email for password reset
            if send_password_reset_otp_email(email, otp):
                return JsonResponse({
                    'success': True,
                    'message': 'OTP sent to your email.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send OTP. Please try again.'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No account found with that email address.'
            })

    return render(request, 'forgot_password.html')


# ✅ VERIFY PASSWORD RESET OTP
def verify_password_otp_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        
        if verify_otp(f'password_reset_{email}', otp):
            # Store verified email temporarily for password reset
            store_registration_data(f'verified_reset_{email}', {'email': email})
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired OTP.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# ✅ RESEND PASSWORD RESET OTP
def resend_password_otp_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            user = User.objects.filter(email=email).first()
            if user:
                otp = generate_otp()
                store_otp(f'password_reset_{email}', otp)
                
                if send_password_reset_otp_email(email, otp):
                    return JsonResponse({
                        'success': True,
                        'message': 'OTP resent successfully!'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to send OTP.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Email not found.'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


# ✅ RESET PASSWORD CONFIRM
def reset_password_confirm_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Check if OTP was verified
        verified_data = get_registration_data(f'verified_reset_{email}')
        
        if not verified_data:
            return JsonResponse({
                'success': False,
                'message': 'Session expired. Please start the password reset process again.'
            })
        
        if password1 != password2:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match.'
            })
        
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(password1)
            user.save()
            return JsonResponse({
                'success': True,
                'message': 'Password reset successful!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'User not found.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('password1')
            confirm_password = request.POST.get('password2')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successful! You can now log in.')
                return redirect('accounts:login')
            else:
                messages.error(request, 'Passwords do not match.')

        return render(request, 'password_reset_form.html')
    else:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('accounts:forgot_password')



def profile_settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('core:home')  # 👈 redirect to home
        else:
            messages.error(request, "Please enter a valid phone number")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})



def product_filter_view(request):
    query = request.GET.get('q', '').strip().lower()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()

    # 🔹 Synonyms mapping
    synonyms = {
        'mobile': 'smartphone',
        'mobiles': 'smartphone',
        'cell': 'smartphone',
        'cellphone': 'smartphone',
        'phone': 'smartphone',
        'android': 'smartphone',
        'iphone': 'smartphone',

        'lappy': 'laptop',
        'notebook': 'laptop',
        'macbook': 'laptop',
        'computer': 'laptop',
        'pc': 'laptop',
        'ultrabook': 'laptop',

        'earphone': 'audio',
        'earphones': 'audio',
        'headphone': 'audio',
        'headphones': 'audio',
        'speaker': 'audio',
        'speakers': 'audio',
        'soundbar': 'audio',
        'pods': 'audio',

        'watch': 'wearable',
        'smartwatch': 'wearable',
        'band': 'wearable',
        'fitband': 'wearable',

        'tab': 'tablet',
        'tablet': 'tablet',
        'ipad': 'tablet',
    }

    # Apply synonym mapping
    if query in synonyms:
        query = synonyms[query]

    # 🔹 Try filtering by name or category
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__name__icontains=query)
        )

    # 🔹 Fallback: If no match, try matching only by category name
    if not products.exists():
        products = Product.objects.filter(category__name__icontains=query)

    # 🔹 Price filter
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    context = {
        'products': products.distinct(),
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'search_results.html', context)



