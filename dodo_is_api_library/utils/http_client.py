"""
Модуль обработки HTTP запросов.
"""

from typing import Any

from http import HTTPStatus
import httpx


class HttpMethods:
    """
    Класс представления HTTP методов.
    """

    # Безопасные.
    HEAD: str = "HEAD"
    GET: str = "GET"
    OPTIONS: str = "OPTIONS"
    # Небезопасные.
    DELETE: str = "DELETE"
    PATCH: str = "PATCH"
    POST: str = "POST"
    PUT: str = "PUT"

    @classmethod
    def all_safe(cls) -> tuple[str, str, str]:
        return (cls.HEAD, cls.GET, cls.OPTIONS)

    @classmethod
    def all_unsafe(cls) -> tuple[str, str, str, str]:
        return (cls.DELETE, cls.PATCH, cls.POST, cls.PUT)


class HttpContentType:
    """
    Класс представления HTTP Content-Type.
    """

    APPLICATION_JSON: str = "application/json"
    APPLICATION_X_WWW_FORM_URLENCODED: str = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA: str = "multipart/form-data"
    TEXT_PLAIN: str = "text/plain"


class HttpClient:
    """
    Класс обработки HTTP запросов.
    """

    @staticmethod
    async def send_request(
        method: str,
        url: str,
        query_params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        auth: Any = None,
        timeout_sec: int = 15,
    ) -> tuple[int, Any, dict]:
        """
        Отправляет HTTP запрос с указанными параметрами.

        Возвращает:
            - статус-код ответа
            - тело ответа
            - заголовки ответа
        """
        if method in HttpMethods.all_safe():
            pass
        elif method in HttpMethods.all_unsafe():
            if data is not None and not isinstance(data, dict):
                raise ValueError('Данные "data" должны быть dict')
            if headers is None:
                headers = {}
            headers.setdefault("Content-Type", HttpContentType.APPLICATION_JSON)
        else:
            raise ValueError(f"Метод {method} не поддерживается")

        r_headers: dict = {}
        async with httpx.AsyncClient() as client:
            try:
                r: httpx.Response = await client.request(
                    method=method,
                    url=url,
                    params=query_params,
                    data=data,
                    headers=headers,
                    auth=auth,
                    timeout=httpx.Timeout(timeout_sec),
                )
                r_status: int = r.status_code
                r_body: Any = r.json()
                r_headers = dict(r.headers)

            except httpx.ConnectError:
                r_status = HTTPStatus.BAD_GATEWAY.value  # 502
                r_body = {"error": "Соединение не установлено"}
            except (httpx.ConnectTimeout, httpx.ReadTimeout):
                r_status = HTTPStatus.GATEWAY_TIMEOUT.value  # 504
                r_body = {"error": "Превышено время ожидания соединения"}
            except httpx.LocalProtocolError as e:
                r_status = HTTPStatus.BAD_REQUEST.value  # 400
                r_body = {
                    "error": "Неправильный протокол запроса",
                    "detail": str(e),
                }
            except (httpx.RequestError, Exception) as e:
                r_status = HTTPStatus.INTERNAL_SERVER_ERROR.value  # 500
                r_body = {
                    "error": "Ошибка обработки запроса сервером",
                    "detail": str(e),
                }

        return r_status, r_body, r_headers
