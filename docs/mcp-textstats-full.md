# MCP textstats — полный пример и результаты

Что делает
- Минимальный MCP-подобный сервер (`scripts/mcp_textstats.py`) с инструментом `textstats(path)`: считает строки, слова и символы в UTF‑8 файле. Общается через stdin/stdout, принимает упрощённые JSON-запросы.

Описание MCP и протокол
- MCP (Model Context Protocol) — способ подключать внешние инструменты к агентам через стандартный обмен сообщениями.
- В этой минимальной реализации используется упрощённый JSON-RPC по stdin/stdout:
  - Методы:
    - `tools/list` — вернуть список доступных инструментов.
    - `tools/call` — вызвать конкретный инструмент по имени с аргументами.
  - Запрос: `{"id":<number|string>, "method":"tools/...", "params":{...}}`
  - Ответ: либо `{"id":<same>, "result": ...}`, либо `{"id":<same>, "error": {"code": <int>, "message": <string>}}`.

Как запускать
- Список доступных инструментов:
  ```bash
  echo '{"id":1,"method":"tools/list"}' | python3 scripts/mcp_textstats.py
  ```
- Вызов `textstats` с реальным файлом (пример для `README.md`):
  ```bash
  echo '{"id":2,"method":"tools/call","params":{"name":"textstats","args":{"path":"README.md"}}}' | python3 scripts/mcp_textstats.py
  ```
- Ошибочные примеры:
  ```bash
  echo '{"id":3,"method":"tools/call","params":{"name":"textstats","args":{}}}' | python3 scripts/mcp_textstats.py
  echo '{"id":4,"method":"tools/call","params":{"name":"textstats","args":{"path":" "}}}' | python3 scripts/mcp_textstats.py
  echo '{"id":5,"method":"tools/call","params":{"name":"textstats","args":{"path":"no_such_file.txt"}}}' | python3 scripts/mcp_textstats.py
  ```

Реальные результаты (с текущего запуска)
```json
{"id":1,"result":[{"name":"textstats","description":"Count lines, words, and characters in a UTF-8 text file","args":{"path":"string"}}]}
{"id":2,"result":{"path":"README.md","lines":216,"words":1159,"chars":9037}}
{"id":3,"error":{"code":400,"message":"args.path is required"}}
{"id":4,"error":{"code":400,"message":"args.path must be a non-empty string"}}
{"id":5,"error":{"code":404,"message":"file not found: no_such_file.txt"}}
```

Примечания
- Значения для `lines/words/chars` зависят от содержимого файла.
- Это упрощённая реализация MCP: для полноценной интеграции нужен манифест и секция `mcp` в `opencode.json`.

Интеграция с OpenCode (локальный MCP)
- Добавьте в `opencode.json`:
  ```json
  {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
      "textstats": {
        "type": "local",
        "command": ["python3", "scripts/mcp_textstats.py"],
        "enabled": true
      }
    }
  }
  ```
- После изменения перезапустите OpenCode. Сервер будет доступен агентам как MCP «textstats».

Как вызывать (кратко)
- Непосредственно (stdin/stdout): см. команды выше в разделе «Как запускать».
- Через OpenCode (после интеграции): агенты смогут вызывать `tools/list` и `tools/call` этого MCP. Для проверки — используйте встроенные команды агента или вставьте JSON-запрос в консоль MCP (если агент предоставляет такую возможность).
