from re import (
    sub,
    IGNORECASE,
)


def process_legal_entity_name(value: str | None) -> str | None:
    """
    Обрабатывает название юридического лица.
    """
    if value is None:
        return None
    # INFO. Могут быть лидирующие пробелы, дублирование типа предприятия, кавычки.
    value = value.strip()
    value = sub(pattern=r'[«»"“”]', repl="", string=value)
    value = sub(pattern=r'^(?:ООО|ОАО|ЗАО|ИП)\s+', repl="", string=value, flags=IGNORECASE)
    # INFO. Дополнительный strip, если внутри кавычек были множественные пробелы.
    return value.strip()


def process_full_address(value: str | None) -> str | None:
    """
    Обрабатывает адрес.
    """
    if value is None:
        return None
    return value.strip()
