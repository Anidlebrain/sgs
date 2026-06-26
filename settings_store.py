import json
from dataclasses import asdict, dataclass

from app_paths import SETTINGS_FILE


LOG_LEVEL_VALUES = {
    "trace": 10,
    "debug": 20,
    "info": 30,
    "warn": 40,
    "error": 50,
}
LOG_LEVEL_NAMES = tuple(LOG_LEVEL_VALUES.keys())
DEFAULT_LOG_LEVEL = "info"


def normalize_log_level(level):
    text = str(level or "").strip().lower()
    return text if text in LOG_LEVEL_VALUES else DEFAULT_LOG_LEVEL


def is_valid_log_level(level):
    return str(level or "").strip().lower() in LOG_LEVEL_VALUES


def should_emit_log(message_level, configured_level):
    message_level = normalize_log_level(message_level)
    configured_level = normalize_log_level(configured_level)
    return LOG_LEVEL_VALUES[message_level] >= LOG_LEVEL_VALUES[configured_level]


def infer_log_level(text):
    text = str(text)

    if any(word in text for word in ("异常", "错误", "Traceback")):
        return "error"

    if any(word in text for word in (
        "失败",
        "中断",
        "中止",
        "超时",
        "停止",
        "FailSafe",
        "可疑点击",
        "没有检测到浏览器窗口",
    )):
        return "warn"

    if any(word in text for word in (
        "匹配不足",
        "未找到：",
        "没有检测到",
        "当前没有检测到",
        "等待出现",
        "已出现",
        "找到并点击",
        "等待后点击",
        "检测到 ",
        "置信度=",
        "坐标=",
        "搜索区域=",
        "来源=",
    )):
        return "debug"

    if any(word in text for word in ("模板不存在", "模板读取", "数量：")):
        return "trace"

    return "info"


def format_log_record(text, level=None):
    from datetime import datetime

    level = normalize_log_level(level or infer_log_level(text))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{now}] [{level.upper()}] {text}"


@dataclass
class BotSettings:
    DEFAULT_THRESHOLD: float = 0.65
    CLICK_SLEEP: float = 0.4

    THRESH_BUTTON: float = 0.65
    THRESH_SMALL: float = 0.65
    THRESH_CARD: float = 0.65
    THRESH_BOSS: float = 0.65
    THRESH_HEAD: float = 0.65
    THRESH_VICTORY: float = 0.65
    THRESH_SAVE: float = 0.65

    THRESH_ACQUIRE: float = 0.60
    THRESH_REQUIRE: float = 0.75

    THRESH_POPUP: float = 0.55
    THRESH_CONFIRM: float = 0.55
    THRESH_SELECT_KEBINENG: float = 0.65
    THRESH_KOUJING: float = 0.60
    THRESH_KEBINENG_CARD_MARKER: float = 0.70
    THRESH_SELECT_ALL: float = 0.75

    SUPERVISION_ENABLED: bool = True
    SUPERVISION_MIN_CONF: float = 0.50
    LOG_TO_FILE: bool = True
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL
    MAX_GAME_COUNT: int = -1
    SHUTDOWN_AFTER_STOP: bool = False
    LAST_COMBO_PROFILE_KEY: str = "shen_huangzhong_cao_chun"
    ENTRY_WINDOW_GEOMETRY: str = "365x360+601+258"
    MAIN_WINDOW_GEOMETRY: str = "365x710+601+258"

    GAME_REGION_WIDTH: int = 1280
    GAME_REGION_HEIGHT: int = 800
    GAME_REGION_PADDING: int = 60

    BODY_HEAD_REL_X: float = 0.50
    BODY_HEAD_REL_Y: float = 0.18

    BODY_CHEST_REL_X: float = 0.50
    BODY_CHEST_REL_Y: float = 0.31


