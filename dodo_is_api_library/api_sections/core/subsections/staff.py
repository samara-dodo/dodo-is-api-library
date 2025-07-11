"""
Раздел документации "Команда".
"""

from datetime import (
    date,
    datetime,
)
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
from dodo_is_api_library.utils.scopes import DodoISScopes

client: HttpClient = HttpClient()


class ApiStaff():
    """
    Раздел документации "Команда".
    """

    def __init__(
        self,
        get_user_data: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__base_url: str = base_url

    # Смены сотрудников (по пиццериям)

    async def shifts_get(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str | UUID],
        staff_type_name: str | None = None,
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

        Query параметры:
            - clock_in_from [str | datetime]: начало периода, в который попадает начало смен, в формате ISO 8601 (2022-01-01T11:00:00)
            - clock_in_to [str | date]: конец периода, в который попадает начало смен, в формате ISO 8601 (2022-01-02)
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - staff_type_name [str]: фильтр по типу сотрудника
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к query параметрам:
            - в units можно перечислить до 30 заведений в одном запросе
            - в units следует перечислять UUID-ы строго через запятую без пробелов
            - в units следует перечислять UUID-ы без разделителя "-" между их частям
            - from должен быть меньше, чем to

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса
            - shift supervisor - менеджер смены
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id=user_id)
        self.__shifts_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_async_request(**self.__shifts_get_args(user_data['access_token'], clock_in_from, clock_in_to, units, staff_type_name, skip, take))

    def __shifts_get_args(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        units: list[str],
        staff_type_name: str | None = None,
        skip: int = 0,
        take: int = 100,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для метода shifts_get.
        """
        if isinstance(clock_in_from, datetime):
            clock_in_from: str = clock_in_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(clock_in_to, date):
            clock_in_to: str = clock_in_to.strftime('%Y-%m-%d')

        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/staff/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'clockInFrom': clock_in_from,
                    'clockInTo': clock_in_to,
                    'units': ','.join(str(u).replace("-", "") for u in units) if units else None,
                    'staffTypeName': staff_type_name,
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
            required_scopes={DodoISScopes.STAFF_SHIFTS_READ, DodoISScopes.USER_ROLE_READ},
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

        Query параметры:
            - clock_in_from [str | datetime]: начало периода, в который попадает начало смен, в формате ISO 8601 (2022-01-01T11:00:00)
            - clock_in_to [str | date]: конец периода, в который попадает начало смен, в формате ISO 8601 (2022-01-02)
            - staff_ids [Iterable[str | UUID]]: идентификаторы сотрудников в формате UUID
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к query параметрам:
            - В staff_ids можно перечислить до 30 сотрудников в одном запросе
            - в staff_ids следует перечислять UUID-ы строго через запятую без пробелов
            - в staff_ids следует перечислять UUID-ы без разделителя "-" между их частям

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса
            - shift supervisor - менеджер смены
        """
        user_data: dict[str, Any] = await self.__get_user_data(user_id=user_id)
        self.__members_shifts_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_async_request(**self.__members_shifts_get_args(user_data['access_token'], clock_in_from, clock_in_to, staff_ids, skip, take))

    def __members_shifts_get_args(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int = 0,
        take: int = 100,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для методов members_shifts_get.
        """
        if isinstance(clock_in_from, datetime):
            clock_in_from: str = clock_in_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(clock_in_to, date):
            clock_in_to: str = clock_in_to.strftime('%Y-%m-%dT%H:%M:%S')

        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/staff/members/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'clockInFrom': clock_in_from,
                    'clockInTo': clock_in_to,
                    'to': clock_in_to,
                    'staff_ids': ','.join(str(s_id).replace("-", "") for s_id in staff_ids) if staff_ids else None,
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
            required_scopes={DodoISScopes.STAFF_SHIFTS_READ, DodoISScopes.USER_ROLE_READ},
        )
