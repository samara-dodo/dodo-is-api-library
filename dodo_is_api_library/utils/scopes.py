from typing import Iterable


class DodoISScopes:
    """
    Класс представления DodoIS Scopes.
    """

    FRANCHISEE_READ = "franchisee:read"             # ID франшизы
    OFFLINE_ACCESS = "offline_access"               # токен обновления
    OPENID = "openid"                               # токен доступа
    ORGANIZATIONSTRUCTURE = "organizationstructure" # оргструктура
    PHONE = "phone"                                 # номер телефона
    PROFILE = "profile"                             # профиль
    SALES = "sales"                                 # продажи
    SHARED = "shared"                               # общие
    STAFF_SHIFTS_READ = "staffshifts:read"          # смены сотрудников / персонала, доступ на чтение
    USER_ROLE_READ = "user.role:read"               # роли и юниты пользователя, доступ на чтение

    @staticmethod
    def validate_scopes(
        user_scopes: Iterable[str],
        required_scopes: set[str],
    ) -> None:
        """
        Проверяет наличие обязательных scopes.
        """
        missed_scopes: set[str] = required_scopes - set(user_scopes)
        if missed_scopes:
            raise ValueError(
                'У пользователя отсутствуют обязательные scopes: '
                f'{", ".join(missed_scopes)}',
            )
