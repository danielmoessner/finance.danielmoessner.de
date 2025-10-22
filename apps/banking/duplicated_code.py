from django.db import models


def set_balance(instance, changes):
    if changes.count() <= 0:
        instance.balance = 0
    else:
        instance.balance = changes.aggregate(models.Sum("change"))["change__sum"]
    instance.save()
