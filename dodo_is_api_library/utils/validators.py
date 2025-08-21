from re import (
    sub,
    IGNORECASE,
)


def process_legal_entity_name(value: str) -> str:
    """
    Обрабатывает название юридического лица.
    """
    # INFO. Могут быть лидирующие пробелы, дублирование типа предприятия, кавычки.
    value = value.strip()
    value = sub(pattern=r'[«»"“”]', repl="", string=value)
    value = sub(pattern=r'^(?:ООО|ОАО|ЗАО|ИП)\s+', repl="", string=value, flags=IGNORECASE)
    # INFO. Дополнительный strip, если внутри кавычек были множественные пробелы.
    return value.strip()


def process_full_address(value: str) -> str:
    """
    Обрабатывает адрес.
    """
    return value.strip()
