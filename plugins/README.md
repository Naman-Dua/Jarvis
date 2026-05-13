# Kora Plugins Directory

Drop `.py` files here to extend Kora's capabilities.

Each plugin must expose:

```python
DESCRIPTION = "Short description of what this plugin does"

def matches(text: str) -> bool:
    ...

def handle_command(text: str) -> dict | None:
    ...
```

Return format:

```python
{"action": "plugin_name", "reply": "response text"}
```
