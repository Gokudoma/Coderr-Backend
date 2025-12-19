import django_filters
from django.db.models import Q
from offers_app.models import Offer, Review


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
        Search in title and description using Django's Q objects.
        """
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )


class ReviewFilter(django_filters.FilterSet):
    """
    FilterSet for Review listing.
    Maps query parameters 'business_user_id' and 'reviewer_id' to model fields.
    """
    business_user_id = django_filters.NumberFilter(field_name='business_user')
    reviewer_id = django_filters.NumberFilter(field_name='reviewer')

    class Meta:
        model = Review
        fields = ['business_user_id', 'reviewer_id']