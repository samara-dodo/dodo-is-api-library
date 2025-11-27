"""
Раздел документации "API → Авторизация".
"""

import base64
import hashlib
from http import HTTPStatus
import secrets
from typing import (
    Any,
    Callable,
)

from dodo_is_api_library.utils.http_client import HttpMethods
from dodo_is_api_library.utils.http_client import (
    HttpClient,
    HttpContentType,
    HttpMethods,
)


class ApiOAuth:
    """
    Раздел документации "OAuth".
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        get_user_data: Callable,
        update_user_data: Callable,
        redirect_uri: str,
        raise_http_exception: Callable,
        base_url: str,
    ):
        self.__client_id: str = client_id
        self.__client_secret: str = client_secret
        self.__get_user_data: Callable = get_user_data
        self.__update_user_data: Callable = update_user_data
        self.__redirect_uri: str = redirect_uri
        self.__raise_http_exception: Callable = raise_http_exception
        self.__base_url: str = base_url

    async def get_auth_url(
        self,
        user_data: dict[str, Any] | None = None,
        user_id: int | str | None = None,
        user_ip: str | None = None,
        override_redirect_uri: str | None = None,
    ) -> str:
        """
        Возвращает ссылку для авторизации в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881

        Аргументы:
            user_data [dict[str, Any] | None]: данные пользователя
            user_id [int | str | None]: уникальный идентификатор пользователя в приложении
            user_ip [str | None]: ip-адрес пользователя
            override_redirect_uri [str]: ссылка для редиректа с DodoIS после успешной авторизации

        Если передан user_data, он обязательно должен иметь ключи:
            - scopes [Iterable[str]] - список scope-ов для доступа к DodoIS API
        Иначе - user_data будет получен из функции get_user_data.

        Если передан override_redirect_uri - он будет использован вместо
        redirect_uri, который был передан при инициализации класса DodoISApi.

        Ввиду того, что этот метод используется для авторизации указание ID
        пользователя в базе данных может быть невозможно. Для этого случая
        предусмотрен аргумент user_ip, который ожидает ip-адрес пользователя.

        В общем случае, в user_ip можно передавать строку любого содержания
        и назначения, этот аргумент служит только как дополнительный уникальный
        ключ для сохранения code_verifier и code_challenge кодов в приложении
        с привязкой к пользователю, которые потребуются для получения токена
        авторизации в методе get_auth_token_data.
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id, user_ip=user_ip)
        code_verifier, code_challenge = self.__generate_oauth_pkce_code_pair()
        await self.__update_user_data(
            user_id=user_id,
            user_ip=user_ip,
            user_data={
                "code_verifier": code_verifier,
                "code_challenge": code_challenge,
            },
        )
        return (
            f"{self.__base_url}/authorize?"
            f"client_id={self.__client_id}&"
            f"scope={' '.join(user_data['scopes'])}&"
            f"response_type=code&"
            f"redirect_uri={override_redirect_uri or self.__redirect_uri}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256"
        )

    async def handle_auth_callback(
        self,
        code: str,
        user_data: dict[str, Any] | None = None,
        user_id: int | str | None = None,
        user_ip: str | None = None,
        override_redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        """
        Принимает код авторизации в DodoIS, обменивает его на Access и Refresh токены
        и сохраняет их в сервисе.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881

        Аргументы:
            user_data [dict[str, Any] | None]: данные пользователя
            user_id [int | str | None]: уникальный идентификатор пользователя в приложении
            user_ip [str | None]: ip-адрес пользователя
            override_redirect_uri [str]: ссылка для редиректа с DodoIS после успешной авторизации

        Если передан user_data, он обязательно должен иметь ключи:
            - code_verifier [str] - код подтверждения
            - scopes [Iterable[str]] - список scope-ов для доступа к DodoIS API
        Иначе - user_data будет получен из функции get_user_data.

        Если передан override_redirect_uri - он будет использован вместо
        redirect_uri, который был передан при инициализации класса DodoISApi.

        Ввиду того, что этот метод используется для авторизации указание ID
        пользователя в базе данных может быть невозможно. Для этого случая
        предусмотрен аргумент user_ip, который ожидает ip-адрес пользователя.

        В общем случае, в user_ip можно передавать строку любого содержания
        и назначения, этот аргумент служит только как дополнительный уникальный
        ключ для получения code_verifier кода в приложении с привязкой к пользователю.
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id, user_ip=user_ip)
        status_, data, _ = await HttpClient.send_request(
            **self.__handle_auth_callback_http_params(
                code=code,
                user_data=user_data,
                override_redirect_uri=override_redirect_uri,
            ),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        await self.__update_user_data(
            user_id=user_id,
            user_data={
                "access_token": data["access_token"],
                # INFO. Запрос может не содержать scope на получение Refresh токена.
                "refresh_token": data.get("refresh_token"),
            },
        )
        return data

    def __handle_auth_callback_http_params(
        self,
        code: str,
        user_data: dict[str, Any],
        override_redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для refresh_token_pair_post."""
        return {
            "method": HttpMethods.POST,
            "url": f"{self.__base_url}/token",
            "data": {
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": user_data["code_verifier"],
                "scope": " ".join(user_data["scopes"]),
                "redirect_uri": override_redirect_uri or self.__redirect_uri,
            },
            "headers": {"Content-Type": HttpContentType.APPLICATION_X_WWW_FORM_URLENCODED},
        }

    async def refresh_token_pair_post(
        self,
        user_id: Any,
        user_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Обновляет Access и Refresh токены по Refresh токену.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881

        Аргументы:
            user_data [dict[str, Any] | None]: данные пользователя
            user_id [int | str | None]: уникальный идентификатор пользователя в приложении

        Если передан user_data, он обязательно должен иметь ключи:
            - refresh_token [str] - JWT токен обновления в DodoIS API
        Иначе - user_data будет получен из функции get_user_data.
        """
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        status_, data, _ = await HttpClient.send_request(
            **self.__refresh_token_pair_post_http_params(user_data=user_data),
        )
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        await self.__update_user_data(
            user_id=user_id,
            user_data={
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            },
        )
        return data

    def __refresh_token_pair_post_http_params(
        self,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для refresh_token_pair_post."""
        return {
            "method": HttpMethods.POST,
            "url": f"{self.__base_url}/token",
            "data": {
                "client_id": self.__client_id,
                "client_secret": self.__client_secret,
                "grant_type": "refresh_token",
                "refresh_token": user_data["refresh_token"],
            },
            "headers": {"Content-Type": HttpContentType.APPLICATION_X_WWW_FORM_URLENCODED},
        }

    async def user_profile_get(
        self,
        user_data: dict[str, Any] | None = None,
        user_id: int | str | None = None,
    ) -> dict[str, Any]:
        """
        Возвращает данные пользователя в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881

        Аргументы:
            user_data [dict[str, Any] | None]: данные пользователя
            user_id [int | str | None]: уникальный идентификатор пользователя в приложении

        Если передан user_data, он обязательно должен иметь ключи:
            - access_token [str] - JWT токен доступа к DodoIS API
        Иначе - user_data будет получен из функции get_user_data.
        """
        # TODO. Вынести в общие методы.
        if user_data is None:
            user_data = await self.__get_user_data(user_id=user_id)
        status_, data, _ = await HttpClient.send_request(
            **self.__user_profile_get_http_params(user_data=user_data),
        )
        # TODO. Вынести в общие методы.
        if status_ != HTTPStatus.OK:
            self.__raise_http_exception(
                status_code=status_,
                detail=data,
            )
        return data

    def __user_profile_get_http_params(
        self,
        user_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Возвращает параметры HTTP запроса для user_profile_get."""
        return {
            'method': HttpMethods.GET,
            'url': f"{self.__base_url}/userinfo",
            'headers': {"Authorization": f"Bearer {user_data["access_token"]}"},
        }

    def __generate_oauth_pkce_code_pair(
        self,
        length: int = 56,
    ) -> tuple[str, str]:
        """
        Генерирует пару кодов: code_verifier и code_challenge.
        """
        code_verifier: str = secrets.token_urlsafe(length)[:length]
        digest: bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        code_challenge: str = (
            base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")
        )
        return code_verifier, code_challenge
