# DodoIS Api Library

Библиотека для асинхронного взаимодействия с DodoIS API.

### Интеграция библиотеки в приложение

В настоящий момент установка зависимости через PyPi не представляется возможным.
Для интеграции библиотеки в приложение:

```bash
pip install git+https://github.com/samara-dodo/dodo-is-api-library.git
```

Или через Poetry для установки и обновления:
```bash
poetry add git+https://github.com/samara-dodo/dodo-is-api-library.git
poetry update dodo-is-api-library
```

Внимание! Для установки зависимостей внутри Docker нужно в Dockerfile внести код:
```bash
# Устанавливает и настраивает git (для установки зависимостей не из PyPi, а из git).
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
```

Для инициализации библиотеки в коде:

```python
from dodo_is_api_library import DodoISApi

dodo_is: DodoISApi = DodoISApi(
    client_id=settings.DODO_IS_CLIENT_ID,
    client_secret=settings.DODO_IS_CLIENT_SECRET,
    redirect_uri=settings.DODO_IS_REDIRECT_URI,
    get_user_data=async_get_user_data,
    update_user_data=async_update_user_data,
)
```
где:
- client_id: id приложения в Marketplace
- client_secret: секрет приложения в Marketplace
- redirect_uri: адрес, на который вернется callback из DodoIS
- get_user_data: асинхронная функция, которая получает данные пользователя в сервисе
- update_user_data: асинхронная функция, которая может записывает данные пользователя в сервисе

Примеры реализации функций получения и сохранения данных пользователя:

```python
async def get_user_data(
    user_id: int | None = None,
    user_ip: str | None = None,
) -> dict[str, Any]:
    """
    Возвращает данные пользователя по ID и IP-адресу запроса.

    Хранятся в PostgreSQL (доступны по user_id):
        - access_token
        - refresh_token
    Хранятся в Redis (доступны по user_ip):
        - code_verifier
        - code_challenge
    """
    # INFO. Базовый набор scopes для авторизации и получения данных пользователя.
    user_data: dict[str, Any] = {
        "scopes": (
            "offline_access",  # токен обновления (refresh)
            "openid",  # доступ
            "phone",  # номер телефона
            "profile",  # имя и фамилия
        )
    }
    if user_id:
        async with async_session_maker() as session:
            user: User = await user_repository.retrieve_by_id(
                obj_id=user_id, session=session
            )
        user_data.update(
            {
                "access_token": user.dodois_token_access,
                "refresh_token": user.dodois_token_refresh,
            }
        )
    if user_ip:
        for key, redis_key in (
            ("code_challenge", RedisKeys.CODE_CHALLENGE_BY_IP),
            ("code_verifier", RedisKeys.CODE_VERIFIER_BY_IP),
        ):
            user_data[key] = await redis_client.get(key=redis_key.format(ip=user_ip))
    return user_data

async def update_user_data(
    user_data: dict[str, Any],
    user_id: int | None = None,
    user_ip: str | None = None,
) -> None:
    """
    Обновляет данные пользователя по ID и IP-адресу запроса.

    Хранятся в PostgreSQL (доступны по user_id):
        - access_token
        - refresh_token
    Хранятся в Redis (доступны по user_ip):
        - code_verifier
        - code_challenge
    """
    if user_id:
        async with async_session_maker() as session:
            await user_repository.update_by_id(
                obj_id=user_id,
                obj_data=user_data,
                session=session,
            )
    if user_ip:
        for key, redis_key in (
            ("code_challenge", RedisKeys.CODE_CHALLENGE_BY_IP),
            ("code_verifier", RedisKeys.CODE_VERIFIER_BY_IP),
        ):
            if key in user_data:
                await redis_client.set(
                    key=redis_key.format(ip=user_ip),
                    value=user_data[key],
                    ex_sec=TimeIntervals.SECONDS_IN_1_DAY,
                )
```

### Релиз в PyPi

1. Обновить pyproject.toml:

- "dependencies": зависимости (при необходимости)
- "version": обновить версию (семантика: мажорная.минорная.патч)

2. Установить необходимые инструменты для экспорта библиотеки:

```bash
pip install build twine
```

3. Собрать библиотеку:

```bash
rm -r dist/ build/ *.egg-info
python -m build
```

4. Опубликовать библиотеку:

```bash
twine upload dist/*
```

После ввода команды в консоли запросится "API token" аккаунта PyPi, который необходимо запросить у старшего разработчика.

### ТЕХНОЛОГИИ

Проект разработан с использованием следующих технологий:

- [Python] (v.3.12) - целевой язык программирования
- [HttpX] (v.0.28) - HTTP клиент для sync и async обращений по протоколам HTTP/1.1 и HTTP/2

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

[Python]: <https://www.python.org/>
[HttpX]: <https://www.python-httpx.org/>
