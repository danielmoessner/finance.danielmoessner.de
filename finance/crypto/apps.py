from django.apps import AppConfig
import logging


class CryptoConfig(AppConfig):
    name = "finance.crypto"
    verbose_name = "Crypto"

    def ready(self):
        from background_task.models import Task
        from finance.crypto.tasks import update_prices
        if not Task.objects.filter(task_name="finance.crypto.tasks.update_prices").exists():
            update_prices(repeat=Task.DAILY)
        # from finance.crypto.tasks import test
        # if not Task.objects.filter(task_name="finance.crypto.tasks.test").exists():
        #     test(repeat=5)
