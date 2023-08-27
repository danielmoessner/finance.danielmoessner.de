from django.core.management.base import BaseCommand

from apps.stocks.models import Bank, Depot, Stock


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        depots = Depot.objects.all()
        banks = Bank.objects.all()
        stocks = Stock.objects.all()
        for objs in [depots, banks, stocks]:
            for obj in objs:
                obj.reset()
