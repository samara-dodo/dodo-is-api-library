"""
Модуль обращения к эндпоинтам DodoIS.
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
from http import HTTPStatus

from utils.http_client import (
    HttpClient,
    HttpMethods,
)

client: HttpClient = HttpClient()


class DodoISScopes:
    """
    Класс представления DodoIS Scopes.
    """

    OPENID = 'openid'                        # токен доступа
    SALES = 'sales'                          # продажи
    STAFF_SHIFTS_READ = 'staffshifts:read'   # смены сотрудников / персонала, доступ на чтение
    USER_ROLE_READ = 'user.role:read'        # роли и юниты пользователя, доступ на чтение


class DodoISApi:
    """
    Класс обращения к эндпоинтам DodoIS.

    Используется в приложениях со способом авторизации "Authorization Code flow".

    Аргументы:
        client_id: str
            Идентификатор приложения в магазине приложений
        client_secret: str
            Секрет приложения в магазине приложений
        code_challenge: str
            Случайная код-строка, можно сгенерировать в https://example-app.com/pkce
        code_verifier: str
            Верификатор код-строки (стандарт PKCE (S256)), можно сгенерировать в https://example-app.com/pkce
        get_user_data: Callable
            Функция получения данных пользователя из сервиса
        set_user_data: Callable
            Функция сохранения данных пользователя в сервисе
        redirect_uri: str = 'https://localhost:5001/'
            URI для перенаправления после успешной авторизации в DodoIS
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        # TODO. Убрать их в данные пользователя.
        code_challenge: str,
        code_verifier: str,
        # ENDTODO.
        get_user_data: Callable,
        set_user_data: Callable,
        redirect_uri: str = 'https://localhost:5001/',
    ):
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.code_challenge: str = code_challenge
        self.code_verifier: str = code_verifier
        self.get_user_data: Callable = get_user_data
        self.set_user_data: Callable = set_user_data
        self.redirect_uri: str = redirect_uri
        self.__base_url: str = 'https://api.dodois.io/dodopizza/ru'

    # Аутентификация

    # TODO. Добавить синхронный вызов.
    async def get_auth_url(
        self,
        user_id: Any,
    ) -> str:
        """
        Возвращает ссылку для авторизации в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id)
        return (
            f'{self.__base_url}/connect/authorize?'
            f'client_id={self.client_id}&'
            f'scope={" ".join(user_data['scopes'])}&'
            f'response_type=code&'
            f'redirect_uri={self.redirect_uri}&'
            f'code_challenge={self.code_challenge}&'
            f'code_challenge_method=S256'
        )

    # TODO. Добавить синхронный вызов.
    async def handle_auth_callback(
        self,
        user_id: Any,
        code: str,
    ):
        """
        Принимает код авторизации в DodoIS, обменивает его на Access и Refresh токены
        и сохраняет их в сервисе.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id)
        status_, data, _ = await client.send_async_request(
            method=HttpMethods.POST,
            url=f'{self.__base_url}/connect/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'code_verifier': self.code_verifier,
                'scope': user_data['scopes'],
                'redirect_uri': self.redirect_uri,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        if status_ != HTTPStatus.OK.value:  # 200
            raise Exception(
                f'Error getting auth token data from DodoIS with status "{status_}"!\n'
                f'Response data: {data}',
            )
        await self.set_user_data(
            user_id=user_id,
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
        )

    def refresh_token_pair_post(
        self,
        user_id: Any,
    ):
        """
        Смотри описание "refresh_token_pair_post_async".
        """
        user_data: dict[str, Any] = self.get_user_data(user_id=user_id)
        status_, data, _ = client.send_sync_request(
            **self.__update_refresh_token_pair_post_args(refresh_token=user_data['refresh_token']),
        )
        if status_ != HTTPStatus.OK.value:  # 200
            raise Exception(
                f'Error refreshing Access token from DodoIS with status "{status_}"!\n'
                f'Response data: {data}',
            )
        self.set_user_data(
            user_id=user_id,
            access=data['access_token'],
            refresh=data['refresh_token'],
        )

    async def refresh_token_pair_post_async(
        self,
        user_id: Any,
    ):
        """
        Обновляет Access и Refresh токены по Refresh токену.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id=user_id)
        status_, data, _ = await client.send_async_request(
            **self.__update_refresh_token_pair_post_args(refresh_token=user_data['refresh_token']),
        )
        if status_ != HTTPStatus.OK.value:  # 200
            raise Exception(
                f'Error refreshing Access token from DodoIS with status "{status_}"!\n'
                f'Response data: {data}',
            )
        await self.set_user_data(
            user_id=user_id,
            access=data['access_token'],
            refresh=data['refresh_token'],
        )

    def __update_refresh_token_pair_post_args(
        self,
        refresh_token: str,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для методов update_access_token_post_*.
        """
        return {
            'method': HttpMethods.POST,
            'url': f'{self.__base_url}/connect/token',
            'data': {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            },
            'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
        }

    # Учёт, производство, доставка, команда

    ## Команда

    ### Смены сотрудников (по идентификаторам)

    def komanda_smeny_sotrudnikov_po_identifikatoram_get(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
    ) -> tuple[int, dict, dict]:
        """
        Смотри описание "komanda_smeny_sotrudnikov_po_identifikatoram_get_async".
        """
        user_data: dict[str, Any] = self.get_user_data(user_id=user_id)
        self.__komanda_smeny_sotrudnikov_po_identifikatoram_get_validate_scopes(user_scopes=user_data['scopes'])
        return client.send_sync_request(**self.__komanda_smeny_sotrudnikov_po_identifikatoram_get_args(user_data['access_token'], clock_in_from, clock_in_to, staff_ids, skip, take))

    async def komanda_smeny_sotrudnikov_po_identifikatoram_get_async(
        self,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
    ) -> tuple[int, dict, dict]:
        """
        Смены сотрудников (рабочее время, рабочие часы, фактические часы):
        отработанное время с детализацией по дневным, ночным и праздничным
        часам (в минутах), данные о доставленных заказах, расстоянии,
        стаже сотрудника на момент смены.

        Документация: https://docs.dodois.io/docs/dodo-is/9eeef5b727118-komanda-smeny-sotrudnikov-po-identifikatoram

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
        user_data: dict[str, Any] = await self.get_user_data(user_id=user_id)
        self.__komanda_smeny_sotrudnikov_po_identifikatoram_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_async_request(**self.__komanda_smeny_sotrudnikov_po_identifikatoram_get_args(user_data['access_token'], clock_in_from, clock_in_to, staff_ids, skip, take))

    def __komanda_smeny_sotrudnikov_po_identifikatoram_get_args(
        self,
        access_token: str,
        clock_in_from: str | datetime,
        clock_in_to: str | date,
        staff_ids: list[str | UUID],
        skip: int = 0,
        take: int = 100,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для методов komanda_smeny_sotrudnikov_po_identifikatoram_get_*.
        """
        if isinstance(clock_in_from, datetime):
            clock_in_from: str = clock_in_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(period_to, date):
            period_to: str = period_to.strftime('%Y-%m-%dT%H:%M:%S')

        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/staff/members/shifts',
            'query_params': {
                k: v
                for k, v
                in {
                    'clockInFrom': clock_in_from,
                    'clockInTo': clock_in_to,
                    'to': period_to,
                    'staff_ids': ','.join(str(s_id).replace("-", "") for s_id in staff_ids) if staff_ids else None,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __komanda_smeny_sotrudnikov_po_identifikatoram_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        self.__validate_scopes(
            user_scopes=user_scopes,
            required_scopes={DodoISScopes.STAFF_SHIFTS_READ, DodoISScopes.USER_ROLE_READ},
        )

    ### Смены сотрудников (по пиццериям)

    def komanda_smeny_sotrudnikov_po_picceriyam_get(
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
        Смотри описание "komanda_smeny_sotrudnikov_po_picceriyam_get_async".
        """
        user_data: dict[str, Any] = self.get_user_data(user_id=user_id)
        self.__komanda_smeny_sotrudnikov_po_picceriyam_get_validate_scopes(user_scopes=user_data['scopes'])
        return client.send_sync_request(**self.__komanda_smeny_sotrudnikov_po_picceriyam_get_args(user_data['access_token'], clock_in_from, clock_in_to, units, staff_type_name, skip, take))

    async def komanda_smeny_sotrudnikov_po_picceriyam_get_async(
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
        Смены сотрудников (рабочее время, рабочие часы, фактические часы):
        отработанное время с детализацией по дневным, ночным и праздничным часам
        (в минутах), данные о доставленных заказах, расстоянии,
        стаже сотрудника на момент смены.

        Документация: https://docs.dodois.io/docs/dodo-is/16c2ad8c8d1eb-komanda-smeny-sotrudnikov-po-piczczeriyam

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
        self.__komanda_smeny_sotrudnikov_po_picceriyam_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_async_request(**self.__komanda_smeny_sotrudnikov_po_picceriyam_get_args(user_data['access_token'], clock_in_from, clock_in_to, units, staff_type_name, skip, take))

    def __komanda_smeny_sotrudnikov_po_picceriyam_get_args(
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
        Возвращает аргументы для методов komanda_smeny_sotrudnikov_po_picceriyam_get_*.
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

    def __komanda_smeny_sotrudnikov_po_picceriyam_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        self.__validate_scopes(
            user_scopes=user_scopes,
            required_scopes={DodoISScopes.STAFF_SHIFTS_READ, DodoISScopes.USER_ROLE_READ},
        )

    ## Учет

    ### Учет -> Продажи

    def uchet_prodazhi_get(
        self,
        period_from: str | datetime,
        period_to: str | datetime,
        units: Iterable[str | UUID],
        orderSource: str | None = None,
        salesChannel: str | None = None,
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
    ) -> tuple[int, dict, dict]:
        """
        Смотри описание "prodazhi_get_async".
        """
        user_data: dict[str, Any] = self.get_user_data(user_id=user_id)
        self.__uchet_prodazhi_get_validate_scopes(user_scopes=user_data['scopes'])
        return client.send_sync_request(**self.__uchet_prodazhi_get_args(user_data['access_token'], orderSource, period_from, period_to, units, salesChannel, skip, take))

    async def uchet_prodazhi_get_async(
        self,
        period_from: str | datetime,
        period_to: str | datetime,
        units: Iterable[str | UUID],
        order_source: str | None = None,
        sales_channel: str | None = None,
        skip: int = 0,
        take: int = 100,
        user_id: Any = None,
    ) -> tuple[int, dict, dict]:
        """
        Возвращает продажи за указанный период (включительно),
        отсортированные по дате и идентификатору продажи.

        Документация: https://docs.dodois.io/docs/dodo-is/5cdae1cb7443f-uchyot-prodazhi

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей. Повторять до тех пор,
        пока не будет достигнут конец списка (isEndOfListReached = true).

        Query параметры:
            - period_from [str | datetime]: начало периода в формате ISO 8601 (2011-08-01T18:31:42)
            - period_to [str | datetime]: конец периода в формате ISO 8601 (2011-09-02T19:21:53)
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - order_source [str]: источник заказа (CallCenter / Website / Dine-in / MobileApp / Manager / Aggregator / Kiosk)
            - sales_channel [str]: канал продаж (Dine-in / Takeaway / Delivery)
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к query параметрам:
            - в units можно перечислить до 30 заведений в одном запросе
            - в units следует перечислять UUID-ы строго через запятую без пробелов
            - в units следует перечислять UUID-ы без разделителя "-" между их частями
            - from должен быть меньше, чем to
            - диапазон дат между to и from параметрами не должен превышать 31 день

        Доступно для следующих ролей:
            - division administrator - Администратор подразделения
            - store Manager - Менеджер офиса
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id=user_id)
        self.__uchet_prodazhi_get_validate_scopes(user_scopes=user_data['scopes'])
        return await client.send_async_request(**self.__uchet_prodazhi_get_args(user_data['access_token'], order_source, period_from, period_to, units, sales_channel, skip, take))

    def __uchet_prodazhi_get_args(
        self,
        access_token: str,
        period_from: str | datetime,
        period_to: str | datetime,
        units: Iterable[str],
        order_source: str | None = None,
        sales_channel: str | None = None,
        skip: int = 0,
        take: int = 100,
    ) -> dict[str, Any]:
        """
        Возвращает аргументы для методов prodazhi_get_*.
        """
        if isinstance(period_from, datetime):
            period_from: str = period_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(period_to, datetime):
            period_to: str = period_to.strftime('%Y-%m-%dT%H:%M:%S')
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/accounting/sales',
            'query_params': {
                k: v
                for k, v
                in {
                    'orderSource': order_source,
                    'from': period_from,
                    'to': period_to,
                    'units': ','.join(u.replace("-", "") for u in units) if units else None,
                    'salesChannel': sales_channel,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __uchet_prodazhi_get_validate_scopes(
        self,
        user_scopes: list[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        self.__validate_scopes(
            user_scopes=user_scopes,
            required_scopes={DodoISScopes.SALES, DodoISScopes.USER_ROLE_READ},
        )

    # Общий функционал.

    def __validate_scopes(
        self,
        user_scopes: Iterable[str],
        required_scopes: set[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        missed_scopes: set[str] = required_scopes - set(user_scopes)
        if missed_scopes:
            raise ValueError(f'У пользователя отсутсвуют обязательные scopes: {", ".join(missed_scopes)}')
