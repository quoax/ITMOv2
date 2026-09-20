# Журнал экспериментов Практики 2

Файл ведёт OpenCode по вашим запросам. Агент записывает фактические результаты экспериментов и вносит изменения в связанные файлы. Свою оценку сообщайте ему в чате; вручную заполнять шаблон не нужно.

- Выбранный слабый артефакт Практики 1:
- Выбранный слабый артефакт Практики 1: practices/practice_01/tests_load.md
- Что в нём нужно улучшить: сделать проверяемым; согласовать статусы
- Как поймём, что изменение полезно: проходит проверка

| Техника | Файл эксперимента | Изменённый файл Практики 1 | Конкретное изменение | Проверка | Что отклонили |
|---|---|---|---|---|---|
| Few-shot | [`few_shot/experiment.md`](few_shot/experiment.md) | practices/practice_01/tests_load.md#нагрузочные-проверки (таблица сценариев) | Уточнены пороги и добавлены воспроизводимые команды hey/wrk; согласованы ожидания по 2xx/4xx/5xx | make step2 OK | Отклонены предложения требовать jq/внешние скрипты wrk |
| R.C.T.F. | [`rctf/experiment.md`](rctf/experiment.md) | practices/practice_01/tests_load.md#что-сохранять-после-прогона | Добавлен единый шаблон фиксации результатов (поля и как получить из hey/wrk) | make step2 OK | Отклонены требования к jq/сложному парсингу |
| Chain of Verification | [`chain_of_verification/experiment.md`](chain_of_verification/experiment.md) | practices/practice_01/tests_load.md#нагрузочные-проверки — сценарий «Стабильность при 502» | Уточнён сценарий «502»: введена базовая метка P95_ok и режим мока always_timeout | make step2 OK | Отклонён автопарсинг результатов во время практики |
| Tree of Thoughts | [`tree_of_thoughts/experiment.md`](tree_of_thoughts/experiment.md) | practices/practice_01/tests_load.md#примечания | Инструмент по умолчанию — hey; wrk обозначен как опция | make step2 OK | Отклонён перенос сценариев в pytest без агрегирования квантилей |
| RAG | [`rag/experiment.md`](rag/experiment.md) | practices/practice_01/tests_load.md#примечания | Добавлена ссылка на подтверждённые статусы 422/502 и контракт ReviewResponse | make step2 OK | Отклонены упоминания 400/504 |
| ReAct | [`react/experiment.md`](react/experiment.md) | practices/practice_01/tests_load.md#подсказки | Добавлена подсказка о запуске uvicorn перед нагрузкой | make step2 OK | Отклонён автозапуск сервиса в рамках П2 |
