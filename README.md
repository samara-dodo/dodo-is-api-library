# DodoIS Api Library

Библиотека для взаимодействия с DodoIS API.

### Релиз в PyPi

1. Обновить pyproject.toml:

- "dependencies": зависимости (при необходимости)
- "version": обновить версию (семантика: мажорная.минорная.патч)

2. Установить необходимые инструменты для экпорта библиотеки:

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

После ввода команды в консоле запросится "API token" аккаунта PyPi, который необходимо запросить у старшего разработчика.

### ТЕХНОЛОГИИ

Проект разработан с использованием следующих технологий:

- [Python] (v.3.12) - целевой язык программирования
- [AnyIO] (v.4.9) - универсальная асинхронная библиотека, которая предоставляет единый API поверх asyncio и trio
- [HttpX] (v.0.28) - HTTP клиент для sync и async обращений по протоколам HTTP/1.1 и HTTP/2

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

[Python]: <https://www.python.org/>
[HttpX]: <https://www.python-httpx.org/>
[Anyio]: <https://anyio.readthedocs.io/en/stable/>
