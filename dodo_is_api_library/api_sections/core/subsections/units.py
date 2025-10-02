"""
Раздел документации "Заведения".
"""

from datetime import (
    date,
    datetime,
)
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Iterable,
)
from uuid import UUID

from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.converter import (
    convert_datetime_to_str,
    convert_uuid_to_str,
)
from dodo_is_api_library.utils.scopes import DodoISScopes
from dodo_is_api_library.utils.validators import (
    process_full_address,
    process_legal_entity_name,
)

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

    async def shifts_get(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str],
        skip: int = 0,
        take: int = 100,
        take_all: bool = False,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Заведения → Смены заведений

        Возвращает список смен заведений, отсортированный по дате начала смены.

        Документация: https://docs.dodois.io/docs/dodo-is/b73aa5a9c1052-zavedeniya-smeny-zavedenij
        URL: https://api.dodois.io/dodopizza/ru/units/shifts

        Смены выбираются по времени начала (если начало смены попало
        в диапазон from – to включительно).

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей. Повторять до тех пор,
        пока не будет достигнут конец списка (isEndOfListReached = true).

        Аргументы:
            - clock_in_from [str | datetime]: начало периода, в который попадает начало смен, в формате ISO 8601 (2022-01-01T11:00:00)
            - clock_in_to [str | date]: конец периода, в который попадает начало смен, в формате ISO 8601 (2022-01-02)
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать
            - take_all [bool]: признак, что нужно получить все записи из API

        Требования к аргументам:
            - в units можно перечислить до 30 заведений в одном запросе
            - from должен быть меньше, чем to

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса

        Требования к scopes:
            - unit:read - заведения, доступ на чтение
            - unitshifts:read - смены заведений, доступ на чтение
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__shifts_get_validate_scopes(user_scopes=user_data['scopes'])
        http_data: dict[str, Any] = self.__shifts_get_http_params(
            access_token=user_data['access_token'],
            clock_in_from=clock_in_from,
            clock_in_to=clock_in_to,
            units=units,
            skip=skip,
            take=take,
            take_all=take_all,
        )
        return_data: list[dict[str, Any]] = []
        while 1:
            status_, data, _ = await HttpClient.send_request(**http_data)
            if status_ != HTTPStatus.OK:
                self.__raise_http_exception(
                    status_code=status_,
                    detail=data,
                )
            return_data.extend(data["shifts"])
            if data['isEndOfListReached'] or not take_all:
                break
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']
        return self.__shifts_get_process_data(data=return_data)


    def __shifts_get_process_data(
        self,
        data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Обрабатывает полученные данные из API ответа для shifts_get.
        """
        return data

    def __shifts_get_http_params(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str],
        skip: int = 0,
        take: int = 100,
        take_all: bool = False,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для shifts_get.
        """
        if len(units) > 30:
            raise ValueError('В "units" можно перечислить до 30 заведений в одном запросе')
        if clock_in_from:
            clock_in_from = convert_datetime_to_str(clock_in_from)
        if clock_in_to:
            clock_in_to = convert_datetime_to_str(clock_in_to)
        if take_all:
            skip = 0
            take = 100
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'from': clock_in_from,
                    'to': clock_in_to,
                    'units': ','.join(convert_uuid_to_str(uid=u) for u in units),
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __shifts_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода shifts_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.UNIT_READ,
                DodoISScopes.UNITSHIFTS_READ,
                DodoISScopes.USER_ROLE_READ,
            },
        )

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

        Документация: https://docs.dodois.io/docs/dodo-is/f901f00320572-zavedeniya-informacziya-o-piczczeriyah-kofejnyah
        URL: https://api.dodois.io/dodopizza/ru/units/stores

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей.
        Повторять до тех пор, пока не будет достигнут конец списка
        (isEndOfListReached = true).

        Аргументы:
            - business_id [str]: идентификатор бизнеса
            - country_id [str]: идентификатор страны в формате ISO 3166-1 alpha-2
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
            status_, data, _ = await HttpClient.send_request(**http_data)
            if status_ != HTTPStatus.OK:
                self.__raise_http_exception(
                    status_code=status_,
                    detail=data,
                )
            return_data.extend(data["stores"])
            if data['isEndOfListReached'] or not take_all:
                break
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']
        return self.__stores_get_process_data(data=return_data)

    def __stores_get_process_data(
        self,
        data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        for d in data:
            d["organizationName"] = process_legal_entity_name(d["organizationName"])
            d["location"]["fullAddress"] = process_full_address(d["location"]["fullAddress"])
        return data

    def __stores_get_http_params(
        self,
        access_token: str,
        business_id: str,
        country_id: str,
        organizations: Iterable[str] | None = None,
        unit_states: Iterable[str] | None = None,
        units: list[str | UUID] | None = None,
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
            'url': f'{self.__base_url}/stores',
            'query_params': {
                k: v
                for k, v
                in {
                    'businessId': business_id,
                    'countryId': country_id,
                    'organizations': ','.join(str(o) for o in organizations) if organizations else None,
                    'unitStates': ','.join(str(s) for s in unit_states) if unit_states else None,
                    'skip': skip,
                    'take': take,
                    'units': ','.join(convert_uuid_to_str(u) for u in units) if units else None,
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
                DodoISScopes.SHARED,
            },
        )
