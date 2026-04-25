"""Plugin/skill loader — drop .py files into plugins/ directory."""

import importlib.util
import os
import re

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")
_loaded_plugins = {}

LIST_PLUGINS_PATTERN = re.compile(r"^(?:list|show) plugins$", re.I)
RELOAD_PLUGINS_PATTERN = re.compile(r"^reload plugins$", re.I)


def ensure_plugin_dir():
    os.makedirs(PLUGIN_DIR, exist_ok=True)


def load_plugins():
    global _loaded_plugins
    ensure_plugin_dir()
    _loaded_plugins = {}
    for filename in os.listdir(PLUGIN_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue
        name = filename[:-3]
        path = os.path.join(PLUGIN_DIR, filename)
        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _loaded_plugins[name] = mod
            print(f"[PLUGIN] Loaded: {name}")
        except Exception as e:
            print(f"[PLUGIN] Failed to load {name}: {e}")
    return _loaded_plugins


def get_loaded_plugins():
    return _loaded_plugins


def is_plugin_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(LIST_PLUGINS_PATTERN.match(normalized) or RELOAD_PLUGINS_PATTERN.match(normalized))


def handle_plugin_command(text):
    normalized = " ".join(str(text).strip().split())

    if RELOAD_PLUGINS_PATTERN.match(normalized):
        loaded = load_plugins()
        names = list(loaded.keys())
        if names:
            return {"action": "reload_plugins", "reply": f"Reloaded {len(names)} plugins: {', '.join(names)}"}
        return {"action": "reload_plugins", "reply": "No plugins found in the plugins folder."}

    if LIST_PLUGINS_PATTERN.match(normalized):
        names = list(_loaded_plugins.keys())
        if names:
            descriptions = []
            for n, mod in _loaded_plugins.items():
                desc = getattr(mod, "DESCRIPTION", "No description")
                descriptions.append(f"{n}: {desc}")
            return {"action": "list_plugins", "reply": "Loaded plugins: " + "; ".join(descriptions)}
        return {"action": "list_plugins", "reply": "No plugins loaded. Put .py files in the plugins folder."}

    return None


def try_plugin_handle(text):
    for name, mod in _loaded_plugins.items():
        handler = getattr(mod, "handle_command", None)
        matcher = getattr(mod, "matches", None)
        if handler and matcher:
            if matcher(text):
                try:
                    result = handler(text)
                    if result:
                        return result
                except Exception as e:
                    return {"action": "plugin_error", "reply": f"Plugin {name} error: {e}"}
    return None


# Auto-load on import
load_plugins()
