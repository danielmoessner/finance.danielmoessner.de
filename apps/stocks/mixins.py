from django.http import HttpRequest



class GetDepotMixin:
    request: HttpRequest

    def get_depot(self):
        return self.request.user.stock_depots.filter(is_active=True).first()
