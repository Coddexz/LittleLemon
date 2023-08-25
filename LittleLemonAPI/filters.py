from django_filters import rest_framework
from .models import MenuItem

class MenuItemFilter(rest_framework.FilterSet):
    class Meta:
        model = MenuItem
        fields = '__all__'
        
# Check the existence of filters and apply them possibly
class OrderFilter:
    @staticmethod
    def check_filters(queryset, params):
        id_name = params.get('id')
        status_name = params.get('status')
        user_name = params.get('user')
        date_name = params.get('date')
        delivery_crew_name = params.get('delivery_crew')
    
        if id_name:
            queryset = queryset.filter(id=id_name)
        if status_name:
            queryset = queryset.filter(status=status_name)
        if user_name:
            queryset = queryset.filter(user=user_name)
        if date_name:
            queryset = queryset.filter(date=date_name)
        if delivery_crew_name:
            queryset = queryset.filter(delivery_crew=delivery_crew_name)
        
        return queryset