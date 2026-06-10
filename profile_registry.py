from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GeneralProfile:
    key: str
    name: str
    search_text: str
    select_template: str
    select_desc: str
    skill_template: str
    skill_threshold_name: str
    skill_desc: str
    target_template: Optional[str]
    target_threshold_name: str
    target_desc: str


@dataclass(frozen=True)
class SpiritProfile:
    key: str
    name: str
    prompt_template: str
    prompt_threshold_name: str
    prompt_desc: str


DEFAULT_GENERAL_PROFILE_KEY = "shen_huangzhong"
DEFAULT_SPIRIT_PROFILE_KEY = "cao_chun"

AVAILABLE_GENERAL_PROFILES = {
    DEFAULT_GENERAL_PROFILE_KEY: GeneralProfile(
        key=DEFAULT_GENERAL_PROFILE_KEY,
        name="神黄忠",
        search_text="shenhuangzhong ",
        select_template="select_hero.png",
        select_desc="选择武将-神黄忠",
        skill_template="acquire.png",
        skill_threshold_name="THRESH_ACQUIRE",
        skill_desc="摸体力值张牌",
        target_template="head.png",
        target_threshold_name="THRESH_HEAD",
        target_desc="神黄忠部位选择图",
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
