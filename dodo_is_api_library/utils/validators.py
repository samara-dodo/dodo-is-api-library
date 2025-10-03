from re import (
    sub,
    IGNORECASE,
)
from typing import Iterable


class BusinessIds:
    """
    Класс представления идентификаторов бизнеса.
    """

    DRINKIT: str = "c0b18e725258427a8bffea4f73957b0e"
    PIZZA: str = "63d4829611ea45c8ae71394860a2481c"

    @classmethod
    def validate(cls, value: str) -> None:
        """Производит валидацию идентификатора бизнеса."""
        if value not in (cls.DRINKIT, cls.PIZZA):
            raise ValueError(
                'В "business_id" допустимы следующие значения: '
                '"c0b18e725258427a8bffea4f73957b0e" (drinkit), '
                '"63d4829611ea45c8ae71394860a2481c" (pizza)',
            )


class CountryIds:
    """
    Класс представления идентификаторов страны в формате ISO 3166-1 alpha-2.
    """

    RU: str = "ru"

    @classmethod
    def validate(cls, value: str) -> None:
        """Производит валидацию идентификатора страны."""
        if value not in {cls.RU}:
            raise ValueError('В "country_id" допустимы следующие значения: "ru"')


class UnitStates:
    """
    Класс представления статусов объекта.
    """

    CLOSE: str = "Close"
    OPEN: str = "Open"
    TEMPORARY_CLOSE: str = "TemporaryClosed"

    @classmethod
    def validate(cls, value: Iterable[str]) -> None:
        """Производит валидацию идентификатора бизнеса."""
        if value and not set(value).issubset({
            cls.CLOSE,
            cls.OPEN,
            cls.TEMPORARY_CLOSE,
        }):
            raise ValueError(
                'В "unit_states" допустимы следующие значения: ["Open", "Close", "TemporaryClosed"]',
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
