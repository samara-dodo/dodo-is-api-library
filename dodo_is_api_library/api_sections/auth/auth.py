"""
Раздел документации "Auth".
"""

from http import HTTPStatus
from typing import (
    Any,
    Callable,
)

from dodo_is_api_library.utils.http_client import HttpMethods
from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpMethods,
)
from dodo_is_api_library.utils.scopes import DodoISScopes


class ApiAuth:
    """
    Раздел документации "Auth".
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


    async def roles_list_get(
        self,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Auth → Список ролей

        Возвращает список всех существующих ролей пользователей.

        Документация: https://docs.dodois.io/docs/auth/ee3cd76b10a13-auth-spisok-rolej
        URL: https://api.dodois.io/auth/roles/list

        Необходимы scopes:
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__roles_list_get_validate_scopes(user_data=user_data)
        status_, data, _ = await HttpClient.send_request(
            **self.__roles_list_get_http_params(user_data=user_data),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        return data

    def __roles_list_get_http_params(
        self,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для roles_list_get."""
        return {
            "method": HttpMethods.GET,
            "url": f"{self.__base_url}/roles/list",
            "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
        }

    def __roles_list_get_validate_scopes(
        self,
        user_data: dict[str, Any],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_data['scopes'],
            required_scopes={DodoISScopes.USER_ROLE_READ},
        )

    async def roles_units_get(
        self,
        user_id: Any = None,
        user_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Auth → Юниты пользователя

        Возвращает список юнитов (пиццерий, или других заведений в рамках
        концепции бизнеса) доступных пользователю, от имени которого
        делается запрос, с указанием доступных ролей в каждом из этих юнитов.

        Документация: https://docs.dodois.io/docs/auth/1e28e79cbde05-auth-yunity-polzovatelya
        URL: https://api.dodois.io/auth/roles/units

        Необходимы scopes:
            - user.role:read - роли и юниты пользователя
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        self.__roles_units_get_validate_scopes(user_data=user_data)
        status_, data, _ = await HttpClient.send_request(
            **self.__roles_units_get_http_params(user_data=user_data),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        return data

    def __roles_units_get_http_params(
        self,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для roles_units_get."""
        return {
            "method": HttpMethods.GET,
            "url": f"{self.__base_url}/roles/units",
            "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
        }

    def __roles_units_get_validate_scopes(
        self,
        user_data: dict[str, Any],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        DodoISScopes.validate_scopes(
            user_scopes=user_data['scopes'],
            required_scopes={DodoISScopes.USER_ROLE_READ},
        )
