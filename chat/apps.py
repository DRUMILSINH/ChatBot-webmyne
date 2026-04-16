from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"

    def ready(self):
        from django.db.models.signals import post_migrate
        from chat.signals import ensure_rbac_groups

        post_migrate.connect(
            ensure_rbac_groups,
            sender=self,
            dispatch_uid="chat.ensure_rbac_groups",
        )

        try:
            from chat.warmup import start_cold_start_preload

            start_cold_start_preload()
        except Exception:
            return
