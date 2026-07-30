from enum import StrEnum


class HttpContentTypes(StrEnum):
    """
    Класс представления HTTP Content-Type.
    """

    APPLICATION_JSON = "application/json"
    APPLICATION_X_WWW_FORM_URLENCODED = "application/x-www-form-urlencoded"
    MULTIPART_FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"


class HttpMethods(StrEnum):
    """
    Класс представления HTTP методов.
    """

    # Безопасные.
    HEAD = "HEAD"
    GET = "GET"
    OPTIONS = "OPTIONS"
    # Небезопасные.
    DELETE = "DELETE"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"

    @classmethod
    def all_safe(cls) -> tuple[str, str, str]:
        return (cls.HEAD, cls.GET, cls.OPTIONS)

    @classmethod
    def all_unsafe(cls) -> tuple[str, str, str, str]:
        return (cls.DELETE, cls.PATCH, cls.POST, cls.PUT)
