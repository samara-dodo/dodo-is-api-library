"""
Раздел документации "Marketplace".
"""

from typing import Callable

from dodo_is_api_library.api_sections.marketplace.subsections.franchisee import ApiFranchisee


class ApiMarketplace:
    """
    Раздел документации "Marketplace".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.franchisee = ApiFranchisee(
            get_user_data=get_user_data,
            raise_http_exception=raise_http_exception,
            base_url=f"{base_url}/franchisee",
        )
