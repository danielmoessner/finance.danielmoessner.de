class GetDepotMixin:
    def get_depot(self):
        return self.request.user.stock_depots.filter(is_active=True).first()
