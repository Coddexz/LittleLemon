from django.dispatch import receiver
from djoser.signals import user_registered

# Adding every new user to the customer group
@receiver(user_registered)
def add_to_default_group(sender, user, request, **kwargs):
    from django.contrib.auth.models import Group
    group_name = 'Customer'
    group, created = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
