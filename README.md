# KYŪREIKA — ядро и SQLite

Локальное Python-ядро вымышленного персонажа Королевы Девяти Хвостов. Без внешних зависимостей.

## Структура

- `Kyureika.bat` — запуск и меню для Windows
- `main.py` — командный интерфейс управления ядром
- `core/database.py` — SQLite, таблицы, память, сообщения и состояние
- `core/personality.py` — характер персонажа и сборка контекста
- `data/kyureika.sqlite3` — локальная база, создаётся при запуске (не хранится в Git)
- `tests/` — проверки

## Запуск

Требуется Python 3.10+. На Windows дважды нажмите `Kyureika.bat` или выполните:

```bash
python main.py init
python main.py status
python main.py remember "Хозяин любит зелёный чай"
python main.py memories
python main.py context
python -m unittest discover -s tests
```

При первом запуске SQLite создаётся в `data/kyureika.sqlite3`. Таблицы: `schema_version`, `personality`, `memories`, `messages`, `emotional_state`, `settings`.

Это ядро хранения и личности, а не готовый чат-бот: языковая модель, графический интерфейс и полноценная логика диалога пока не подключены.

Не добавляйте SQLite-файл с личными разговорами в Git.
