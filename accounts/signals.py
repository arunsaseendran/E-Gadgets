from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from orders.views import send_order_status_email


# Store the old status before save
@receiver(pre_save, sender=Order)
def store_old_status(sender, instance, **kwargs):
    """Store the old status before updating"""
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            instance._old_status = old_order.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Order)
def send_status_update_email(sender, instance, created, **kwargs):
    """Send email when order status changes"""
    if not created and hasattr(instance, '_old_status'):
        old_status = instance._old_status
        new_status = instance.status
        
        # Only send email if status actually changed
        if old_status and old_status != new_status:
            send_order_status_email(instance, old_status, new_status)
