"""
Раздел документации "Сети заведений".
"""

from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
)
from uuid import UUID

from dodo_is_api_library.utils.http_client import (
    HttpMethods,
    HttpResponseDTO,
    http_client,
)
from dodo_is_api_library.utils.scopes import DodoISScopes


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
        business_id: UUID | None = None,
        country_id: str | None = None,
        unit_states: Iterable[Literal["Open", "Close"]] | None = None,
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

        Аргументы:
            - business_id [UUID | None]: идентификатор бизнеса в формате UUID
            - country_id [str]: идентификатор страны в формате ISO 3166-1 alpha-2
            - unit_states [Iterable[str]]: Состояние юнита

        Требования к аргументам:
            - если unit_states не указан, то DodoIS вернет только "Open" пиццерии.

        Необходимы scopes:
            - franchisee:read - получение информации о сетях заведений
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__units_get_validate_scopes(user_data=user_data)
        response: HttpResponseDTO = await http_client.send_request(
            **self.__units_get_http_params(
                business_id=business_id,
                country_id=country_id,
                unit_states=unit_states,
                user_data=user_data,
            ),
        )
        if response.status_code != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=response.status_code,
                detail=response.data,
            )
        return response.data

    def __units_get_http_params(
        self,
        business_id: UUID | None,
        country_id: str | None,
        unit_states: Iterable[Literal["Open", "Close"]] | None,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для units_get."""
        return {
            "method": HttpMethods.GET,
            "url": f"{self.__base_url}/units",
            "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
            'query_params': {
                k: v
                for k, v
                in {
                    'businessId': business_id,
                    'countryId': country_id,
                    'unitStates': ','.join(s for s in unit_states) if unit_states else None,
                }.items()
                if v is not None
            },
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
