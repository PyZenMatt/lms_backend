from django.apps import AppConfig


class RewardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rewards'

    
    def ready(self):
        # importa i signal handlers per invalidare la cache e reward automation
        import rewards.signals  # noqa
