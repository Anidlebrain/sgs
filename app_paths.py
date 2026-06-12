from pathlib import Path
import sys


if getattr(sys, "frozen", False):
    # 打包成 exe 后，BASE_DIR 指向 exe 所在文件夹
    BASE_DIR = Path(sys.executable).parent
else:
    # 正常 python 运行时，BASE_DIR 指向当前 py 文件所在文件夹
    BASE_DIR = Path(__file__).parent


TEMPLATE_DIR = BASE_DIR / "templates"
DEBUG_DIR = BASE_DIR / "debug_screens"
LEARNED_TEMPLATE_DIR = BASE_DIR / "learned_templates"
LOG_DIR = BASE_DIR / "logs"
SETTINGS_FILE = BASE_DIR / "settings.json"

DEBUG_DIR.mkdir(exist_ok=True)
LEARNED_TEMPLATE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
