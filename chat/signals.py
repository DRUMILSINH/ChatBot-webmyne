from django.contrib.auth.models import Group


def ensure_rbac_groups(**kwargs):
    for name in ("chat_user", "chat_analyst", "chat_admin"):
        Group.objects.get_or_create(name=name)
