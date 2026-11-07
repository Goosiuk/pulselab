# Быстрый запуск

Открыть эту папку как проект в PyCharm. Интерпретатор проекта — `.venv/bin/python`.

Контейнер `pulselab-demo` должен быть запущен. Его состояние можно посмотреть в Docker Desktop или командой:

```bash
docker ps -a
```

Если контейнер уже существует, запустить его:

```bash
docker start pulselab-demo
```

После этого запустить `probe.py` из PyCharm или терминала:

```bash
source .venv/bin/activate
python probe.py
```

Ожидается словарь с `status_code=200`, `ok=True`, временем ответа и `error=None`.

Для нескольких проверок и записи в файл:

```bash
python monitor.py --url http://127.0.0.1:8088/health --count 5 --interval 1 --timeout 0.5 --out checks.jsonl
```

Первое создание образа и контейнера описано в [README.md](README.md). Все команды выполняются из корня проекта.
