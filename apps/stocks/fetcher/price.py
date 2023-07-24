from django.utils import timezone
from apps.stocks.models import Stock
from apps.stocks.forms import PriceForm


def save_price(price: float, stock: Stock) -> None:
    price = PriceForm(
        {
            "ticker": stock.ticker,
            "exchange": stock.exchange,
            "date": timezone.now(),
            "price": price,
        }
    )
    if price.is_valid():
        price.save()
