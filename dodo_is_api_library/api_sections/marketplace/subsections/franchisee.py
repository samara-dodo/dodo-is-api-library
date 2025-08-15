"""
Раздел документации "Сети заведений".
"""

from http import HTTPStatus
from typing import (
    Any,
    Callable,
)

from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.scopes import DodoISScopes

client: HttpClient = HttpClient()


class ApiFranchisee:
    """
    Раздел документации "Сети заведений".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = base_url

    async def units_get(
        self,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Заведения → Сети

        Получение информации о сетях заведений.
        Идентификаторы концепций (businessId):
            - 63d4829611ea45c8ae71394860a2481c - Dodo Pizza
            - c0b18e725258427a8bffea4f73957b0e - Drinkit

        Документация: https://docs.dodois.io/docs/marketplace/96e2e64397a05-zavedeniya-seti
        URL: https://api.dodois.io/franchisee/units

        Необходимы scopes:
            - franchisee:read - получение информации о сетях заведений
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__units_get_validate_scopes(user_data=user_data)
        status_, data, _ = await HttpClient.send_request(
            **self.__units_get_http_params(user_data=user_data),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        return data

    def __units_get_http_params(
        self,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для units_get."""
        return {
            "method": HttpMethods.GET,
            "url": f"{self.__base_url}/units",
            "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
        }

    def __units_get_validate_scopes(
        self,
        user_data: dict[str, Any],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_data['scopes'],
            required_scopes={DodoISScopes.FRANCHISEE_READ},
        )
