from apps.banking.models import Account, Category, Depot


def calculate_change_counts():
    accounts = list(Account.objects.all())
    for account in accounts:
        account.calculate_changes_count()
        account.save()
    depots = list(Depot.objects.filter(is_active=True))
    for depot in depots:
        depot.calculate_changes_count()
        depot.save()
    categories = list(Category.objects.all())
    for category in categories:
        category.calculate_changes_count()
        category.save()
