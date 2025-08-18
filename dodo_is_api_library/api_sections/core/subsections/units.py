"""
Раздел документации "Заведения".
"""

from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Iterable,
)

from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.scopes import DodoISScopes

client: HttpClient = HttpClient()


class ApiUnits():
    """
    Раздел документации "Заведения".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = f'{base_url}/units'

    async def stores_get(
        self,
        business_id: str,
        country_id: str,
        organizations: Iterable[str] | None = None,
        unit_states: Iterable[str] | None = None,
        units: list[str] | None = None,
        skip: int = 0,
        take: int = 100,
        take_all: bool = False,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Заведения → Информация о пиццериях/кофейнях

        Возвращает список пиццерий/кофеен с информацией о них.

        Документация: https://api.dodois.io/dodopizza/ru/units/stores
        URL: https://api.dodois.io/dodopizza/ru/units/stores

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей.
        Повторять до тех пор, пока не будет достигнут конец списка
        (isEndOfListReached = true).

        Аргументы:
            - business_id [str]: идентификатор бизнеса
            - country_id [str | date]: идентификатор страны в формате ISO 3166-1 alpha-2
            - organizations [Iterable[str]]: перечень ID организаций Dodo IS
            - unit_states [Iterable[str]]: перечень состояний заведений в Dodo IS
            - units [Iterable[str]]: список заведений (пиццерий) Dodo IS
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать
            - take_all [bool]: признак, что нужно получить все записи из API

        Требования к аргументам:
            - в unit_states допустимы следующие значения: ["Open", "Close", "TemporaryClosed"]
            - если take_all=True, то take будет проигнорирован

        Требования к scopes:
            - shared - общее
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__stores_get_validate_scopes(user_scopes=user_data['scopes'])
        http_data: dict[str, Any] = self.__stores_get_http_params(
            access_token=user_data['access_token'],
            business_id=business_id,
            country_id=country_id,
            organizations=organizations,
            unit_states=unit_states,
            units=units,
            skip=skip,
            take=take,
            take_all=take_all,
        )
        return_data: list[dict[str, Any]] = []
        while 1:
            status_, data, _ = await client.send_request(**http_data)
            if status_ != HTTPStatus.OK:
                self.__raise_http_exception(
                    status_code=status_,
                    detail=data,
                )
            return_data.append(data["stores"])
            if data['isEndOfListReached'] or not take_all:
                return data
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']

    def __stores_get_http_params(
        self,
        access_token: str,
        business_id: str,
        country_id: str,
        organizations: Iterable[str] | None = None,
        unit_states: Iterable[str] | None = None,
        units: list[str] | None = None,
        skip: int = 0,
        take: int = 100,
        take_all: bool = False,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для stores_get.
        """
        if take_all:
            skip = 0
            take = 100
        if (
            unit_states is not None
            and
            not set(unit_states).issubset({"Open", "Close", "TemporaryClosed"})
        ):
            raise ValueError(
                'В "unit_states" допустимы следующие значения: ["Open", "Close", "TemporaryClosed"]',
            )
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/sales',
            'query_params': {
                k: v
                for k, v
                in {
                    'businessId': business_id,
                    'countryId': country_id,
                    'organizations': ','.join(str(o) for o in organizations),
                    'unitStates': ','.join(str(s) for s in unit_states),
                    'skip': skip,
                    'take': take,
                    'units': ','.join(u for u in units),
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __stores_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода stores_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.STAFF_SHIFTS_READ,
                DodoISScopes.USER_ROLE_READ,
            },
        )
