from django.apps import AppConfig
import logging


logger = logging.getLogger("background_tasks")


class CryptoConfig(AppConfig):
    name = "finance.crypto"
    verbose_name = "Crypto"

    def ready(self):
        from background_task.models import Task
        if Task.objects.all().count() == 0:
            from finance.crypto.tasks import update_prices
            from background_task.tasks import Task
            update_prices(repeat=Task.DAILY)
            logger.info("The Update Prices Background Task was started.")
        else:
            logger.info("Some Background Task is already running.")
