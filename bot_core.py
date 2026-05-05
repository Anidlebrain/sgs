import time
import random
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import pyautogui


# =========================================================
# 基础路径
# =========================================================

import sys

if getattr(sys, "frozen", False):
    # 打包成 exe 后，BASE_DIR 指向 exe 所在文件夹
    BASE_DIR = Path(sys.executable).parent
else:
    # 正常 python 运行时，BASE_DIR 指向当前 py 文件所在文件夹
    BASE_DIR = Path(__file__).parent

TEMPLATE_DIR = BASE_DIR / "templates"
DEBUG_DIR = BASE_DIR / "debug_screens"
DEBUG_DIR.mkdir(exist_ok=True)

pyautogui.FAILSAFE = True


# =========================================================
# 阈值配置
# =========================================================

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
        "desc": "用于 head.png，决定是否进入点击头部/胸部流程。",
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


# =========================================================
# 自动化核心类
# =========================================================

class GameBot:
    def __init__(self, log_func=None, settings=None):
        self.log_func = log_func or print
        self.settings = settings or BotSettings()

        self.running = False
        self.paused = False
        self.stop_flag = False

        self.click_lock = threading.Lock()

        self.increase_damage_last_click_time = 0
        self.xiaorui_last_click_time = 0
        self.save_cancel_last_click_time = 0
        self.cancel_last_click_time = 0

    # -------------------------
    # 日志
    # -------------------------

    def log(self, text):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_func(f"[{now}] {text}")

    # -------------------------
    # 暂停辅助
    # -------------------------

    def sleep_with_pause(self, seconds):
        start = time.time()

        while time.time() - start < seconds:
            if self.stop_flag:
                return False

            if self.paused:
                time.sleep(0.2)
                continue

            time.sleep(0.1)

        return True

    # -------------------------
    # 鼠标相关
    # -------------------------

    def move_mouse_to_center(self):
        try:
            w, h = pyautogui.size()
            pyautogui.moveTo(w // 2, h // 2, duration=0.08)
        except Exception as e:
            self.log(f"鼠标回中失败：{e}")

    # -------------------------
    # 截图相关
    # -------------------------

    def screenshot_bgr(self):
        img = pyautogui.screenshot()
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    def save_debug_screenshot(self, name="screen"):
        screen = self.screenshot_bgr()
        filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = DEBUG_DIR / filename

        try:
            ext = path.suffix
            success, encoded_img = cv2.imencode(ext, screen)

            if success:
                encoded_img.tofile(str(path))
                self.log(f"已保存调试截图：{path}")
                return path

            self.log(f"截图编码失败：{path}")
            return None

        except Exception as e:
            self.log(f"保存截图异常：{e}")
            return None

    # -------------------------
    # 模板读取
    # -------------------------

    def load_template(self, template_name):
        path = TEMPLATE_DIR / template_name

        if not path.exists():
            self.log(f"模板不存在：{path}")
            return None

        try:
            data = np.fromfile(str(path), dtype=np.uint8)
            tpl = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception as e:
            self.log(f"模板读取异常：{path} | {e}")
            return None

        if tpl is None:
            self.log(f"模板读取失败：{path}")
            return None

        return tpl

    # -------------------------
    # 模板匹配
    # -------------------------

    def find_template(self, template_name, threshold=None, region=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        rect = self.find_template_rect(template_name, threshold, region)

        if rect is None:
            return None

        x, y, w, h, conf = rect
        return x + w // 2, y + h // 2, conf

    def find_template_quiet(self, template_name, threshold=None, region=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        screen = self.screenshot_bgr()
        template = self.load_template(template_name)

        if template is None:
            return None

        if region is not None:
            x, y, w, h = region
            search_img = screen[y:y + h, x:x + w]
            offset_x, offset_y = x, y
        else:
            search_img = screen
            offset_x, offset_y = 0, 0

        if search_img.size == 0:
            return None

        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < threshold:
            return None

        th, tw = template.shape[:2]
        center_x = offset_x + max_loc[0] + tw // 2
        center_y = offset_y + max_loc[1] + th // 2

        return center_x, center_y, max_val

    def find_template_rect(self, template_name, threshold=None, region=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        screen = self.screenshot_bgr()
        template = self.load_template(template_name)

        if template is None:
            return None

        if region is not None:
            x, y, w, h = region
            search_img = screen[y:y + h, x:x + w]
            offset_x, offset_y = x, y
        else:
            search_img = screen
            offset_x, offset_y = 0, 0

        if search_img.size == 0:
            return None

        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < threshold:
            self.log(
                f"匹配不足：{template_name} | "
                f"最高置信度={max_val:.3f} | 阈值={threshold:.3f}"
            )
            return None

        th, tw = template.shape[:2]
        top_left_x = offset_x + max_loc[0]
        top_left_y = offset_y + max_loc[1]

        return top_left_x, top_left_y, tw, th, max_val

    def find_all_templates(self, template_name, threshold=None, region=None, min_distance=20):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        screen = self.screenshot_bgr()
        template = self.load_template(template_name)

        if template is None:
            return []

        if region is not None:
            x, y, w, h = region
            search_img = screen[y:y + h, x:x + w]
            offset_x, offset_y = x, y
        else:
            search_img = screen
            offset_x, offset_y = 0, 0

        if search_img.size == 0:
            return []

        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= threshold)

        th, tw = template.shape[:2]
        candidates = []

        for x, y in zip(xs, ys):
            conf = result[y, x]
            cx = offset_x + x + tw // 2
            cy = offset_y + y + th // 2
            candidates.append((cx, cy, float(conf)))

        candidates.sort(key=lambda item: item[2], reverse=True)

        final_points = []

        for cx, cy, conf in candidates:
            too_close = False

            for fx, fy, _ in final_points:
                distance = ((cx - fx) ** 2 + (cy - fy) ** 2) ** 0.5

                if distance < min_distance:
                    too_close = True
                    break

            if not too_close:
                final_points.append((cx, cy, conf))

        return final_points

    def count_template(self, template_name, threshold=None, region=None):
        points = self.find_all_templates(template_name, threshold, region)
        count = len(points)
        self.log(f"检测到 {template_name} 数量：{count}")
        return count, points

    # -------------------------
    # 等待多个模板中的任意一个
    # -------------------------

    def wait_any_template(self, template_names, threshold=None, timeout=5, region=None, desc=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        show_name = desc or " / ".join(template_names)
        self.log(f"等待出现：{show_name}，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，停止等待")
                return None

            if self.paused:
                time.sleep(0.2)
                continue

            for template_name in template_names:
                found = self.find_template_quiet(
                    template_name,
                    threshold=threshold,
                    region=region
                )

                if found is not None:
                    x, y, conf = found
                    self.log(
                        f"已出现：{template_name} | "
                        f"置信度={conf:.3f} | 坐标=({x}, {y})"
                    )
                    return template_name, x, y, conf

            time.sleep(0.25)

        self.log(f"等待超时：{show_name}")
        return None

    # -------------------------
    # require.png 检测
    # -------------------------

    def detect_require_prompt(self):
        found = self.find_template(
            "require.png",
            threshold=self.settings.THRESH_REQUIRE
        )

        if found is None:
            self.log("没有检测到 require.png")
            return False

        x, y, conf = found
        self.log(f"检测到 require.png | 置信度={conf:.3f} | 坐标=({x}, {y})")
        return True

    # -------------------------
    # 点击工具
    # -------------------------

    def safe_click(self, x, y, jitter=3):
        with self.click_lock:
            rx = x + random.randint(-jitter, jitter)
            ry = y + random.randint(-jitter, jitter)

            pyautogui.moveTo(rx, ry, duration=random.uniform(0.05, 0.15))
            pyautogui.click()

            time.sleep(self.settings.CLICK_SLEEP)
            self.move_mouse_to_center()

    def click_template(self, template_name, threshold=None, region=None, desc=None):
        found = self.find_template(template_name, threshold, region)

        if found is None:
            self.log(f"未找到：{desc or template_name}")
            return False

        x, y, conf = found

        self.log(
            f"找到并点击：{desc or template_name} | "
            f"置信度={conf:.3f} | 坐标=({x}, {y})"
        )

        self.safe_click(x, y)
        return True

    def wait_template(self, template_name, threshold=None, timeout=5, region=None, desc=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        self.log(f"等待出现：{desc or template_name}，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，停止等待")
                return None

            if self.paused:
                time.sleep(0.2)
                continue

            found = self.find_template(template_name, threshold, region)

            if found is not None:
                x, y, conf = found
                self.log(
                    f"已出现：{desc or template_name} | "
                    f"置信度={conf:.3f} | 坐标=({x}, {y})"
                )
                return found

            time.sleep(0.25)

        self.log(f"等待超时：{desc or template_name}")
        return None

    def wait_and_click_template(self, template_name, threshold=None, timeout=5, region=None, desc=None):
        found = self.wait_template(template_name, threshold, timeout, region, desc)

        if found is None:
            return False

        x, y, conf = found
        self.safe_click(x, y)
        self.log(f"等待后点击：{desc or template_name}")
        return True

    # -------------------------
    # 特殊弹窗处理
    # -------------------------

    def handle_after_lijue_prompts(self, duration=3.0):
        self.log(f"持续检测 increase_damage.png / xiaorui.png，最长 {duration} 秒")

        start = time.time()
        handled_any = False

        while time.time() - start < duration:
            if self.stop_flag:
                return handled_any

            if self.paused:
                time.sleep(0.2)
                continue

            handled = False

            if self.handle_increase_damage():
                handled = True
                handled_any = True
                time.sleep(0.4)

            if self.handle_xiaorui():
                handled = True
                handled_any = True
                time.sleep(0.4)

            if not handled:
                time.sleep(0.2)

        return handled_any

    def handle_increase_damage(self):
        now = time.time()

        if now - self.increase_damage_last_click_time < 0.8:
            return False

        found = self.find_template_quiet(
            "increase_damage.png",
            threshold=self.settings.THRESH_POPUP
        )

        if found is None:
            return False

        x, y, conf = found
        self.log(f"检测到 increase_damage.png | 置信度={conf:.3f}")

        ok = self.click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            desc="increase_damage-确定"
        )

        if ok:
            self.increase_damage_last_click_time = time.time()
            self.log("已处理 increase_damage：点击确定")
            return True

        self.log("检测到 increase_damage，但没有找到 confirm.png")
        return False

    def handle_xiaorui(self):
        now = time.time()

        if now - self.xiaorui_last_click_time < 0.8:
            return False

        found = self.find_template_quiet(
            "xiaorui.png",
            threshold=self.settings.THRESH_POPUP
        )

        if found is None:
            return False

        x, y, conf = found
        self.log(f"检测到 xiaorui.png | 置信度={conf:.3f}")

        ok = self.click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            desc="xiaorui-确定"
        )

        if ok:
            self.xiaorui_last_click_time = time.time()
            self.log("已处理 xiaorui：点击确定")
            return True

        self.log("检测到 xiaorui，但没有找到 confirm.png")
        return False

    def handle_save_by_cancel(self):
        now = time.time()

        if now - self.save_cancel_last_click_time < 1.0:
            return False

        save_found = self.find_template_quiet(
            "save.png",
            threshold=self.settings.THRESH_SAVE
        )

        if save_found is None:
            return False

        x, y, conf = save_found
        self.log(f"检测到求桃 save.png | 置信度={conf:.3f} | 尝试点击取消")

        cancel_found = self.find_template_quiet(
            "cancel.png",
            threshold=self.settings.THRESH_BUTTON
        )

        if cancel_found is None:
            self.log("检测到 save.png，但没有找到 cancel.png")
            return False

        cx, cy, cconf = cancel_found
        self.log(f"找到 cancel.png | 置信度={cconf:.3f} | 点击取消")
        self.safe_click(cx, cy)

        self.save_cancel_last_click_time = time.time()
        return True

    def handle_missing_head_save_victory(self, context="未知阶段", victory_timeout=15):
        """
        head.png 没检测到时调用。

        逻辑：
        1. 检测 save.png
        2. 如果检测到 save.png，则点击 cancel.png
        3. 然后在 victory_timeout 秒内等待 victory.png
        4. 检测到 victory.png 返回 "victory"
        5. 没检测到返回 "not_found"
        """
        self.log(f"{context}：未检测到 head.png，开始检测 save.png")

        save_handled = self.handle_save_by_cancel()

        if not save_handled:
            self.log(f"{context}：未检测到 save.png，或没有成功点击 cancel.png")
            return "not_found"

        self.log(f"{context}：已处理 save.png，开始等待 victory.png，最长 {victory_timeout} 秒")

        start = time.time()

        while time.time() - start < victory_timeout:
            if self.stop_flag:
                self.log(f"{context}：收到停止信号，停止等待 victory.png")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            victory_found = self.find_template_quiet(
                "victory.png",
                threshold=self.settings.THRESH_VICTORY
            )

            if victory_found is not None:
                x, y, conf = victory_found
                self.log(
                    f"{context}：检测到 victory.png | "
                    f"置信度={conf:.3f} | 坐标=({x}, {y})"
                )
                return "victory"

            time.sleep(0.3)

        self.log(f"{context}：{victory_timeout} 秒内没有检测到 victory.png")
        return "not_found"

    def handle_cancel_only(self):
        now = time.time()

        if now - self.cancel_last_click_time < 0.8:
            return False

        cancel_found = self.find_template_quiet(
            "cancel.png",
            threshold=self.settings.THRESH_BUTTON
        )

        if cancel_found is None:
            return False

        x, y, conf = cancel_found
        self.log(f"检测到 cancel.png | 置信度={conf:.3f} | 点击取消")
        self.safe_click(x, y)

        self.cancel_last_click_time = time.time()
        return True

    def click_head_target(self):
        """
        将灵技能阶段使用。

        如果检测到 head.png：
            点击头部、胸部，返回 "handled"

        如果没检测到 head.png：
            检测 save.png，点击 cancel.png，然后 15 秒内检测 victory.png。
        """
        self.log("等待人体图 head.png 出现")

        rect = None
        start = time.time()
        timeout = 6

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，停止等待 head.png")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            rect = self.find_template_rect(
                "head.png",
                threshold=self.settings.THRESH_HEAD
            )

            if rect is not None:
                break

            time.sleep(0.25)

        if rect is None:
            self.log("未检测到人体图 head.png")
            return self.handle_missing_head_save_victory(
                context="将灵技能阶段",
                victory_timeout=15
            )

        x, y, w, h, conf = rect

        head_x = int(x + w * self.settings.BODY_HEAD_REL_X)
        head_y = int(y + h * self.settings.BODY_HEAD_REL_Y)

        chest_x = int(x + w * self.settings.BODY_CHEST_REL_X)
        chest_y = int(y + h * self.settings.BODY_CHEST_REL_Y)

        self.log(
            f"检测到 head.png | 置信度={conf:.3f} | "
            f"模板区域=({x}, {y}, {w}, {h})"
        )

        self.log(f"先点击头部位置=({head_x}, {head_y})")
        self.safe_click(head_x, head_y, jitter=2)

        time.sleep(0.4)

        self.log(f"再点击胸部位置=({chest_x}, {chest_y})")
        self.safe_click(chest_x, chest_y, jitter=2)

        return "handled"

    def wait_head_after_attack(self, timeout=10):
        """
        出牌阶段出杀后使用。

        如果检测到 head.png：
            点击头部、胸部，返回 "handled"

        如果没检测到 head.png：
            检测 save.png，点击 cancel.png，然后 15 秒内检测 victory.png。
        """
        self.log(f"出杀后等待 head.png，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，停止等待出杀后的 head.png")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            rect = self.find_template_rect(
                "head.png",
                threshold=self.settings.THRESH_HEAD
            )

            if rect is not None:
                x, y, w, h, conf = rect

                head_x = int(x + w * self.settings.BODY_HEAD_REL_X)
                head_y = int(y + h * self.settings.BODY_HEAD_REL_Y)

                chest_x = int(x + w * self.settings.BODY_CHEST_REL_X)
                chest_y = int(y + h * self.settings.BODY_CHEST_REL_Y)

                self.log(
                    f"出杀后检测到 head.png | 置信度={conf:.3f} | "
                    f"模板区域=({x}, {y}, {w}, {h})"
                )

                self.log(f"先点击头部位置=({head_x}, {head_y})")
                self.safe_click(head_x, head_y, jitter=2)

                time.sleep(0.4)

                self.log(f"再点击胸部位置=({chest_x}, {chest_y})")
                self.safe_click(chest_x, chest_y, jitter=2)

                return "handled"

            time.sleep(0.25)

        self.log("出杀后没有检测到 head.png")
        return self.handle_missing_head_save_victory(
            context="出牌阶段",
            victory_timeout=15
        )

    def wait_victory_only_after_attack(self, timeout=10):
        self.log(f"等待 victory.png，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，停止等待胜利")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            victory_found = self.find_template_quiet(
                "victory.png",
                threshold=self.settings.THRESH_VICTORY
            )

            if victory_found is not None:
                x, y, conf = victory_found
                self.log(f"检测到胜利界面 | 置信度={conf:.3f} | 一局结束")
                return "victory"

            time.sleep(0.3)

        self.log("10 秒内没有检测到 victory.png，判断进入下一轮")
        return "next_turn"

    def clear_cancel_until_acquire(self, timeout=150):
        """
        出牌阶段未检测到 victory 后调用。

        逻辑：
        1. 持续检测 cancel.png，有就点击。
        2. 等待 acquire.png 出现。
        3. 如果 timeout 秒内没等到 acquire.png，再额外检测一次 victory.png。
           - 有 victory.png：返回 victory，让完整流程进入下一局。
           - 没有 victory.png：返回 timeout。
        """
        self.log(f"进入下一轮清理阶段：持续点击 cancel.png，直到 acquire.png 出现，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，退出下一轮清理阶段")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            acquire_found = self.find_template_quiet(
                "acquire.png",
                threshold=self.settings.THRESH_ACQUIRE
            )

            if acquire_found is not None:
                x, y, conf = acquire_found
                self.log(f"检测到武将技能阶段 acquire.png | 置信度={conf:.3f}")
                return "next_turn"

            if self.handle_cancel_only():
                time.sleep(0.3)
                continue

            time.sleep(0.3)

        self.log(f"下一轮清理阶段超时：{timeout} 秒内未检测到 acquire.png，开始额外检测 victory.png")

        victory_found = self.find_template_quiet(
            "victory.png",
            threshold=self.settings.THRESH_VICTORY
        )

        if victory_found is not None:
            x, y, conf = victory_found
            self.log(f"超时后检测到 victory.png | 置信度={conf:.3f} | 判定本局胜利")
            return "victory"

        self.log("下一轮清理阶段超时：未检测到 acquire.png，也未检测到 victory.png")
        return "timeout"

    # =========================================================
    # 阶段函数：确定流程
    # =========================================================

    def stage_start_challenge(self):
        self.log("执行阶段：开始挑战")

        return self.click_template(
            "start_challenge.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="开始挑战"
        )

    def stage_check_victory(self):
        self.log("执行阶段：检测胜利界面")

        found = self.find_template(
            "victory.png",
            threshold=self.settings.THRESH_VICTORY
        )

        if found is None:
            self.log("当前没有检测到胜利界面")
            return False

        x, y, conf = found
        self.log(f"检测到胜利界面 | 置信度={conf:.3f} | 坐标=({x}, {y})")
        return True

    # =========================================================
    # 牌局阶段 ①：换牌阶段
    # =========================================================

    def battle_phase_change_cards(self):
        self.log("执行牌局阶段①：换牌阶段")

        attack_count, _ = self.count_template(
            "attack.png",
            threshold=self.settings.THRESH_CARD
        )

        if attack_count > 0:
            self.log(f"换牌阶段：检测到 {attack_count} 张【杀】，直接点击取消")
            cancel_ok = self.click_template(
                "cancel.png",
                threshold=self.settings.THRESH_BUTTON,
                desc="换牌阶段-取消"
            )

            if not cancel_ok:
                self.log("换牌阶段失败：检测到【杀】，但是没有找到 cancel.png")
                return False

            self.log("换牌阶段完成：已点击取消")
            return True

        self.log("当前没有检测到【杀】，尝试点击换牌")

        ok = self.click_template(
            "change_cards.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="换牌"
        )

        if not ok:
            self.log("换牌失败：没有找到换牌按钮")
            return False

        time.sleep(1.0)

        attack_count, _ = self.count_template(
            "attack.png",
            threshold=self.settings.THRESH_CARD
        )

        if attack_count > 0:
            self.log(f"换牌后检测到 {attack_count} 张【杀】，直接点击取消")
            cancel_ok = self.click_template(
                "cancel.png",
                threshold=self.settings.THRESH_BUTTON,
                desc="换牌阶段-取消"
            )

            if not cancel_ok:
                self.log("换牌阶段失败：换牌后检测到【杀】，但是没有找到 cancel.png")
                return False

            self.log("换牌阶段完成：已点击取消")
            return True

        self.log("换牌后仍未检测到【杀】，但换牌阶段先结束")
        return True

    # =========================================================
    # 牌局阶段 ②：武将技能阶段
    # =========================================================

    def battle_phase_acquire_skill(self):
        self.log("执行牌局阶段②：武将技能阶段")

        return self.click_template(
            "acquire.png",
            threshold=self.settings.THRESH_ACQUIRE,
            desc="摸体力值张牌"
        )

    # =========================================================
    # 牌局阶段 ③：将灵技能阶段 require
    # =========================================================

    def battle_phase_repairing_skill(self):
        self.log("执行牌局阶段③：将灵技能阶段 require")

        require_found = self.detect_require_prompt()

        if not require_found:
            self.log("没有检测到 require.png，本阶段不需要操作")
            return True

        self.log("检测到 require.png，开始执行将灵技能流程")

        if not self.wait_and_click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            timeout=3,
            desc="将灵技能-第一次确定"
        ):
            self.log("将灵技能失败：没有找到第一次 confirm.png")
            return False

        time.sleep(0.5)

        select_found = self.wait_any_template(
            ["select_figure.png", "select_figure_2.png"],
            threshold=self.settings.THRESH_SMALL,
            timeout=5,
            desc="选择一名其他角色"
        )

        if select_found is None:
            self.log("将灵技能失败：没有出现 select_figure.png 或 select_figure_2.png")
            return False

        if not self.click_template(
            "lijue.png",
            threshold=self.settings.THRESH_BOSS,
            desc="Boss 李傕"
        ):
            self.log("将灵技能失败：没有找到 lijue.png")
            return False

        self.log("将灵技能：已点击李傕，等待并点击 confirm.png")
        if not self.wait_and_click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            timeout=3,
            desc="选择李傕后确认"
        ):
            self.log("将灵技能失败：点击李傕后没有找到 confirm.png")
            return False

        self.log("将灵技能：确认李傕后休息 1 秒")
        time.sleep(1.0)

        self.log("将灵技能：开始持续检测 increase_damage.png / xiaorui.png")
        self.handle_after_lijue_prompts(duration=3.0)

        self.log("将灵技能：弹窗检测结束，休息 1 秒后等待 head.png")
        time.sleep(1.0)

        head_result = self.click_head_target()

        if head_result == "handled":
            self.log("将灵技能阶段完成")
            return True

        if head_result == "victory":
            self.log("将灵技能阶段完成：未检测到 head.png，但通过 save.png 后检测到胜利")
            return "victory"

        if head_result == "stopped":
            self.log("将灵技能阶段中止")
            return False

        self.log("将灵技能失败：未检测到 head.png，也没有通过 save.png 检测到胜利")
        return False

    # =========================================================
    # 牌局阶段 ④：出牌阶段
    # =========================================================

    def battle_phase_attack(self):
        self.log("执行牌局阶段④：出牌阶段")

        self.log("出牌阶段：第一次点击整理手牌")
        self.click_template(
            "sort.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="整理手牌-第一次"
        )

        time.sleep(0.5)

        self.log("出牌阶段：第二次点击整理手牌")
        self.click_template(
            "sort.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="整理手牌-第二次"
        )

        time.sleep(0.5)

        if not self.click_template(
            "attack.png",
            threshold=self.settings.THRESH_CARD,
            desc="杀"
        ):
            self.log("出牌阶段失败：没有找到 attack.png")
            return "failed"

        time.sleep(0.5)

        select_found = self.wait_any_template(
            ["select_figure.png", "select_figure_2.png"],
            threshold=self.settings.THRESH_SMALL,
            timeout=5,
            desc="选择一名其他角色"
        )

        if select_found is None:
            self.log("出牌阶段失败：没有出现 select_figure.png 或 select_figure_2.png")
            return "failed"

        if not self.click_template(
            "lijue.png",
            threshold=self.settings.THRESH_BOSS,
            desc="Boss 李傕"
        ):
            self.log("出牌阶段失败：没有找到 lijue.png")
            return "failed"

        self.log("出牌阶段：已点击李傕，等待并点击 confirm.png")
        if not self.wait_and_click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            timeout=3,
            desc="选择李傕后确认"
        ):
            self.log("出牌阶段失败：点击李傕后没有找到 confirm.png")
            return "failed"

        self.log("出牌阶段：确认李傕后休息 1 秒")
        time.sleep(1.0)

        self.log("出牌阶段：开始持续检测 increase_damage.png / xiaorui.png")
        self.handle_after_lijue_prompts(duration=3.0)

        self.log("出牌阶段：弹窗检测结束，休息 1.5 秒后等待 head.png")
        time.sleep(1.5)

        head_result = self.wait_head_after_attack(timeout=10)

        if head_result == "stopped":
            self.log("出牌阶段中止")
            return "failed"

        if head_result == "victory":
            self.log("出牌阶段完成：未检测到 head.png，但通过 save.png 后检测到胜利")
            return "victory"

        if head_result == "handled":
            self.log("出牌阶段：head.png 已处理，开始检测 save.png")
            self.handle_save_by_cancel()
        else:
            self.log("出牌阶段：未出现 head.png，且没有通过 save.png 检测到胜利，继续后续流程")

        victory_result = self.wait_victory_only_after_attack(timeout=10)

        if victory_result == "victory":
            self.log("出牌阶段完成：检测到胜利")
            return "victory"

        if victory_result == "stopped":
            self.log("出牌阶段中止")
            return "failed"

        clear_result = self.clear_cancel_until_acquire(timeout=100)

        if clear_result == "next_turn":
            self.log("出牌阶段完成：已进入下一轮武将技能阶段")
            return "next_turn"

        if clear_result == "victory":
            self.log("出牌阶段完成：清理阶段超时后检测到胜利")
            return "victory"

        if clear_result == "stopped":
            self.log("出牌阶段中止")
            return "failed"

        self.log("出牌阶段失败：没有检测到 victory，也没有检测到 acquire")
        return "failed"

    # =========================================================
    # 牌局循环：从当前轮开始，一直打到胜利
    # =========================================================

    def run_battle_until_victory(self, start_with_acquire=True, max_turns=30):
        self.log("开始执行牌局循环：直到胜利或停止")

        turn_id = 0

        while not self.stop_flag and turn_id < max_turns:
            turn_id += 1
            self.log(f"========== 牌局循环：第 {turn_id} 轮 ==========")

            if self.stage_check_victory():
                self.log("牌局循环：检测到胜利")
                return "victory"

            self.log("牌局循环：进入武将技能阶段")
            if not self.battle_phase_acquire_skill():
                self.log("牌局循环提示：武将技能阶段未成功，继续尝试后续阶段")

            self.log("牌局循环：武将技能阶段结束，等待 2 秒")
            if not self.sleep_with_pause(2):
                return "stopped"

            self.log("牌局循环：进入将灵技能阶段")
            repairing_result = self.battle_phase_repairing_skill()

            if repairing_result == "victory":
                self.log("牌局循环：将灵技能阶段检测到胜利")
                return "victory"

            if not repairing_result:
                self.log("牌局循环中断：将灵技能阶段失败")
                return "failed"

            self.log("牌局循环：将灵技能阶段结束，等待 2 秒")
            if not self.sleep_with_pause(2):
                return "stopped"

            self.log("牌局循环：进入出牌阶段")
            attack_result = self.battle_phase_attack()

            if attack_result == "victory":
                self.log("牌局循环：出牌阶段检测到胜利")
                return "victory"

            if attack_result == "next_turn":
                self.log("牌局循环：检测到 acquire.png，进入下一轮")
                continue

            if attack_result == "failed":
                self.log("牌局循环中断：出牌阶段失败")
                return "failed"

        self.log(f"牌局循环结束：超过最大轮数 {max_turns}")
        return "timeout"

    def battle_phase_attack_and_continue(self):
        self.log("执行出牌阶段，并在检测到 acquire.png 后继续后续轮次")

        attack_result = self.battle_phase_attack()

        if attack_result == "victory":
            self.log("出牌阶段连续流程：已胜利")
            return True

        if attack_result == "next_turn":
            self.log("出牌阶段连续流程：检测到 acquire.png，继续执行下一轮")
            result = self.run_battle_until_victory(max_turns=30)
            return result == "victory"

        self.log("出牌阶段连续流程：出牌阶段失败或未进入下一轮")
        return False

    # =========================================================
    # 备用处理
    # =========================================================

    def battle_handle_confirm(self):
        self.log("备用测试：尝试点击确定")

        return self.click_template(
            "confirm.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="确定"
        )

    def battle_handle_skip(self):
        self.log("备用测试：尝试点击跳过")

        return self.click_template(
            "skip.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="跳过"
        )

    def battle_handle_close(self):
        self.log("备用测试：尝试关闭弹窗")

        return self.click_template(
            "close.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="关闭"
        )

    def stage_battle_once(self):
        self.log("执行阶段：牌局单步备用处理")

        if self.stage_check_victory():
            return True

        handlers = [
            self.battle_handle_close,
            self.battle_handle_confirm,
            self.battle_handle_skip,
        ]

        for handler in handlers:
            ok = handler()
            if ok:
                return True

        self.log("牌局单步备用处理：没有发现可处理按钮")
        return False

    def stage_battle_core_test(self):
        self.log("开始执行牌局核心流程测试")

        if not self.battle_phase_change_cards():
            self.log("牌局核心流程中断：换牌阶段失败")
            return False

        if not self.sleep_with_pause(0.8):
            return False

        result = self.run_battle_until_victory(max_turns=30)

        return result == "victory"

    def stage_battle_loop(self, max_seconds=30):
        self.log(f"开始牌局循环测试，最长 {max_seconds} 秒")

        start_time = time.time()

        while time.time() - start_time < max_seconds:
            if self.stop_flag:
                self.log("收到停止信号，退出牌局循环测试")
                return False

            if self.paused:
                time.sleep(0.2)
                continue

            if self.stage_check_victory():
                self.log("牌局循环测试中检测到胜利")
                return True

            self.stage_battle_once()

            time.sleep(0.3)

        self.log("牌局循环测试结束：达到时间上限")
        return False

    # =========================================================
    # 完整流程：连续循环
    # =========================================================

    def run_one_full_cycle(self):
        self.log("完整流程：开始连续运行")

        self.stop_flag = False
        self.running = True

        game_id = 0

        try:
            while not self.stop_flag:
                game_id += 1
                self.log(f"========== 完整流程：第 {game_id} 局开始 ==========")

                self.log("完整流程：点击开始挑战")
                if not self.stage_start_challenge():
                    self.log("完整流程中断：开始挑战失败")
                    break

                self.log("完整流程：开始挑战后等待 5 秒")
                if not self.sleep_with_pause(5):
                    break

                self.log("完整流程：进入换牌阶段")
                if not self.battle_phase_change_cards():
                    self.log("完整流程中断：换牌阶段失败")
                    break

                self.log("完整流程：换牌阶段结束，等待 5 秒")
                if not self.sleep_with_pause(5):
                    break

                self.log("完整流程：进入牌局循环")
                result = self.run_battle_until_victory(max_turns=30)

                if result == "victory":
                    self.log("完整流程：本局胜利，等待 5 秒后进入下一局")
                    if not self.sleep_with_pause(5):
                        break
                    continue

                if result == "stopped":
                    self.log("完整流程：收到停止信号")
                    break

                self.log(f"完整流程中断：牌局循环结果={result}")
                break

            self.log("完整流程：连续运行已停止")

        except pyautogui.FailSafeException:
            self.log("触发 FailSafe：鼠标移动到左上角，脚本停止")

        except Exception as e:
            self.log(f"完整流程异常：{e}")

        finally:
            self.running = False
            self.log("完整流程结束")