# Skill: notify-mini-frontend — что делает и как работает

Что это
- Специализированный навык для разработки и эволюции минимального фронтенда и HTTP-слоя над учебным сервисом Notify Mini (`practices/practice_03/lab/demo`).
- Цель: быстро и детерминированно реализовать Фичу A (UI + API) без внешних зависимостей, используя только стандартную библиотеку Python и простую вёрстку.

Что делает навык
- Задаёт чёткие шаги и шаблоны для:
  - HTTP API на `http.server` (`BaseHTTPRequestHandler`/`ThreadingHTTPServer`).
  - Статической страницы (`web/index.html`, `web/script.js`, `web/style.css`) с добавлением, удалением и фильтром.
  - Минимального расширения бэкенда (`service.py`): `normalize_name`, `unsubscribe`, `list_subscribers`.
  - Цели `make serve` для локального запуска сервера.
- Формализует контракт API, чтобы фронт и сервер были согласованы.

Как устроен
- Файл навыка: `.opencode/skills/notify-mini-frontend/SKILL.md`.
- Внутри описаны:
  - Триггеры (какие файлы/ключевые слова запускают навык).
  - Ограничения (без Flask, без npm; только стандартная библиотека).
  - API-контракт и шаблоны кода для сервера и фронтенда.
  - Чеклисты для Feature A (UI+API) и Feature B (персистентность и улучшения UX).
  - Критерии приёмки (что должно заработать в браузере и API).

API (JSON)
- `GET /api/subscribers` → `{ "subscribers": ["Ann", ...] }`
- `POST /api/subscribe` тело `{ "name": "Ann" }` → `{ "subscribed": true }` (400 при пустом имени)
- `POST /api/unsubscribe` тело `{ "name": "Ann" }` → `{ "unsubscribed": true|false }`
- Статика: `GET /` → `web/index.html`; `GET /style.css`, `GET /script.js` → ассеты UI.

Интерфейс (клиент)
- `web/index.html`: форма добавления имени, поле фильтра, список подписчиков и кнопки удаления.
- `web/script.js`: обращения к API (`fetch`), обновление списка, дебаунс фильтра.
- `web/style.css`: минимальный стиль без фреймворков.

Как запускать
1. Запустить сервер из каталога `practices/practice_03/lab/demo`:
   - `make serve`
2. Открыть в браузере: `http://127.0.0.1:8000/`
3. Проверить:
   - Добавление имени (появляется в списке).
   - Фильтрация (список отфильтровывается по подстроке).
   - Удаление (имя исчезает, API возвращает `{"unsubscribed": true}`).

Проверка API вручную
- Список подписчиков: `curl -s http://127.0.0.1:8000/api/subscribers`
- Добавление: `curl -s -X POST http://127.0.0.1:8000/api/subscribe -H 'Content-Type: application/json' -d '{"name":"Ann"}'`
- Удаление: `curl -s -X POST http://127.0.0.1:8000/api/unsubscribe -H 'Content-Type: application/json' -d '{"name":"Ann"}'`

Ожидаемый результат
- Рабочая страница управления подписчиками с добавлением, удалением и фильтром.
- API стабильно возвращает корректные JSON-ответы и коды статусов.
- Юнит-тесты демо проходят: `make -s -C practices/practice_03/lab test`.

Связанные материалы
- Навык: `.opencode/skills/notify-mini-frontend/SKILL.md`
- Краткая выжимка по pre-commit: `docs/pre-commit-summary.md`
