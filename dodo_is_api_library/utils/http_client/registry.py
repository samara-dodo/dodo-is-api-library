from enum import StrEnum

from dodo_is_api_library.utils.http_client.client import HttpClient
from dodo_is_api_library.utils.http_client.client import HttpClientConfig


class HttpClientNames(StrEnum):
    """Класс представления названий HTTPклиентов."""

    DODOIS_API = "dodois_api"


class HttpClientsRegistry:
    """Класс реестра HTTP клиентов."""

    def __init__(self):
        self._clients: dict[str, HttpClient] = {}

    def get_client(
        self,
        name: HttpClientNames,
        config: HttpClientConfig,
    ) -> HttpClient:
        """
        Создает и возвращает HTTP-клиента.
        При повторном вызове возвращает уже созданный HTTP-клиент.
        """
        if name not in self._clients:
            self._clients[name] = HttpClient(config=config)
        return self._clients[name]

    async def close_all(self):
        for client in self._clients.values():
            await client.close()


http_clients_registry: HttpClientsRegistry = HttpClientsRegistry()

http_client: HttpClient = http_clients_registry.get_client(
    name=HttpClientNames.DODOIS_API,
    config=HttpClientConfig(
        max_concurrent_requests=10,
        rate_limit_request_count=200,
        rate_limit_period_sec=60,
        timeout_sec=60,
        timeout_connect_sec=15,
        max_attempts=1,
    ),
)
