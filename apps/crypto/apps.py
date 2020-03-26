from django.apps import AppConfig
import logging


class CryptoConfig(AppConfig):
    name = "apps.crypto"
    verbose_name = "Crypto"

    # def ready(self):
    #     from background_task.models import Task
    #     from apps.crypto.tasks import update_prices
    #     if not Task.objects.filter(task_name="apps.crypto.tasks.update_prices").exists():
    #         update_prices(repeat=Task.DAILY)
        # from apps.crypto.tasks import test
        # if not Task.objects.filter(task_name="apps.crypto.tasks.test").exists():
        #     test(repeat=5)
