"""
Модуль обработки HTTP запросов.
"""

import asyncio

import anyio
from http import HTTPStatus
import anyio.from_thread
import httpx


class HttpMethods:
    """
    Класс представления HTTP методов.
    """

    # Безопасные.
    HEAD: str = 'HEAD'
    GET: str = 'GET'
    OPTIONS: str = 'OPTIONS'
    # Небезопасные.
    DELETE: str = 'DELETE'
    PATCH: str = 'PATCH'
    POST: str = 'POST'
    PUT: str = 'PUT'

    @classmethod
    def all_safe(cls) -> tuple[str]:
        return (cls.HEAD, cls.GET, cls.OPTIONS)

    @classmethod
    def all_unsafe(cls) -> tuple[str]:
        return (cls.DELETE, cls.PATCH, cls.POST, cls.PUT)


class HttpContentType:
    """
    Класс представления HTTP Content-Type.
    """

    APPLICATION_JSON: str = 'application/json'
    MULTIPART_FORM_DATA: str = 'multipart/form-data'
    TEXT_PLAIN: str = 'text/plain'


class HttpClient:
    """
    Класс обработки HTTP запросов.
    """

    def send_sync_request(
        self,
        method: str,
        url: str,
        query_params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        auth: dict | None = None,
        timeout_sec: int = 15,
    ) -> tuple[int, dict, dict]:
        """
        Отправляет HTTP запрос с указанными параметрами.

        Возвращает:
            - статус-код ответа
            - тело ответа
            - заголовки ответа
        """
        try:
            # INFO. Проверка, запущен ли event loop (например, внутри FastAPI).
            asyncio.get_running_loop()
            return anyio.from_thread.run(self.send_async_request, method, url, query_params, data, headers, auth, timeout_sec)
        except RuntimeError:
            return asyncio.run(self.send_async_request(method, url, query_params, data, headers, auth, timeout_sec))

    async def send_async_request(
        self,
        method: str,
        url: str,
        query_params: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
        auth: any = None,
        timeout_sec: int = 15,
    ) -> tuple[int, dict, dict]:
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
            headers.setdefault('Content-Type', HttpContentType.APPLICATION_JSON)
        else:
            raise ValueError(f'Метод {method} не поддерживается')

        r_headers: dict = {}
        async with httpx.AsyncClient() as client:
            try:
                r: httpx.Response = await client.request(
                    method=method,
                    url=url,
                    params=query_params,
                    json=data,
                    headers=headers,
                    auth=auth,
                    timeout=httpx.Timeout(timeout_sec),
                )
                r_status: int = r.status_code
                r_body: dict = r.json()
                r_headers: httpx.Headers = r.headers

            except httpx.ConnectError:
                r_status: dict = HTTPStatus.BAD_GATEWAY.value  # 502
                r_body: dict = {'error': 'Соединение не установлено'}
            except (httpx.ConnectTimeout, httpx.ReadTimeout):
                r_status: int = HTTPStatus.GATEWAY_TIMEOUT.value  # 504
                r_body: dict = {'error': "Превышено время ожидания соединения"}
            except httpx.LocalProtocolError as e:
                r_status: int = HTTPStatus.BAD_REQUEST.value  # 400
                r_body: dict = {
                    'error': 'Неправильный протокол запроса',
                    'detail': str(e),
                }
            except (httpx.RequestError, Exception) as e:
                r_status: int = HTTPStatus.INTERNAL_SERVER_ERROR.value  # 500
                r_body: dict = {
                    'error': 'Ошибка обработки запроса сервером',
                    'detail': str(e),
                }

        return r_status, r_body, r_headers
