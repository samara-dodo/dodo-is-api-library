from datetime import (
    datetime,
    timezone,
)
from uuid import UUID


def convert_date_to_str(dt: str | datetime) -> str:
    """
    Конвертирует дату в строку формата YYYY-MM-DD.
    """
    if isinstance(dt, str):
        return dt
    return dt.strftime("%Y-%m-%d")


def convert_datetime_to_str(dt: str | datetime) -> str:
    """
    Конвертирует дату и время в строку формата YYYY-MM-DDTHH:MM:SS.
    """
    if isinstance(dt, str):
        return dt
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")


def convert_uuid_to_str(
    uid: str | UUID,
    to_hex: bool = True,
) -> str:
    """
    Конвертирует UUID в строку.

    Если to_hex=True, то возвращает строку в формате XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX,
    иначе - строку в формате XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.

    В DodoIS API по-умолчанию используется HEX формат UUID.
    """
    if isinstance(uid, str):
        return uid.replace("-", "") if to_hex else uid
    return uid.hex if to_hex else str(uid)