THRESHOLD_META = [
    {
        "name": "THRESH_BUTTON",
        "title": "通用按钮阈值",
        "desc": "用于开始挑战、取消、整理手牌等普通按钮。",
    },
    {
        "name": "THRESH_SMALL",
        "title": "小图标/提示阈值",
        "desc": "用于 select_figure、select_figure_2 等较小提示图。",
    },
    {
        "name": "THRESH_CARD",
        "title": "手牌识别阈值",
        "desc": "用于 attack.png，也就是【杀】的识别。",
    },
    {
        "name": "THRESH_BOSS",
        "title": "Boss头像阈值",
        "desc": "用于 lijue.png，也就是李傕头像识别。",
    },
    {
        "name": "THRESH_HEAD",
        "title": "人体图阈值",
        "desc": "用于神黄忠技能效果的部位选择模板 head.png；其他武将无该流程时不会使用。",
    },
    {
        "name": "THRESH_VICTORY",
        "title": "胜利界面阈值",
        "desc": "用于 victory.png，判断是否通关。",
    },
    {
        "name": "THRESH_SAVE",
        "title": "求桃阈值",
        "desc": "用于 save.png，检测到后点击取消。",
    },
    {
        "name": "THRESH_ACQUIRE",
        "title": "武将技能阈值",
        "desc": "用于 acquire.png，也就是神黄忠武将技能提示识别。",
    },
    {
        "name": "THRESH_REQUIRE",
        "title": "将灵技能询问阈值",
        "desc": "用于 require.png，也就是是否发动【缝甲】。",
    },
    {
        "name": "THRESH_POPUP",
        "title": "弹窗技能阈值",
        "desc": "用于 increase_damage.png / xiaorui.png。",
    },
    {
        "name": "THRESH_CONFIRM",
        "title": "确认按钮阈值",
        "desc": "用于 confirm.png，点确定时使用。",
    },
    {
        "name": "THRESH_SELECT_KEBINENG",
        "title": "轲比能选将阈值",
        "desc": "用于 select_kebineng.png，也就是选将搜索结果卡面。",
    },
    {
        "name": "THRESH_KOUJING",
        "title": "寇旌技能阈值",
        "desc": "用于 koujing.png，也就是轲比能出牌阶段的寇旌提示。",
    },
    {
        "name": "THRESH_KEBINENG_CARD_MARKER",
        "title": "轲比能手牌标记阈值",
        "desc": "用于 kebineng_card_marker.png，也就是手牌上的寇旌杀标记。",
    },
    {
        "name": "THRESH_SELECT_ALL",
        "title": "全选按钮阈值",
        "desc": "用于 select_all.png。该按钮紧挨整理手牌，默认比普通按钮更严格。",
    },
]


DEFAULT_SETTING_VALUES = asdict(BotSettings())


def coerce_bool_setting(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        if value in (0, 1):
            return bool(value)
        raise ValueError("不是有效布尔值")

    if isinstance(value, str):
        text = value.strip().lower()

        if text in ("true", "1", "yes", "y", "on"):
            return True

        if text in ("false", "0", "no", "n", "off"):
            return False

    raise ValueError("不是有效布尔值")


def validate_setting_value(name, value):
    if name == "MAX_GAME_COUNT" and value != -1 and value <= 0:
        raise ValueError("必须为 -1 或正整数")

    if name in ("GAME_REGION_WIDTH", "GAME_REGION_HEIGHT") and value <= 0:
        raise ValueError("必须大于 0")

    if name == "GAME_REGION_PADDING" and value < 0:
        raise ValueError("不能小于 0")

    if (
        name == "DEFAULT_THRESHOLD"
        or name.startswith("THRESH_")
        or name == "SUPERVISION_MIN_CONF"
        or name.startswith("BODY_")
    ) and not 0 <= value <= 1:
        raise ValueError("必须在 0 到 1 之间")

    if name == "CLICK_SLEEP" and value < 0:
        raise ValueError("不能小于 0")

    return value


def coerce_setting_value(name, default_value, value):
    if isinstance(default_value, bool):
        parsed_value = coerce_bool_setting(value)
    elif name == "LOG_LEVEL":
        if not is_valid_log_level(value):
            raise ValueError("不是有效日志级别")

        parsed_value = normalize_log_level(value)
    elif isinstance(default_value, int):
        parsed_value = int(float(value))
    elif isinstance(default_value, float):
        parsed_value = float(value)
    elif isinstance(default_value, str):
        parsed_value = str(value)
    else:
        parsed_value = value

    return validate_setting_value(name, parsed_value)


def write_settings_file(settings):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
            f.write("\n")
    except Exception as e:
        return False, f"保存设置失败：{e}"

    return True, None


def load_bot_settings():
    if not SETTINGS_FILE.exists():
        settings = BotSettings()
        saved, save_error = write_settings_file(settings)

        if not saved:
            return settings, False, f"设置文件不存在，且{save_error}"

        return settings, True, "设置文件不存在，已生成默认设置文件"

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        settings = BotSettings()
        saved, save_error = write_settings_file(settings)

        if not saved:
            return settings, False, f"读取设置失败：{e}；同时{save_error}"

        return settings, False, f"读取设置失败：{e}；已重建默认设置文件"

    if not isinstance(data, dict):
        settings = BotSettings()
        saved, save_error = write_settings_file(settings)

        if not saved:
            return settings, False, f"设置文件格式错误；同时{save_error}"

        return settings, False, "设置文件格式错误；已重建默认设置文件"

    values = DEFAULT_SETTING_VALUES.copy()
    repaired_items = []

    for name, default_value in DEFAULT_SETTING_VALUES.items():
        if name not in data:
            repaired_items.append(f"缺失 {name}")
            continue

        value = data[name]

        try:
            values[name] = coerce_setting_value(name, default_value, value)
        except (TypeError, ValueError) as e:
            repaired_items.append(f"修复 {name}（{e}）")

    settings = BotSettings(**values)

    if repaired_items:
        saved, save_error = write_settings_file(settings)

        if not saved:
            return settings, False, f"设置文件已在内存中修复，但{save_error}"

        repaired_text = "；".join(repaired_items[:8])

        if len(repaired_items) > 8:
            repaired_text += f"；另有 {len(repaired_items) - 8} 项"

        return settings, True, f"设置文件已自动补齐/修复：{repaired_text}"

    return settings, True, None


def save_bot_settings(settings):
    return write_settings_file(settings)
