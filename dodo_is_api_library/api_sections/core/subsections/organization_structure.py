"""
Раздел документации "Оргструктура".
"""

from datetime import datetime
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Iterable,
)
from uuid import UUID

from dodo_is_api_library.utils.converter import (
    convert_datetime_to_str,
    convert_uuid_to_str,
)
from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.scopes import DodoISScopes


class ApiOrganizationStructure:
    """
    Раздел документации "Оргструктура".
    """

    def __init__(
        self,
        get_user_data: Callable,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__get_user_data: Callable = get_user_data
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = f"{base_url}/organization-structure"

    # Список юрлиц

    async def legal_entities_get(
        self,
        modified_at: str | datetime | None = None,
        type_ids: list[str | UUID] | None = None,
        skip: int = 0,
        take: int = 1000,
        take_all: bool = False,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Оргструктура → Список юрлиц

        Возвращает список юрлиц, отсортированный по ID.

        Документация: https://docs.dodois.io/docs/dodo-is/064bf6a8adf46-orgstruktura-spisok-yurlicz
        URL: https://api.dodois.io/dodopizza/ru/organization-structure/legal-entities

        Для получения данных необходимо указывать параметр skip,
        смещая его на количество уже полученных записей. Повторять до тех пор,
        пока не будет достигнут конец списка (isEndOfListReached = true).

        Аргументы:
            - modified_at [str | datetime | None]: дата и время изменения в формате ISO 8601 (2011-08-01T18:31:42).
                                                   Фильтр возвращает записи у которых дата изменения больше или равна переданной
            - type_ids [list[str | UUID] | None]: список id (hex UUID) типов юрлиц
            - skip [int]: количество записей, которые следует пропустить
            - take [int]: количество записей, которые следует выбрать
            - take_all [bool]: признак, что нужно получить все записи из API

        Требования к аргументам:
            - если take_all=True, то take будет проигнорирован

        Требования к scopes:
            - organizationstructure - оргструктура
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__legal_entities_get_validate_scopes(user_scopes=user_data['scopes'])
        http_data: list[dict[str, Any]] = self.__legal_entities_get_http_params(
            access_token=user_data['access_token'],
            modified_at=modified_at,
            type_ids=type_ids,
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
            return_data.extend(data["legalEntities"])
            if data['isEndOfListReached'] or not take_all:
                return return_data
            else:
                http_data['query_params']['skip'] += http_data['query_params']['take']

    def __legal_entities_get_http_params(
        self,
        access_token: str,
        modified_at: str | datetime | None,
        type_ids: list[str | UUID] | None,
        skip: int,
        take: int,
        take_all: bool,
    ) -> list[dict[str, Any]]:
        """
        Возвращает параметры HTTP запроса для legal_entities_get.
        """
        if take_all:
            skip = 0
            take = 1000
        if modified_at:
            modified_at: str = convert_datetime_to_str(modified_at)
        if type_ids:
            type_ids: list[str] = [convert_uuid_to_str(i) for i in type_ids]
        return {
            'method': HttpMethods.GET,
            'url': f'{self.__base_url}/legal-entities',
            'query_params': {
                k: v
                for k, v
                in {
                    'modifiedAt': modified_at,
                    'typeIds': ",".join(type_ids) if type_ids else None,
                    'skip': skip,
                    'take': take,
                }.items()
                if v is not None
            },
            'headers': {'Authorization': f'Bearer {access_token}'},
        }

    def __legal_entities_get_validate_scopes(
        self,
        user_scopes: Iterable[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes для метода legal_entities_get.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_scopes,
            required_scopes={
                DodoISScopes.ORGANIZATIONSTRUCTURE,
            },
        )
