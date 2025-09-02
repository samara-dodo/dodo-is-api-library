"""
Раздел документации "Команда".
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

from dodo_is_api_library.utils.converter import convert_date_to_str
from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.scopes import DodoISScopes

client: HttpClient = HttpClient()


class ApiStaff():
    """
    Раздел документации "Команда".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = f'{base_url}/staff'

    # Смены сотрудников (по пиццериям)

    async def shifts_get(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str | UUID],
        staff_type: str | None = None,
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
    ) -> tuple[int, dict, dict]:
        """
        Команда → Смены сотрудников (по пиццериям)

        Смены сотрудников (рабочее время, рабочие часы, фактические часы):
        отработанное время с детализацией по дневным, ночным и праздничным часам
        (в минутах), данные о доставленных заказах, расстоянии,
        стаже сотрудника на момент смены.

        Документация: https://docs.dodois.io/docs/dodo-is/16c2ad8c8d1eb-komanda-smeny-sotrudnikov-po-piczczeriyam
        URL: https://api.dodois.io/dodopizza/ru/staff/shifts

        Смены выбираются по времени начала. Также есть фильтр по типу сотрудника.
        Время смен не обрезается по фильтру. Если начало смены попало в диапазон
        clockInFrom – clockInTo (отметки времени начала смены), то смена вернётся целиком.
        Для получения всех часов по каждому сотруднику нужно выкачать все смены
        за период и сгруппировать у себя по staffId.

        Аргументы:
            - clock_in_from [str | datetime]: начало периода, в который попадает начало смен, в формате ISO 8601 (2022-01-01T11:00:00)
            - clock_in_to [str | date]: конец периода, в который попадает начало смен, в формате ISO 8601 (2022-01-02)
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - staff_type [str]: фильтр по типу сотрудника
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к аргументам:
            - в units можно перечислить до 30 заведений в одном запросе
            - from должен быть меньше, чем to

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса
            - shift supervisor - менеджер смены
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__shifts_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_request(
            **self.__shifts_get_http_params(
                access_token=user_data['access_token'],
                clock_in_from=clock_in_from,
                clock_in_to=clock_in_to,
                units=units,
                staff_type=staff_type,
                skip=skip,
                take=take,
            ),
        )

    def __shifts_get_http_params(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str | UUID],
        staff_type: str | None,
        skip: int,
        take: int,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для shifts_get.
        """
        if isinstance(clock_in_from, datetime):
            clock_in_from = clock_in_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(clock_in_to, date):
            clock_in_to = clock_in_to.strftime('%Y-%m-%d')
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'clockInFrom': clock_in_from,
                    'clockInTo': clock_in_to,
                    'units': ','.join(str(u).replace("-", "") for u in units),
                    'staffTypeName': staff_type,
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
                DodoISScopes.STAFF_SHIFTS_READ,
                DodoISScopes.USER_ROLE_READ,
            },
        )

    # Список сотрудников

    async def members_get(
        self,
        dismissed_from: str | date | None = None,
        dismissed_to: str | date | None = None,
        hired_from: str | date | None = None,
        hired_to: str | date | None = None,
        last_modified_from: str | date | None = None,
        last_modified_to: str | date | None = None,
        staff_type: str | None = None,
        statuses: Iterable[str] | None = None,
        units: Iterable[str | UUID] | None = None,
        skip: int = 0,
        take: int = 1000,
        take_all: bool = False,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ):
        """
        Команда → Список сотрудников

        Возвращает список сотрудников, отсортированный по дате трудоустройства (hiredOn).

        Документация: https://docs.dodois.io/docs/dodo-is/33e626f47ca51-komanda-spisok-sotrudnikov
        URL: https://api.dodois.io/dodopizza/ru/staff/members

        Аргументы:
            - dismissed_from [str | date] - фильтр по дате увольнения сотрудников, начало диапазона, в формате ISO 8601 (2022-01-01)
            - dismissed_to [str | date] - фильтр по дате увольнения сотрудников, конец диапазона, в формате ISO 8601 (2022-01-01)
            - hired_from [str | date] - фильтр по дате трудоустройства сотрудников, начало диапазона, в формате ISO 8601 (2022-01-01)
            - hired_to [str | date] - фильтр по дате трудоустройства сотрудников, конец диапазона, в формате ISO 8601 (2022-01-01)
            - last_modified_from [str | date] - фильтр по дате изменения, начало диапазона, в формате ISO 8601 (2022-01-01)
            - last_modified_to [str | date] - фильтр по дате изменения, конец диапазона, в формате ISO 8601 (2022-01-01)
            - staff_type [str] - фильтр по типу сотрудника
            - statuses [list[str]] - фильтр по статусу сотрудника
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать
            - take_all [bool]: признак, что нужно получить все записи из API

        Требования к аргументам:
            - каждый фильтр *_from должны быть не больше соответствующего фильтра *_to
            - фильтр по заведениям units применяется по нескольким значениям; если не указан,
              то будут выданы записи по всем доступным для пользователя заведениям
            - staff_type должен быть одним из следующих значений: "Operator", "KitchenMember", "Courier", "Cashier", "PersonalManager"
            - statuses должен включать следующие значения: "Dismissed" - уволен, "Suspended" - отстранен, "Active" - работает
            - фильтр take должен быть больше 0 и меньше либо равен 1000

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса
            - shift supervisor - менеджер смены

        Требования к scopes:
            - staffmembers:read - сотрудники / персонал, доступ на чтение (содержит персональные данные)
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__members_get_validate_scopes(user_scopes=user_data["scopes"])
        http_data: dict[str, Any] = self.__members_get_http_params(
            access_token=user_data['access_token'],
            dismissed_from=dismissed_from,
            dismissed_to=dismissed_to,
            hired_from=hired_from,
            hired_to=hired_to,
            last_modified_from=last_modified_from,
            last_modified_to=last_modified_to,
            staff_type=staff_type,
            statuses=statuses,
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
            return_data.extend(data["members"])
            if data['isEndOfListReached'] or not take_all:
                break
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']
        return self.__members_get_process_data(data=return_data)

    def __members_get_process_data(
        self,
        data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Обрабатывает полученные данные из API ответа для members_get.
        """
        return data

    def __members_get_http_params(
        self,
        access_token: str,
        dismissed_from: str | date | None,
        dismissed_to: str | date | None,
        hired_from: str | date | None,
        hired_to: str | date | None,
        last_modified_from: str | date | None,
        last_modified_to: str | date | None,
        staff_type: str | None,
        statuses: Iterable[str] | None,
        units: Iterable[str | UUID] | None,
        skip: int,
        take: int,
        take_all: bool,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для members_get.
        """
        # TODO. Оптимизировать.
        if staff_type and staff_type.lower() not in ('operator', 'kitchenmember', 'courier', 'cashier', 'personalmanager'):
            return self.__raise_http_exception(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='staff_type must be one of "Operator", "KitchenMember", "Courier", "Cashier", "PersonalManager"',
            )
        if statuses:
            for s in statuses:
                if s.lower() not in ('dismissed', 'suspended', 'active'):
                    return self.__raise_http_exception(
                        status_code=HTTPStatus.BAD_REQUEST,
                        detail='statuses must be one of "Dismissed", "Suspended", "Active"',
                    )
        if take_all:
            skip = 0
            take = 1000
        if dismissed_from:
            dismissed_from = convert_date_to_str(dismissed_from)
        if dismissed_to:
            dismissed_to = convert_date_to_str(dismissed_to)
        if hired_from:
            hired_from = convert_date_to_str(hired_from)
        if hired_to:
            hired_to = convert_date_to_str(hired_to)
        if last_modified_from:
            last_modified_from = convert_date_to_str(last_modified_from)
        if last_modified_to:
            last_modified_to = convert_date_to_str(last_modified_to)
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/members',
            'query_params': {
                k: v
                for k, v
                in {
                    'dismissedFrom': dismissed_from,
                    'dismissedTo': dismissed_to,
                    'hiredFrom': hired_from,
                    'hiredTo': hired_to,
                    'lastModifiedFrom': last_modified_from,
                    'lastModifiedTo': last_modified_to,
                    'staffType': staff_type,
                    'statuses': ','.join(statuses) if statuses else None,
                    'units': ','.join(str(u).replace("-", "") for u in units) if units else None,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }



    def __members_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода members_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.STAFF_MEMBERS_READ,
                DodoISScopes.USER_ROLE_READ,
            },
        )

    # Смены сотрудников (по идентификаторам)

    async def members_shifts_get(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ):
        """
        Команда → Смены сотрудников (по идентификаторам)

        Смены сотрудников (рабочее время, рабочие часы, фактические часы):
        отработанное время с детализацией по дневным, ночным и праздничным
        часам (в минутах), данные о доставленных заказах, расстоянии,
        стаже сотрудника на момент смены.

        Документация: https://docs.dodois.io/docs/dodo-is/9eeef5b727118-komanda-smeny-sotrudnikov-po-identifikatoram
        URL: https://api.dodois.io/dodopizza/ru/staff/members/shifts

        Смены выбираются по времени начала. Также есть фильтр по типу сотрудника.
        Время смен не обрезается по фильтру. Если начало смены попало в диапазон
        clockInFrom – clockInTo (отметки времени начала смены), то смена вернётся целиком.
        Для получения всех часов по каждому сотруднику нужно выкачать все смены
        за период и сгруппировать у себя по staffId.

        Аргументы:
            - clock_in_from [str | datetime]: начало периода, в который попадает начало смен, в формате ISO 8601 (2022-01-01T11:00:00)
            - clock_in_to [str | date]: конец периода, в который попадает начало смен, в формате ISO 8601 (2022-01-02)
            - staff_ids [Iterable[str | UUID]]: идентификаторы сотрудников в формате UUID
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к аргументам:
            - В staff_ids можно перечислить до 30 сотрудников в одном запросе

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса
            - shift supervisor - менеджер смены
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__members_shifts_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_request(
            **self.__members_shifts_get_http_params(
                access_token=user_data['access_token'],
                clock_in_from=clock_in_from,
                clock_in_to=clock_in_to,
                staff_ids=staff_ids,
                skip=skip,
                take=take,
            ),
        )

    def __members_shifts_get_http_params(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int,
        take: int,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для методов members_shifts_get.
        """
        if isinstance(clock_in_from, datetime):
            clock_in_from = clock_in_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(clock_in_to, date):
            clock_in_to = clock_in_to.strftime('%Y-%m-%dT%H:%M:%S')
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/members/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'clockInFrom': clock_in_from,
                    'clockInTo': clock_in_to,
                    'to': clock_in_to,
                    'staff_ids': ','.join(
                        str(s_id).replace("-", "") for s_id in staff_ids
                    ) if staff_ids else None,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __members_shifts_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода members_shifts_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.STAFF_SHIFTS_READ,
                DodoISScopes.USER_ROLE_READ,
            },
        )
