"""
Раздел документации "Доставка".
"""

from datetime import datetime
from typing import (
    Any,
    Callable,
    Iterable,
)
from uuid import UUID

from http import HTTPStatus

from dodo_is_api_library.utils.converter import convert_datetime_to_str
from dodo_is_api_library.utils.http_client import (
    HttpMethods,
    HttpResponseDTO,
    http_client,
)
from dodo_is_api_library.utils.scopes import DodoISScopes


class ApiDelivery():
    """Раздел документации "Доставка"."""

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = f'{base_url}/delivery'

    # TODO. Сделать раздел.
    # Статистика

    # TODO. Сделать раздел.
    # Сертификаты за опоздание

    # Заказы курьеров

    async def couriers_orders_get(
        self,
        dt_from: str | datetime,
        dt_to: str | datetime,
        units: Iterable[str | UUID],
        skip: int = 0,
        take: int = 1000,
        take_all: bool = False,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Доставка → Заказы курьеров

        Метрики по каждому заказу курьеров.

        Документация: https://docs.dodois.io/docs/dodo-is/14c586221ab77-dostavka-zakazy-kurerov
        URL: https://api.dodois.io/dodopizza/ru/delivery/couriers-orders

        Время в параметрах в возвращаемом ответе отдаётся по UTCefficiency.
        Параметры dt_from и dt_to определяют фильтрация заказов по дате их создания
        и внесенных изменений.

        Аргументы:
            - dt_from [str | datetime]: начало периода в формате ISO 8601 (2022-01-01T11:00:00)
            - dt_to [str | datetime]: конец периода в формате ISO 8601 (2022-01-02T11:00:00)
            - units [Iterable[str | UUID]]: список заведений (пиццерий) Dodo IS в формате UUID
            - staff_type [str]: фильтр по типу сотрудника
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать

        Требования к аргументам:
            - в units можно перечислить до 30 заведений в одном запросе
            - dt_from должен быть меньше, чем dt_to
            - take не может быть меньше 0 или больше 1000

        Доступно для следующих ролей:
            - division administrator - администратор подразделения
            - store manager - менеджер офиса

        Требования к scopes:
            - deliverystatistics - статистика доставки
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self._couriers_orders_get_validate_scopes(user_scopes=user_data['scopes'])
        http_data: dict[str, Any] = self._couriers_orders_get_http_params(
            access_token=user_data['access_token'],
            dt_from=dt_from,
            dt_to=dt_to,
            units=units,
            skip=skip,
            take=take,
            take_all=take_all,
        )
        return_data: list[dict[str, Any]] = []
        while 1:
            response: HttpResponseDTO = await http_client.send_request(**http_data)
            if response.status_code != HTTPStatus.OK:
                self.__raise_http_exception(
                    status_code=response.status_code,
                    detail=response.data,
                )
            return_data.extend(response.data["couriersOrders"])
            if response.data['isEndOfListReached'] or not take_all:
                break
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']
        return self._couriers_orders_get_process_data(data=return_data)

    def _couriers_orders_get_process_data(
        self,
        data: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return data

    def _couriers_orders_get_http_params(
        self,
        access_token: str,
        dt_from: str | datetime,
        dt_to: str | datetime,
        units: Iterable[str | UUID],
        skip: int,
        take: int,
        take_all: bool,
    ) -> dict[str, Any]:
        """
        Возвращает параметры HTTP запроса для _couriers_orders_get.
        """
        if take_all:
            skip = 0
            take = 1000
        if dt_from:
            dt_from = convert_datetime_to_str(dt_from)
        if dt_to:
            dt_to = convert_datetime_to_str(dt_to)
        return {
            "method": HttpMethods.GET,
            "url": f'{self.__base_url}/couriers-orders',
            "query_params": {
                k: v
                for k, v
                in {
                    "from": dt_from,
                    "to": dt_to,
                    "units": ",".join(str(u).replace("-", "") for u in units),
                    "skip": skip,
                    "take": take,
                }.items()
                if v is not None
            },
            "headers": {"Authorization": f"Bearer {access_token}"},
        }

    def _couriers_orders_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода members_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.DELIVERYSTATISTICS,
                DodoISScopes.USER_ROLE_READ,
            },
        )

    # TODO. Сделать раздел.
    # Сектора доставки

    # TODO. Сделать раздел.
    # Стоп-продажи по секторам
