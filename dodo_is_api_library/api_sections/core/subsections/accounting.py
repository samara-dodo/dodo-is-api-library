"""
Раздел документации "Учёт".
"""

from datetime import (
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
from dodo_is_api_library.utils.scopes import DodoISScopes

client: HttpClient = HttpClient()


class ApiAccounting():
    """
    Раздел документации "Учет".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = f'{base_url}/accounting'

    # Продажи

    async def sales_get(
        self,
        period_from: str | datetime,
        period_to: str | datetime,
        units: Iterable[str],
        user_id: Any,
        user_data: dict[str, Any] | None = None,
        order_source: str | None = None,
        sales_channel: str | None = None,
        skip: int = 0,
        take: int = 100,
    ) -> tuple[int, dict, dict]:
        """
        Учёт → Продажи

        Возвращает продажи за указанный период (включительно),
        отсортированные по дате и идентификатору продажи.

        Документация: https://docs.dodois.io/docs/dodo-is/5cdae1cb7443f-uchyot-prodazhi
        URL: https://api.dodois.io/dodopizza/ru/accounting/sales

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей. Повторять до тех пор,
        пока не будет достигнут конец списка (isEndOfListReached = true).

        Аргументы:
            - period_from [str | datetime]: начало периода в формате ISO 8601 (2011-08-01T18:31:42)
            - period_to [str | datetime]: конец периода в формате ISO 8601 (2011-09-02T19:21:53)
            - units [Iterable[str]]: список заведений (пиццерий) Dodo IS
            - user_id [Any]: уникальный идентификатор пользователя в базе данных сервиса
            - order_source [str]: источник заказа (CallCenter / Website / Dine-in / MobileApp / Manager / Aggregator / Kiosk)
            - sales_channel [str]: канал продаж (Dine-in / Takeaway / Delivery)
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к аргументам:
            - в units можно перечислить до 30 заведений в одном запросе
            - в units следует перечислять UUID-ы строго через запятую без пробелов
            - в units следует перечислять UUID-ы без разделителя "-" между их частями
            - from должен быть меньше, чем to
            - диапазон дат между to и from параметрами не должен превышать 31 день

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store Manager - менеджер офиса

        Требования к scopes:
            - sales - продажи
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__sales_get_validate_scopes(user_scopes=user_data['scopes'])
        status_, data, _ = await client.send_request(
            **self.__sales_get_http_params(
                access_token=user_data['access_token'],
                period_from=period_from,
                period_to=period_to,
                units=units,
                order_source=order_source,
                sales_channel=sales_channel,
                skip=skip,
                take=take,
            ),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        return data


    def __sales_get_http_params(
        self,
        access_token: str,
        period_from: str | datetime,
        period_to: str | datetime,
        units: Iterable[str | UUID],
        order_source: str | None,
        sales_channel: str | None,
        skip: int,
        take: int,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для sales_get.
        """
        if isinstance(period_from, datetime):
            period_from = period_from.strftime('%Y-%m-%dT%H:%M:%S')
        if isinstance(period_to, datetime):
            period_to = period_to.strftime('%Y-%m-%dT%H:%M:%S')
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/sales',
            'query_params': {
                k: v
                for k, v
                in {
                    'orderSource': order_source,
                    'from': period_from,
                    'to': period_to,
                    'units': ','.join(str(u).replace("-", "") for u in units),
                    'salesChannel': sales_channel,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __sales_get_validate_scopes(
        self,
        user_scopes: list[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={DodoISScopes.SALES, DodoISScopes.USER_ROLE_READ},
        )
