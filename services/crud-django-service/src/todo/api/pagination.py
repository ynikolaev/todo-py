from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = 10  # default page size
    page_size_query_param = "page_size"  # allow clients to override
    max_page_size = 100
