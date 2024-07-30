from apps.banking.models import Account, Depot


def calculate_change_counts():
    accounts = list(Account.objects.all())
    for account in accounts:
        account.calculate_changes_count()
        account.save()
    depots = list(Depot.objects.filter(is_active=True))
    for depot in depots:
        depot.calculate_changes_count()
        depot.save()
