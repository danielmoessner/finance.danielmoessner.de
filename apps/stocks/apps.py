from django.apps import AppConfig


class StocksConfig(AppConfig):
    name = 'apps.stocks'
    verbose_name = 'Stocks'

    # def ready(self):
    #     from background_task.models import Task
    #     from apps.stocks.tasks import fetch_prices
    #     if not Task.objects.filter(task_name="apps.stocks.tasks.fetch_prices").exists():
    #         fetch_prices(repeat=Task.DAILY)
