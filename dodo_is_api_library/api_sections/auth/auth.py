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
    HttpMethods,
)

client: HttpClient = HttpClient()


class ApiAuth():
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
        base_url: str,
    ):
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.redirect_uri: str = redirect_uri
        self.__get_user_data: Callable = get_user_data
        self.__set_user_data: Callable = set_user_data
        self.__base_url: str = base_url

    # OAuth авторизация.

    async def get_auth_url(
        self,
        user_id: Any,
    ) -> str:
        """
        Возвращает ссылку для авторизации в DodoIS.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.__get_user_data(user_id)
        code_verifier, code_challenge = self.__generate_oauth_pkce_code_pair()
        await self.__set_user_data(user_id=user_id, code_verifier=code_verifier, code_challenge=code_challenge)
        return (
            f'{self.__base_url}/connect/authorize?'
            f'client_id={self.client_id}&'
            f'scope={" ".join(user_data['scopes'])}&'
            f'response_type=code&'
            f'redirect_uri={self.redirect_uri}&'
            f'code_challenge={code_challenge}&'
            f'code_challenge_method=S256'
        )

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
        user_data: dict[str, Any] = await self.__get_user_data(user_id)
        status_, data, _ = await client.send_async_request(
            method=HttpMethods.POST,
            url=f'{self.__base_url}/connect/token',
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': code,
                'code_verifier': user_data['code_verifier'],
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
        await self.__set_user_data(
            user_id=user_id,
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            code_verifier=None,
            code_challenge=None,
        )

    async def refresh_token_pair_post(
        self,
        user_id: Any,
    ):
        """
        Обновляет Access и Refresh токены по Refresh токену.

        Документация: https://buildin.ai/share/f5caf1a5-e60e-48a2-8eab-157cec5d9881
        """
        user_data: dict[str, Any] = await self.__get_user_data(user_id=user_id)
        status_, data, _ = await client.send_async_request(
            **self.__update_refresh_token_pair_post_args(refresh_token=user_data['refresh_token']),
        )
        if status_ != HTTPStatus.OK.value:  # 200
            raise Exception(
                f'Error refreshing Access token from DodoIS with status "{status_}"!\n'
                f'Response data: {data}',
            )
        await self.__set_user_data(
            user_id=user_id,
            access=data['access_token'],
            refresh=data['refresh_token'],
        )

    def __generate_oauth_pkce_code_pair(
        self,
        length: int = 56,
    ) -> tuple[str, str]:
        """
        Генерирует пару кодов: code_verifier и code_challenge.
        """
        code_verifier: str = secrets.token_urlsafe(length)[:length]
        digest: bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge: str = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
        return code_verifier, code_challenge

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
