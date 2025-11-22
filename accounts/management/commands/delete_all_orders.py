from django.core.management.base import BaseCommand
from accounts.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Delete all orders and order items from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all orders',
        )

    def handle(self, *args, **kwargs):
        confirm = kwargs.get('confirm')
        
        if not confirm:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL orders and order items from the database.\n'
                    'To confirm, run: python manage.py delete_all_orders --confirm'
                )
            )
            return
        
        # Count orders and items before deletion
        order_count = Order.objects.count()
        order_item_count = OrderItem.objects.count()
        
        if order_count == 0:
            self.stdout.write(self.style.WARNING('No orders found in the database.'))
            return
        
        # Delete all order items first (cascade will handle this, but being explicit)
        OrderItem.objects.all().delete()
        
        # Delete all orders
        Order.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted:\n'
                f'   - {order_count} orders\n'
                f'   - {order_item_count} order items'
            )
        )
