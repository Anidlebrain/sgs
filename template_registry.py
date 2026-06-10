import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateMeta:
    path: Path
    display_name: str
    learned_subdir: Path
    learned_filename_prefix: str


def safe_filename_part(text):
    text = re.sub(r'[<>:"/\\|?*\s]+', "_", text)
    return text.strip("._") or "template"


def template_meta(path, display_name, learned_subdir, learned_filename_prefix):
    return TemplateMeta(
        path=Path(path),
        display_name=display_name,
        learned_subdir=Path(learned_subdir),
        learned_filename_prefix=safe_filename_part(learned_filename_prefix),
    )


TEMPLATE_META = {
    # 武将：神黄忠
    "acquire.png": template_meta(
        "武将/神黄忠/acquire.png",
        "武将：神黄忠 - acquire.png（技能：裂穹摸牌）",
        "武将/神黄忠/acquire",
        "武将_神黄忠_技能_裂穹摸牌",
    ),
    "head.png": template_meta(
        "武将/神黄忠/head.png",
        "武将：神黄忠 - head.png（技能：裂穹击中）",
        "武将/神黄忠/head",
        "武将_神黄忠_技能_裂穹击中",
    ),

    # 将灵：曹纯
    "require.png": template_meta(
        "将灵/曹纯/require.png",
        "将灵：曹纯 - require.png（技能字：是否发动缮甲）",
        "将灵/曹纯/require",
        "将灵_曹纯_技能字_是否发动缮甲",
    ),
    "require (2).png": template_meta(
        "将灵/曹纯/require (2).png",
        "将灵：曹纯 - require (2).png（技能：是否发动缮甲-全）",
        "将灵/曹纯/require_full",
        "将灵_曹纯_技能_是否发动缮甲_全",
    ),
    "xiaorui.png": template_meta(
        "将灵/曹纯/xiaorui.png",
        "将灵：曹纯 - xiaorui.png（技能字：是否发动骁锐）",
        "将灵/曹纯/xiaorui",
        "将灵_曹纯_技能字_是否发动骁锐",
    ),

    # 通用逻辑/流程
    "start_challenge.png": template_meta(
        "通用/流程按钮/start_challenge.png",
        "通用：start_challenge.png（流程按钮：立即挑战）",
        "通用/流程按钮/start_challenge",
        "通用_流程按钮_立即挑战",
    ),
    "victory.png": template_meta(
        "通用/流程/victory.png",
        "通用：victory.png（流程：起始界面）",
        "通用/流程/victory",
        "通用_流程_起始界面",
    ),
    "add_hero.png": template_meta(
        "通用/流程/add_hero.png",
        "通用：add_hero.png（流程：选择武将）",
        "通用/流程/add_hero",
        "通用_流程_选择武将",
    ),
    "attack.png": template_meta(
        "通用/卡牌/attack.png",
        "通用：attack.png（卡牌：杀）",
        "通用/卡牌/attack",
        "通用_卡牌_杀",
    ),
    "confirm.png": template_meta(
        "通用/流程按钮/confirm.png",
        "通用：confirm.png（流程按钮：确认）",
        "通用/流程按钮/confirm",
        "通用_流程按钮_确认",
    ),
    "cancel.png": template_meta(
        "通用/流程按钮/cancel.png",
        "通用：cancel.png（流程按钮：取消）",
        "通用/流程按钮/cancel",
        "通用_流程按钮_取消",
    ),
    "cancel_2.png": template_meta(
        "通用/流程/cancel_2.png",
        "通用：cancel_2.png（流程：窗口关闭）",
        "通用/流程/cancel_2",
        "通用_流程_窗口关闭",
    ),
    "change.png": template_meta(
        "通用/流程/change.png",
        "通用：change.png（流程：是否换牌）",
        "通用/流程/change",
        "通用_流程_是否换牌",
    ),
    "change_cards.png": template_meta(
        "通用/流程按钮/change_cards.png",
        "通用：change_cards.png（流程按钮：换牌）",
        "通用/流程按钮/change_cards",
        "通用_流程按钮_换牌",
    ),
    "sort.png": template_meta(
        "通用/流程按钮/sort.png",
        "通用：sort.png（流程按钮：整理手牌）",
        "通用/流程按钮/sort",
        "通用_流程按钮_整理手牌",
    ),
    "lijue.png": template_meta(
        "通用/BOSS/lijue.png",
        "通用：lijue.png（BOSS：李傕）",
        "通用/BOSS/lijue",
        "通用_BOSS_李傕",
    ),
    "search.png": template_meta(
        "通用/流程/search.png",
        "通用：search.png（流程：搜索）",
        "通用/流程/search",
        "通用_流程_搜索",
    ),
    "select_figure.png": template_meta(
        "通用/流程/select_figure.png",
        "通用：select_figure.png（流程：选择一个其他角色）",
        "通用/流程/select_figure",
        "通用_流程_选择一个其他角色",
    ),
    "select_figure_2.png": template_meta(
        "通用/流程/select_figure_2.png",
        "通用：select_figure_2.png（流程：选择一个目标）",
        "通用/流程/select_figure_2",
        "通用_流程_选择一个目标",
    ),
    "select_hero.png": template_meta(
        "通用/流程/select_hero.png",
        "通用：select_hero.png（流程：选择武将-神黄忠）",
        "通用/流程/select_hero",
        "通用_流程_选择武将_神黄忠",
    ),
    "save.png": template_meta(
        "通用/流程字/save.png",
        "通用：save.png（流程字：是否出桃）",
        "通用/流程字/save",
        "通用_流程字_是否出桃",
    ),
    "war.png": template_meta(
        "通用/流程/war.png",
        "通用：war.png（流程：关卡界面）",
        "通用/流程/war",
        "通用_流程_关卡界面",
    ),
    "increase_damage.png": template_meta(
        "通用/流程字/increase_damage.png",
        "通用：increase_damage.png（流程字：是否增伤）",
        "通用/流程字/increase_damage",
        "通用_流程字_是否增伤",
    ),
}


def get_template_meta(template_name):
    meta = TEMPLATE_META.get(template_name)

    if meta is not None:
        return meta

    stem = Path(template_name).stem
    return template_meta(
        template_name,
        template_name,
        stem,
        stem,
    )


def get_template_display_name(template_name):
    return get_template_meta(template_name).display_name
