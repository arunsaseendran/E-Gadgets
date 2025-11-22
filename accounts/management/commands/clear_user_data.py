from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import (
    Order, OrderItem, Cart, Wishlist, Review, 
    PurchaseHistory, Notification, ProductView, UserProfile
)


class Command(BaseCommand):
    help = 'Remove all user data except admin/staff users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting user data cleanup...'))
        
        # Get non-admin users
        regular_users = User.objects.filter(is_staff=False, is_superuser=False)
        user_count = regular_users.count()
        
        if user_count == 0:
            self.stdout.write(self.style.SUCCESS('No regular users found. Nothing to delete.'))
            return
        
        self.stdout.write(f'Found {user_count} regular users to delete.')
        
        # Count related data before deletion
        orders_count = Order.objects.filter(user__in=regular_users).count()
        cart_count = Cart.objects.filter(user__in=regular_users).count()
        wishlist_count = Wishlist.objects.filter(user__in=regular_users).count()
        reviews_count = Review.objects.filter(user__in=regular_users).count()
        
        self.stdout.write(f'  - Orders: {orders_count}')
        self.stdout.write(f'  - Cart items: {cart_count}')
        self.stdout.write(f'  - Wishlist items: {wishlist_count}')
        self.stdout.write(f'  - Reviews: {reviews_count}')
        
        # Confirm deletion (skip if --no-input flag is used)
        if not options['no_input']:
            confirm = input('\nAre you sure you want to delete all this data? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Delete related data first (cascade will handle most, but being explicit)
        Order.objects.filter(user__in=regular_users).delete()
        Cart.objects.filter(user__in=regular_users).delete()
        Wishlist.objects.filter(user__in=regular_users).delete()
        Review.objects.filter(user__in=regular_users).delete()
        PurchaseHistory.objects.filter(user__in=regular_users).delete()
        Notification.objects.filter(user__in=regular_users).delete()
        ProductView.objects.filter(user__in=regular_users).delete()
        
        # Delete user profiles and users
        regular_users.delete()
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully deleted {user_count} users and all their data!'))
        self.stdout.write(self.style.SUCCESS('Admin/staff users and their data remain intact.'))
        
        # Show remaining users
        remaining_users = User.objects.all()
        self.stdout.write(f'\nRemaining users: {remaining_users.count()}')
        for user in remaining_users:
            role = 'Superuser' if user.is_superuser else 'Staff' if user.is_staff else 'Regular'
            self.stdout.write(f'  - {user.username} ({role})')
