from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GeneralProfile:
    key: str
    name: str
    search_text: str
    select_template: Optional[str]
    select_threshold_name: str
    select_desc: str
    skill_template: str
    skill_threshold_name: str
    skill_desc: str
    target_template: Optional[str]
    target_threshold_name: str
    target_desc: str
    attack_strategy: str = "standard"
    change_card_strategy: str = "standard"


@dataclass(frozen=True)
class SpiritProfile:
    key: str
    name: str
    prompt_template: Optional[str] = None
    prompt_threshold_name: Optional[str] = None
    prompt_desc: str = "将灵技能询问"


@dataclass(frozen=True)
class ComboProfile:
    key: str
    name: str
    general_profile_key: str
    spirit_profile_key: str


DEFAULT_GENERAL_PROFILE_KEY = "shen_huangzhong"
DEFAULT_SPIRIT_PROFILE_KEY = "cao_chun"
DEFAULT_COMBO_PROFILE_KEY = "shen_huangzhong_cao_chun"

AVAILABLE_GENERAL_PROFILES = {
    DEFAULT_GENERAL_PROFILE_KEY: GeneralProfile(
        key=DEFAULT_GENERAL_PROFILE_KEY,
        name="神黄忠",
        search_text="shenhuangzhong ",
        select_template="select_hero.png",
        select_threshold_name="THRESH_BUTTON",
        select_desc="选择武将-神黄忠",
        skill_template="acquire.png",
        skill_threshold_name="THRESH_ACQUIRE",
        skill_desc="摸体力值张牌",
        target_template="head.png",
        target_threshold_name="THRESH_HEAD",
        target_desc="神黄忠部位选择图",
    ),
    "kebineng": GeneralProfile(
        key="kebineng",
        name="轲比能",
        search_text="kebineng ",
        select_template="select_kebineng.png",
        select_threshold_name="THRESH_SELECT_KEBINENG",
        select_desc="选择武将-轲比能",
        skill_template="koujing.png",
        skill_threshold_name="THRESH_KOUJING",
        skill_desc="寇旌",
        target_template=None,
        target_threshold_name="THRESH_HEAD",
        target_desc="轲比能无部位选择图",
        attack_strategy="kebineng",
        change_card_strategy="cancel_only",
    ),
}

AVAILABLE_SPIRIT_PROFILES = {
    DEFAULT_SPIRIT_PROFILE_KEY: SpiritProfile(
        key=DEFAULT_SPIRIT_PROFILE_KEY,
        name="曹纯",
        prompt_template="require.png",
        prompt_threshold_name="THRESH_REQUIRE",
        prompt_desc="将灵技能询问",
    ),
    "shen_caocao": SpiritProfile(
        key="shen_caocao",
        name="神曹操",
        prompt_template=None,
        prompt_threshold_name=None,
        prompt_desc="无将灵技能触发",
    ),
}


AVAILABLE_COMBO_PROFILES = {
    DEFAULT_COMBO_PROFILE_KEY: ComboProfile(
        key=DEFAULT_COMBO_PROFILE_KEY,
        name="神黄忠 + 曹纯",
        general_profile_key=DEFAULT_GENERAL_PROFILE_KEY,
        spirit_profile_key=DEFAULT_SPIRIT_PROFILE_KEY,
    ),
    "kebineng_shen_caocao": ComboProfile(
        key="kebineng_shen_caocao",
        name="轲比能 + 神曹操",
        general_profile_key="kebineng",
        spirit_profile_key="shen_caocao",
    ),
    "kebineng_cao_chun": ComboProfile(
        key="kebineng_cao_chun",
        name="轲比能 + 曹纯",
        general_profile_key="kebineng",
        spirit_profile_key=DEFAULT_SPIRIT_PROFILE_KEY,
    ),
}


def resolve_general_profile(profile_key=None):
    if isinstance(profile_key, GeneralProfile):
        return profile_key

    key = profile_key or DEFAULT_GENERAL_PROFILE_KEY
    return AVAILABLE_GENERAL_PROFILES.get(key, AVAILABLE_GENERAL_PROFILES[DEFAULT_GENERAL_PROFILE_KEY])


def resolve_spirit_profile(profile_key=None):
    if isinstance(profile_key, SpiritProfile):
        return profile_key

    key = profile_key or DEFAULT_SPIRIT_PROFILE_KEY
    return AVAILABLE_SPIRIT_PROFILES.get(key, AVAILABLE_SPIRIT_PROFILES[DEFAULT_SPIRIT_PROFILE_KEY])


def resolve_combo_profile(profile_key=None):
    if isinstance(profile_key, ComboProfile):
        return profile_key

    key = profile_key or DEFAULT_COMBO_PROFILE_KEY
    return AVAILABLE_COMBO_PROFILES.get(key, AVAILABLE_COMBO_PROFILES[DEFAULT_COMBO_PROFILE_KEY])
