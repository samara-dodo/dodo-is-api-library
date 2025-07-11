from typing import Iterable


class DodoISScopes:
    """
    Класс представления DodoIS Scopes.
    """

    OPENID = 'openid'                        # токен доступа
    SALES = 'sales'                          # продажи
    STAFF_SHIFTS_READ = 'staffshifts:read'   # смены сотрудников / персонала, доступ на чтение
    USER_ROLE_READ = 'user.role:read'        # роли и юниты пользователя, доступ на чтение

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
            raise ValueError(f'У пользователя отсутсвуют обязательные scopes: {", ".join(missed_scopes)}')
