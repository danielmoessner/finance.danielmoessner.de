from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import status

from finance.banking.serializers import AccountSerializer, ChangeSerializer, CategorySerializer, DepotSerializer
from finance.banking.permissions import IsOwner
from finance.banking.models import Account, Change, Category, Depot


class DepotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows depots to be viewed or edited.
    """
    serializer_class = DepotSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Depot.objects.none()

    def get_queryset(self):
        return Depot.get_objects_by_user(self.request.user)


class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows accounts to be viewed or edited.
    """
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Account.objects.none()

    def get_queryset(self):
        return Account.get_objects_by_user(self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Category.objects.none()

    def get_queryset(self):
        return Category.get_objects_by_user(self.request.user)


class ChangeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows changes to be viewed or edited.
    """
    serializer_class = ChangeSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]
    queryset = Change.objects.none()

    def get_queryset(self):
        return Change.get_objects(self.request.user)
