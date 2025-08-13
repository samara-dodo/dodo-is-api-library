import base64
import hashlib
from http import HTTPStatus
from httpx._exceptions import HTTPError
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


class ApiAuth:
    """
    Раздел документации "Auth".
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        get_user_data: Callable,
        set_user_data: Callable,
        redirect_uri: str,
    ):
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.get_user_data: Callable = get_user_data
        self.set_user_data: Callable = set_user_data
        self.redirect_uri: str = redirect_uri

        # Заполняются автоматически.
        self.__base_url: str = "https://auth.dodois.io"

    # OAuth авторизация.

    async def get_auth_url(
        self,
        user_id: int | str | None = None,
        user_ip: str | None = None,
    ) -> str:
        """
        Возвращает ссылку для авторизации в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(
            user_id=user_id,
            user_ip=user_ip,
        )
        code_verifier, code_challenge = self.__generate_oauth_pkce_code_pair()
        user_data.update(
            {
                "code_verifier": code_verifier,
                "code_challenge": code_challenge,
            },
        )
        await self.set_user_data(
            user_id=user_id,
            user_ip=user_ip,
            user_data=user_data,
        )
        return (
            f"{self.__base_url}/connect/authorize?"
            f"client_id={self.client_id}&"
            f"scope={' '.join(user_data['scopes'])}&"
            f"response_type=code&"
            f"redirect_uri={self.redirect_uri}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256"
        )

    async def get_auth_token_data(
        self,
        code: str,
        user_ip: str,
        user_id: int | str | None = None,
    ) -> dict[str, Any]:
        """
        Возвращает данные токена авторизации в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(
            user_id=user_id,
            user_ip=user_ip,
        )
        status_, data, _ = await HttpClient.send_request(
            method=HttpMethods.POST,
            url=f"{self.__base_url}/connect/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": user_data["code_verifier"],
                "scope": " ".join(user_data["scopes"]),
                "redirect_uri": self.redirect_uri,
            },
            headers={"Content-Type": HttpContentType.APPLICATION_X_WWW_FORM_URLENCODED},
        )
        if status_ != HTTPStatus.OK:
            raise HTTPError(
                message=(
                    f"Error getting auth token data from DodoIS with status {status_}. "
                    f"Response data: {data}"
                ),
            )
        return data

    async def get_user_profile(
        self,
        access_token: str,
    ) -> dict[str, Any]:
        """
        Возвращает данные пользователя в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        status_, data, _ = await HttpClient.send_request(
            method=HttpMethods.GET,
            url=f"{self.__base_url}/connect/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if status_ != HTTPStatus.OK:
            raise HTTPError(
                message=(
                    f"Error getting user profile from DodoIS with status {status_}. "
                    f"Response data: {data}"
                ),
            )
        return data

    async def handle_auth_callback(
        self,
        code: str,
        user_id: Any = None,
        user_ip: str | None = None,
    ):
        """
        Принимает код авторизации в DodoIS, обменивает его на Access и Refresh токены
        и сохраняет их в сервисе.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(
            user_id=user_id,
            user_ip=user_ip,
        )
        status_, data, _ = await HttpClient.send_request(
            method=HttpMethods.POST,
            url=f"{self.__base_url}/connect/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": user_data["code_verifier"],
                "scope": user_data["scopes"],
                "redirect_uri": self.redirect_uri,
            },
            headers={"Content-Type": HttpContentType.APPLICATION_X_WWW_FORM_URLENCODED},
        )
        if status_ != HTTPStatus.OK:
            raise HTTPError(
                message=(
                    f'Error getting auth token data from DodoIS with status "{status_}"!\n'
                    f"Response data: {data}",
                ),
            )
        user_data.update(
            {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            },
        )
        await self.set_user_data(
            user_id=user_id,
            user_data=user_data,
        )

    async def refresh_token_pair_post(
        self,
        user_id: Any,
    ):
        """
        Обновляет Access и Refresh токены по Refresh токену.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.get_user_data(user_id=user_id)
        status_, data, _ = await HttpClient.send_request(
            method=HttpMethods.POST,
            url=f"{self.__base_url}/connect/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": user_data["refresh_token"],
            },
            headers={"Content-Type": HttpContentType.APPLICATION_X_WWW_FORM_URLENCODED},
        )
        if status_ != HTTPStatus.OK:
            raise Exception(
                f'Error refreshing Access token from DodoIS with status "{status_}"!\n'
                f"Response data: {data}",
            )
        await self.set_user_data(
            user_id=user_id,
            access=data["access_token"],
            refresh=data["refresh_token"],
        )

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
