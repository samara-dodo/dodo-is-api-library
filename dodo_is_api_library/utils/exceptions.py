from typing import Any

from httpx._exceptions import HTTPError


def raise_http_exception(
    status_code: int,
    detail: Any,
) -> None:
    """
    Выбрасывает исключение при неудачном HTTP обращении.
    """
    raise HTTPError(
        message=(
            f"Error getting auth token data from DodoIS with status {status_code}. "
            f"Response data: {detail}"
        ),
    )
