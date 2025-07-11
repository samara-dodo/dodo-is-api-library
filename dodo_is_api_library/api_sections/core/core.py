"""
Раздел документации "Команда".
"""

from typing import Callable

from dodo_is_api_library.api_sections.core.subsections.accounting import ApiAccounting
from dodo_is_api_library.api_sections.core.subsections.staff import ApiStaff


class ApiCore():
    """
    Раздел документации "Учет, производство, доставка, команда".
    """

    def __init__(
        self,
        get_user_data: Callable,
        base_url: str,
    ):
        self.accounting = ApiAccounting(get_user_data=get_user_data, base_url=base_url)
        self.staff = ApiStaff(get_user_data=get_user_data, base_url=base_url)
