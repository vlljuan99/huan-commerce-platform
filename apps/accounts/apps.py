from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _create_default_groups(sender, **kwargs):
    """
    Create default Django Groups for internal roles.
    Called after every migrate — idempotent via get_or_create.

    Groups:
      - Administrador: full access to all admin areas
      - Comercial: access to customers, orders, catalog (no accounts/billing)
    Assign users to groups via User admin > Permissions > Groups.
    """
    from django.contrib.auth.models import Group, Permission

    admin_group, _ = Group.objects.get_or_create(name="Administrador")
    Group.objects.get_or_create(name="Comercial")

    # Administrador gets all permissions (superuser should be used instead,
    # but the group acts as a label for non-superuser admins)
    if not admin_group.permissions.exists():
        admin_group.permissions.set(Permission.objects.all())


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts"

    def ready(self):
        post_migrate.connect(_create_default_groups, sender=self)
