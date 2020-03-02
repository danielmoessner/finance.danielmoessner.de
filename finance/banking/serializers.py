from rest_framework import serializers

from finance.users.models import StandardUser as User
from .models import Account, Change, Category, Depot


class DepotSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="banking:depot-detail")
    accounts = serializers.HyperlinkedRelatedField(many=True, view_name='banking:account-detail', read_only=True)
    categories = serializers.HyperlinkedRelatedField(many=True, view_name='banking:category-detail', read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.none())

    class Meta:
        model = Depot
        fields = ['url', 'user', 'name', 'accounts', 'categories']

    def get_fields(self):
        fields = super(DepotSerializer, self).get_fields()
        user = self.context['request'].user
        fields['user'].queryset = User.objects.filter(pk=user.pk)
        return fields


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    changes = serializers.HyperlinkedRelatedField(many=True, view_name='banking:change-detail', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="banking:account-detail")
    depot = serializers.HyperlinkedRelatedField(view_name='banking:depot-detail', format='html',
                                                queryset=Depot.objects.none())

    class Meta:
        model = Account
        fields = ['url', 'depot', 'name', 'changes']

    def get_fields(self):
        fields = super(AccountSerializer, self).get_fields()
        user = self.context['request'].user
        fields['depot'].queryset = Depot.get_objects_by_user(user)
        return fields


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    changes = serializers.HyperlinkedRelatedField(many=True, view_name='banking:change-detail', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="banking:category-detail")
    depot = serializers.HyperlinkedRelatedField(view_name='banking:depot-detail', format='html',
                                                queryset=Depot.objects.none())

    class Meta:
        model = Category
        fields = ['url', 'depot', 'name', 'description', 'changes']

    def get_fields(self):
        fields = super(CategorySerializer, self).get_fields()
        user = self.context['request'].user
        fields['depot'].queryset = Depot.get_objects_by_user(user)
        return fields


class ChangeSerializer(serializers.ModelSerializer):
    account = serializers.HyperlinkedRelatedField(view_name='banking:account-detail', format='html',
                                                  queryset=Account.objects.none())
    category = serializers.HyperlinkedRelatedField(view_name='banking:category-detail', format='html',
                                                   queryset=Category.objects.none())
    url = serializers.HyperlinkedIdentityField(view_name="banking:change-detail")

    class Meta:
        model = Change
        fields = ['url', 'account', 'date', 'category', 'description', 'change']

    def validate(self, data):
        if 'account' in data:
            account = data['account']
        else:
            account = self.instance.account
        if 'category' in data:
            category = data['category']
        else:
            category = self.instance.category
        if account.depot != category.depot:
            raise serializers.ValidationError('The account depot has to be the same as the category depot')
        return data

    def get_fields(self):
        fields = super(ChangeSerializer, self).get_fields()
        if self.instance.__class__ == Change:
            depot = self.instance.account.depot
            fields['account'].queryset = Account.get_objects_by_depot(depot)
            fields['category'].queryset = Category.get_objects_by_depot(depot)
        else:
            user = self.context['request'].user
            fields['account'].queryset = Account.get_objects_by_user(user)
            fields['category'].queryset = Category.get_objects_by_user(user)
        return fields
