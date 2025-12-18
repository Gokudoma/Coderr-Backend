from rest_framework.pagination import PageNumberPagination


class OfferPagination(PageNumberPagination):
    """
    Custom pagination class for Offers.
    Allows the client to set the page size via query parameter.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100