from dataclasses import dataclass
from typing import Any

from httpx import Cookies


@dataclass(slots=True)
class HttpResponseDTO:
    """
    Схема представления HTTP ответа.
    """

    cookies: Cookies
    data: Any
    headers: dict
    status_code: int
