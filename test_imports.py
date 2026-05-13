import sys
import traceback

files = [
    'process_mgmt',
    'file_ops',
    'clipboard_ops',
    'system_info',
    'network_tools',
    'timer_tools',
    'window_mgmt',
    'storage',
    'memory_tools',
    'entertainment_mode',
    'auto_debug',
    'knowledge_packs',
    'brain',
    'kora_operator',
    'gui',
    'settings',
    'skills',
    'main',
]
success = True

for f in files:
    try:
        mod = __import__(f)
        print(f + ' imported successfully.')
    except Exception as e:
        print(f + ' failed to import:', e)
        traceback.print_exc()
        success = False

sys.exit(0 if success else 1)
