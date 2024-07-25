from apps.banking.models import Account


def calculate_change_counts():
    accounts = list(Account.objects.all())
    for account in accounts:
        account.calculate_changes_count()
        account.save()
