# Kora Plugins Directory
# Drop .py files here to extend Kora's capabilities.
#
# Each plugin must expose:
#   DESCRIPTION = "Short description of what this plugin does"
#   def matches(text: str) -> bool: ...
#   def handle_command(text: str) -> dict | None: ...
#
# Return format: {"action": "plugin_name", "reply": "response text"}
