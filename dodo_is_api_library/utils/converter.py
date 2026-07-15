from datetime import (
    date,
    datetime,
    timezone,
)
from typing import Iterable
from uuid import UUID


def convert_date_to_str(dt: str | date) -> str:
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

def convert_uuids_to_str(
    uuids: Iterable[str | UUID],
    to_hex: bool = True,
    separator: str = ',',
) -> str| None:
    """Конвертирует список UUID в единую строку.

    Принимает строго Iterable (list, tuple, set и т.д.), содержащий str или UUID.

    Если to_hex=True, то возвращает строку в формате XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX,
    иначе - строку в формате XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.

    В DodoIS API по-умолчанию используется HEX формат UUID.
    """
    if not uuids:
        return None
    if isinstance(uuids, str):
        raise TypeError("Expected list/set/tuple, got str")

    processed: list[str] = []
    for item in uuids:
        if not item:
            continue
        if isinstance(item, UUID):
            processed.append(item.hex if to_hex else str(item))
        elif isinstance(item, str):
            clean_str = item.replace('-', '').strip()
            if to_hex:
                processed.append(clean_str)
            else:
                # INFO. Если нужен формат с дефисами, но строка может их
                #       не содержать: безопасно восстановить значение через UUID.
                processed.append(str(UUID(clean_str)))
        else:
            raise TypeError(
                f"Expected str or UUID, got {type(item).__name__}",
            )
    return separator.join(processed) if processed else None
