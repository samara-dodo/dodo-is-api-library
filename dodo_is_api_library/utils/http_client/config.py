from dataclasses import dataclass


@dataclass
class HttpClientConfig:
    """
    Конфигурация HTTP-клиента.

    Аргументы:
        #### Rate Limiting
        - max_concurrent_requests: максимальное количество конкурентных запросов
        - rate_limit_request_count: максимальное количество запросов за rate_limit_period_sec
        - rate_limit_period_sec: период времени в секундах для лимита запросов rate_limit_request_count
        #### Retries
        - timeout_sec: время ожидания HTTP ответа в секундах
        - timeout_connect_sec: время ожидания TCP соединения в секундах
        - max_attempts: максимальное количество попыток HTTP запросов
        - backoff_delay_base_sec: базовая задержка между попытками в секундах
        - backoff_delay_max_sec: максимальная задержка между попытками в секундах
        - use_jitter: использовать джиттер (экспоненциальная задержка)
        - use_jitter_factor: коэффициент случайного разброса джиттера (0.2 = 20%)
        #### Proxy
        - proxy_url: URL для прокси
    """

    # Rate Limiting
    max_concurrent_requests: int = 10
    rate_limit_request_count: int = 5
    rate_limit_period_sec: float = 1.0

    # Retries
    timeout_sec: float = 30.0
    timeout_connect_sec: float = 5.0
    max_attempts: int = 3
    backoff_delay_base_sec: float = 1.0
    backoff_delay_max_sec: float = 30.0
    use_jitter: bool = True
    use_jitter_factor: float = 0.2

    # Proxy
    proxy_url: str | None = None
