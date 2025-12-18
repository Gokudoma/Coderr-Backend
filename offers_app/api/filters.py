import django_filters
from offers_app.models import Offer


class OfferFilter(django_filters.FilterSet):
    """
    FilterSet for Offer listing.
    Supports filtering by creator_id, calculated min_price, and max_delivery_time.
    """
    creator_id = django_filters.NumberFilter(field_name='user', lookup_expr='exact')
    min_price = django_filters.NumberFilter(field_name='min_price', lookup_expr='gte')
    max_delivery_time = django_filters.NumberFilter(
        field_name='min_delivery_time', lookup_expr='lte'
    )
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Offer
        fields = ['creator_id', 'min_price', 'max_delivery_time']

    def filter_search(self, queryset, name, value):
        """
        Search in title and description.
        """
        return queryset.filter(
            django_filters.models.Q(title__icontains=value) |
            django_filters.models.Q(description__icontains=value)
        )