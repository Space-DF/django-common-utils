import logging

from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class QueryAlertMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        total_queries = len(connection.queries)
        max_queries = 20

        if total_queries > max_queries:
            api_path = request.path_info
            api_method = request.method
            api_name = f"{api_method} {api_path}"
            logging.warning(
                f"Alert: Number of queries ({total_queries}) for API {api_name}"
            )

        return response
