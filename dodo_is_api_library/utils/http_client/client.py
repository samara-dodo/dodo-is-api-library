"""
Модуль отправки HTTP запросов.
"""

import asyncio
from datetime import (
    datetime,
    timezone,
)
from email.utils import parsedate_to_datetime
from http import HTTPStatus
import json
import random
from typing import Any

from aiolimiter import AsyncLimiter
import httpx

from dodo_is_api_library.utils.http_client.dto import HttpResponseDTO
from dodo_is_api_library.utils.http_client.enums import (
    HttpContentTypes,
    HttpMethods,
)
from dodo_is_api_library.utils.http_client.config import HttpClientConfig


class HttpClient:
    """
    Класс обработки HTTP запросов.
    """

    def __init__(
        self,
        config: HttpClientConfig,
    ):
        self._config = config
        self._client = httpx.AsyncClient(
            # INFO. Использование httpx.Limits вместо asyncio.Semaphore
            #       позволяет сделать то же самое по смыслу ограничение,
            #       но на уровне, который ближе к TCP-соединению.
            limits=httpx.Limits(
                max_connections=self._config.max_concurrent_requests,
                max_keepalive_connections=self._config.max_concurrent_requests,
            ),
            proxy=self._config.proxy_url,
        )
        self._rate_limiter = AsyncLimiter(
            max_rate=self._config.rate_limit_request_count,
            time_period=self._config.rate_limit_period_sec,
        )

    async def close(self) -> None:
        """Явное закрытие HTTP-клиента и освобождение ресурсов."""
        await self._client.aclose()

    async def send_request(
        self,
        *,
        method: HttpMethods,
        url: str,
        query_params: dict | None = None,
        data: list | dict | str | bytes | None = None,
        files: dict | None = None,
        headers: dict | None = None,
        auth: Any | None = None,
        timeout_sec: float | None = None,
        max_attempts: int | None = None,
    ) -> HttpResponseDTO:
        """
        Отправляет HTTP запрос с указанными параметрами.

        Возвращает:
            - статус-код ответа
            - тело ответа
            - заголовки ответа

        Автоматически повторяет запрос при 5хх ошибках с использованием
        экспоненциальной задержки (Backoff + Jitter).
        """
        (
            http_headers,
            data_content,
            data_form,
            data_json,
            max_attempts,
            timeout_sec,
        ) = self._prepare_request_data(
            data=data,
            files=files,
            headers=headers,
            max_attempts=max_attempts,
            method=method,
            timeout_sec=timeout_sec,
        )

        response_dto: HttpResponseDTO | None = None

        for attempt in range(1, max_attempts + 1):
            response_dto = HttpResponseDTO(
                cookies=httpx.Cookies(),
                data=None,
                headers={},
                status_code=HTTPStatus.BAD_GATEWAY.value,
            )
            retry_needed: bool = False

            try:
                response_dto = await self._send_single_request(
                    method=method,
                    url=url,
                    query_params=query_params,
                    data_content=data_content,
                    data_form=data_form,
                    data_json=data_json,
                    files=files,
                    headers=http_headers,
                    auth=auth,
                    timeout_sec=timeout_sec,
                )
                if (
                    response_dto.status_code == HTTPStatus.TOO_MANY_REQUESTS
                    or response_dto.status_code >= 500
                ):
                    retry_needed = True

            except httpx.ConnectError:
                response_dto.status_code = HTTPStatus.BAD_GATEWAY.value  # 502
                response_dto.data = {"error": "Соединение не установлено"}
                retry_needed = True
            except httpx.TimeoutException:
                response_dto.status_code = HTTPStatus.GATEWAY_TIMEOUT.value  # 504
                response_dto.data = {"error": "Превышено время ожидания соединения"}
                retry_needed = True
            except httpx.LocalProtocolError as e:
                response_dto.status_code = HTTPStatus.BAD_REQUEST.value  # 400
                response_dto.data = {
                    "error": "Неправильный протокол запроса",
                    "detail": str(e),
                }
                retry_needed = False
            except httpx.RequestError as e:
                response_dto.status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value  # 500
                response_dto.data = {
                    "error": "Ошибка обработки запроса сервером",
                    "detail": str(e),
                }
                retry_needed = True

            if retry_needed and attempt < max_attempts:
                delay: float | None = self._get_backoff_delay(
                    attempt=attempt,
                    response_dto=response_dto,
                )
                if delay is None:
                    break
                await asyncio.sleep(delay)
            else:
                break

        if response_dto is None:
            raise RuntimeError("Request loop has never been executed")
        return response_dto

    def _get_backoff_delay(
        self,
        *,
        attempt: int,
        response_dto: HttpResponseDTO,
    ) -> float | None:
        """
        Высчитывает экспоненциальную задержку с джиттером
        перед следующей попыткой запроса.
        """
        delay: float = self._config.backoff_delay_base_sec * (2 ** (attempt - 1))
        if self._config.use_jitter:
            # INFO. Разброс идет строго вниз, чтобы при срезании
            #       значений по min - они с меньшим шансом становились
            #       равны self.backoff_delay_max_sec.
            delay *= 1 + random.uniform(-self._config.use_jitter_factor, 0.0)  # nosec B311
        delay = min(delay, self._config.backoff_delay_max_sec)
        retry_after: str | int | None = response_dto.headers.get("retry-after")
        if (
            response_dto.status_code != HTTPStatus.TOO_MANY_REQUESTS
            or retry_after is None
        ):
            return delay

        # INFO. Стандарт HTTP/1.1 (RFC  пункт 7.1.3):
        #       https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3
        #           - Retry-After: Fri, 31 Dec 1999 23:59:59 GMT
        #           - Retry-After: 120
        retry_after_sec: float | None = None
        if (
            isinstance(retry_after, str)
            and retry_after.isdigit()
            or isinstance(retry_after, (int, float))
        ):
            retry_after_sec = float(retry_after)
        else:
            try:
                dt: datetime = parsedate_to_datetime(retry_after)
                retry_after_sec = (dt - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError):
                pass

        if retry_after_sec is not None:
            if retry_after_sec > self._config.backoff_delay_max_sec:
                return None
            if retry_after_sec > 0:
                return max(delay, retry_after_sec)
        return delay

    def _prepare_request_data(
        self,
        *,
        data: list | dict | str | bytes | None,
        files: dict | None,
        headers: dict | None,
        max_attempts: int | None,
        method: HttpMethods,
        timeout_sec: float | None,
    ) -> tuple[
        httpx.Headers,
        str | bytes | None,
        dict | None,
        list | dict | str | bytes | None,
        int,
        float,
    ]:
        """Подготавливает данные для отправки запроса."""
        http_headers: httpx.Headers = (
            httpx.Headers(headers) if headers else httpx.Headers()
        )

        data_content: str | bytes | None = None
        data_form: dict | None = None
        data_json: list | dict | str | bytes | None = None

        if method in HttpMethods.all_safe():
            if data is not None:
                raise ValueError(
                    f"Метод {method} не поддерживает передачу тела запроса (data)",
                )
        elif method in HttpMethods.all_unsafe():
            if files is not None:
                if not isinstance(files, dict):
                    raise ValueError('Параметр "files" должен быть dict')
                # INFO. Если переданы файлы, httpx должен сам установить Content-Type!
                if "Content-Type" in http_headers:
                    del http_headers["Content-Type"]
                if data is not None:
                    if not isinstance(data, dict):
                        raise ValueError(
                            'При отправке файлов параметр "data" должен быть dict',
                        )
                    data_form = data

            elif data is not None:
                http_headers.setdefault(
                    "Content-Type", HttpContentTypes.APPLICATION_JSON,
                )
                if http_headers["Content-Type"].startswith(
                    HttpContentTypes.APPLICATION_JSON,
                ):
                    if not isinstance(data, (list, dict, str, bytes)):
                        raise ValueError(
                            'Параметр "data" должен быть list, dict, str или bytes',
                        )
                    if isinstance(data, (list, dict)):
                        data_json = data
                    else:
                        data_content = data
                elif http_headers["Content-Type"].startswith(
                    HttpContentTypes.APPLICATION_X_WWW_FORM_URLENCODED,
                ):
                    if not isinstance(data, dict):
                        raise ValueError(
                            'Для Form-Data параметр "data" должен быть dict',
                        )
                    data_form = data
                else:
                    if not isinstance(data, (str, bytes)):
                        raise ValueError('Параметр "data" должен быть str или bytes')
                    data_content = data
        else:
            raise ValueError(f"Метод {method} не поддерживается")

        timeout_sec = timeout_sec or self._config.timeout_sec
        max_attempts = max(1, (max_attempts or self._config.max_attempts))

        return (
            http_headers,
            data_content,
            data_form,
            data_json,
            max_attempts,
            timeout_sec,
        )

    async def _send_single_request(
        self,
        *,
        method: HttpMethods,
        url: str,
        query_params: dict | None,
        data_content: str | bytes | None,
        data_form: dict | None,
        data_json: list | dict | str | bytes | None,
        files: dict | None,
        headers: httpx.Headers,
        auth: Any | None,
        timeout_sec: float,
    ) -> HttpResponseDTO:
        """
        Отправляет HTTP запрос.

        Строит HttpResponseDTO ответа.
        """
        async with self._rate_limiter:
            response: httpx.Response = await self._client.request(
                method=method,
                url=url,
                params=query_params,
                # INFO. Автоматически делает json.dumps().
                json=data_json,
                # INFO. Передает "как есть" x-www-form-urlencoded.
                data=data_form,
                # INFO. Отправляет "как есть" сырые байты/строку.
                content=data_content,
                files=files,
                headers=headers,
                auth=auth,
                timeout=httpx.Timeout(
                    connect=self._config.timeout_connect_sec,
                    read=timeout_sec,
                    write=timeout_sec,
                    pool=timeout_sec,
                ),
            )
        if not response.content:
            r_data: Any = None
        elif (
            response.headers.get("Content-Type", "").startswith(
                HttpContentTypes.APPLICATION_JSON,
            )
            and response.content
        ):
            try:
                r_data = response.json()
            except json.JSONDecodeError:
                r_data = response.text
        else:
            r_data = response.text
        return HttpResponseDTO(
            cookies=httpx.Cookies(response.cookies),
            data=r_data,
            headers=dict(response.headers.multi_items()),
            status_code=response.status_code,
        )
