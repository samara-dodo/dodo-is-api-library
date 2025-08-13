"""
Модуль обращения к эндпоинтам DodoIS.
"""

from typing import Callable

from dodo_is_api_library.api_sections import (
    ApiAuth,
    ApiCore,
)


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
        set_user_data: Callable
            Функция сохранения данных пользователя в сервисе
        redirect_uri: str = 'https://localhost:5001/'
            URI для перенаправления после успешной авторизации в DodoIS
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        get_user_data: Callable,
        set_user_data: Callable,
        redirect_uri: str = 'https://localhost:5001/',
    ):
        # Заполняются пользовательскими данными.
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.get_user_data: Callable = get_user_data
        self.set_user_data: Callable = set_user_data
        self.redirect_uri: str = redirect_uri

        # Заполняются автоматически.
        self.__base_url: str = 'https://api.dodois.io'

        # Расширяемые классы.
        self.auth = ApiAuth(
            client_id=client_id,
            client_secret=client_secret,
            get_user_data=self.get_user_data,
            set_user_data=self.set_user_data,
            redirect_uri=redirect_uri,
        )
        self.core = ApiCore(
            get_user_data=self.get_user_data,
            base_url=self.__base_url,
        )
