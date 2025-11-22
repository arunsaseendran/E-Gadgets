from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Order


class Command(BaseCommand):
    help = 'Delete all orders placed by admin/staff users'

    def handle(self, *args, **kwargs):
        # Get all admin and staff users
        admin_users = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
        
        deleted_count = 0
        for admin_user in admin_users:
            orders = Order.objects.filter(user=admin_user)
            count = orders.count()
            orders.delete()
            deleted_count += count
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {count} orders for admin user: {admin_user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total orders deleted: {deleted_count}')
        )
