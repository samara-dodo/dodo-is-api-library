"""
Модуль обращения к эндпоинтам DodoIS.
"""

from typing import Callable

from dodo_is_api_library.api_sections import (
    ApiAuth,
    ApiCore,
    ApiOAuth,
    ApiMarketplace,
)
from dodo_is_api_library.utils.exceptions import raise_http_exception


class DodoISApi:
    """
    Класс обращения к эндпоинтам DodoIS.

    Используется в приложениях со способом авторизации "Authorization Code flow".

    Аргументы:
        client_id: str
            Идентификатор приложения в магазине приложений
        client_secret: str
            Секрет приложения в магазине приложений
        get_user_data: Callable
            Функция получения данных пользователя из сервиса
        update_user_data: Callable
            Функция обновления данных пользователя в сервисе
        redirect_uri: str = 'https://localhost:5001/'
            URI для перенаправления после успешной авторизации в DodoIS
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        get_user_data: Callable,
        update_user_data: Callable,
        redirect_uri: str = 'https://localhost:5001/',
        raise_http_exception: Callable = raise_http_exception,
    ):
        # Заполняются пользовательскими данными.
        self.__client_id: str = client_id
        self.__client_secret: str = client_secret
        self.__get_user_data: Callable = get_user_data
        self.__update_user_data: Callable = update_user_data
        self.__redirect_uri: str = redirect_uri
        self.__raise_http_exception: Callable = raise_http_exception

        # Заполняются автоматически.
        self.__base_url: str = 'https://api.dodois.io'
        self.__base_url_oauth: str = 'https://auth.dodois.io'

        # Расширяемые классы.
        self.auth = ApiAuth(
            get_user_data=get_user_data,
            raise_http_exception=raise_http_exception,
            base_url=f"{self.__base_url}/auth",
        )
        self.core = ApiCore(
            get_user_data=self.__get_user_data,
            raise_http_exception=raise_http_exception,
            base_url=f"{self.__base_url}/dodopizza/ru",
        )
        self.oauth = ApiOAuth(
            client_id=self.__client_id,
            client_secret=self.__client_secret,
            get_user_data=self.__get_user_data,
            update_user_data=self.__update_user_data,
            redirect_uri=self.__redirect_uri,
            raise_http_exception=self.__raise_http_exception,
            base_url=f"{self.__base_url_oauth}/connect",
        )
        self.marketplace = ApiMarketplace(
            get_user_data=self.__get_user_data,
            raise_http_exception=raise_http_exception,
            # INFO. Содержит в себе разделение по URL на две категории.
            #       Разделение происходит в ApiMarketplace.
            base_url=self.__base_url,
        )
