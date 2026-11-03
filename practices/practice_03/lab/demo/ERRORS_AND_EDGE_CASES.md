# Проверки ошибок и граничных условий: Пагинация и сортировка

Дата: 2026-11-02

## Сценарии успеха

- GET /api/v1/subscribers?offset=0&limit=2&sort=asc → 200, тело содержит ровно два верхнеуровневых ключа: `items` (2 элемента) и `total` (6)
- Переход на следующую страницу offset=2, limit=2 → 200, `items` (2 элемента), `total` (6)
- Сортировка `sort=desc` → 200, список отсортирован по `created_at` убыванию с tie-breaker `id asc`

## Ошибки валидации (400)

- limit=1000 → 400 VALIDATION_ERROR, details: `{ "limit": "must be between 1 and 100" }`
- offset=-1 → 400 VALIDATION_ERROR, details: `{ "offset": "must be >= 0" }`
- sort=bad → 400 VALIDATION_ERROR, details: `{ "sort": "must be one of asc, desc" }`

UI-поведение: отображается сообщение об ошибке; предлагаются исправления параметров (клиппинг значений).

## Внутренняя ошибка (500)

- Тестовый хук `__test_internal=1` → 500 INTERNAL_ERROR, details: `{}`. UI показывает баннер и предлагает повтор.

## Краевые случаи

- offset >> total → 200, `items: []`, `total: N`. UI корректирует offset на последнюю валидную страницу и повторяет запрос.
- total == 0, items.length == 0 → пустое состояние, пейджер скрыт/disabled, сводка «Показано 0 из 0».

## Автоматизация

- e2e_check.py генерирует файл results_e2e.md с конкретными статусами и краткой сводкой по сценариям.
- test_http_contract.py покрывает контракт: формат {items,total}, 400 с details, 500 INTERNAL_ERROR.
