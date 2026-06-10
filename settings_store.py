import json
from dataclasses import asdict, dataclass

from app_paths import SETTINGS_FILE


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

    SUPERVISION_ENABLED: bool = True
    SUPERVISION_MIN_CONF: float = 0.50

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
        "desc": "用于 acquire.png，也就是【摸体力值张牌】。",
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
]


DEFAULT_SETTING_VALUES = asdict(BotSettings())


def load_bot_settings():
    if not SETTINGS_FILE.exists():
        return BotSettings(), False, None

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return BotSettings(), False, f"读取设置失败：{e}"

    if not isinstance(data, dict):
        return BotSettings(), False, "设置文件格式错误"

    values = DEFAULT_SETTING_VALUES.copy()

    for name, default_value in DEFAULT_SETTING_VALUES.items():
        if name not in data:
            continue

        value = data[name]

        try:
            if isinstance(default_value, bool):
                values[name] = bool(value)
            else:
                values[name] = float(value)
        except (TypeError, ValueError):
            return BotSettings(), False, f"设置项 {name} 不是有效数值"

    return BotSettings(**values), True, None


def save_bot_settings(settings):
    try:
        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
            f.write("\n")
    except Exception as e:
        return False, f"保存设置失败：{e}"

    return True, None
