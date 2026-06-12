import time
import random
import threading
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
import pyautogui

from app_paths import DEBUG_DIR, LEARNED_TEMPLATE_DIR, TEMPLATE_DIR
from profile_registry import resolve_general_profile, resolve_spirit_profile
from settings_store import BotSettings
from template_registry import get_template_display_name, get_template_meta


pyautogui.FAILSAFE = True

# =========================================================
# 自动化核心类
# =========================================================

class GameBot:
    def __init__(
        self,
        log_func=None,
        settings=None,
        minimize_func=None,
        supervision_func=None,
        general_profile=None,
        spirit_profile=None,
    ):
        self.log_func = log_func or print
        self.settings = settings or BotSettings()
        self.minimize_func = minimize_func
        self.supervision_func = supervision_func
        self.general_profile = resolve_general_profile(general_profile)
        self.spirit_profile = resolve_spirit_profile(spirit_profile)

        self.running = False
        self.paused = False
        self.stop_flag = False

        self.click_lock = threading.Lock()
        self.supervision_lock = threading.Lock()
        self.supervision_denied_until = {}
        self.last_match_sources = {}
        self.popup_reject_until = {}

        self.increase_damage_last_click_time = 0
        self.xiaorui_last_click_time = 0
        self.save_cancel_last_click_time = 0
        self.cancel_last_click_time = 0
        self.kebineng_last_select_all_anchor = None

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

    def minimize_ui_window(self):
        """
        最小化主 UI，避免 UI 遮挡搜索框等按钮。
        minimize_func 由 main.py 传入。
        """
        if self.minimize_func is None:
            self.log("没有传入 UI 最小化函数，跳过最小化")
            return False

        try:
            self.minimize_func()
            time.sleep(0.5)
            return True
        except Exception as e:
            self.log(f"最小化 UI 失败：{e}")
            return False

    def resize_all_browser_windows(self, width=1280, height=800, move_to_left_top=True):
        """
        将当前所有常见浏览器窗口统一调整为指定尺寸。

        这样完整流程开始前，游戏浏览器的画面比例会先固定，
        后续模板匹配更稳定。

        说明：
        1. 不寻找具体游戏窗口，只处理所有浏览器窗口。
        2. 自动排除本工具窗口“李傕列传”。
        3. 如果窗口处于最大化状态，会先 restore，再 resize。
        4. 默认把浏览器移动到左上角，方便模板在固定画面下匹配。
        """
        self.log(f"完整流程第一步：调整所有浏览器窗口为 {width}x{height}")

        browser_keywords = [
            "chrome",
            "edge",
            "firefox",
            "opera",
            "brave",
            "vivaldi",
            "browser",
            "浏览器",
            "谷歌",
            "火狐",
            "microsoft edge",
            "360极速",
            "360安全",
            "qq浏览器",
            "搜狗高速",
            "uc浏览器",
        ]

        try:
            windows = pyautogui.getAllWindows()
        except Exception as e:
            self.log(f"获取窗口列表失败：{e}")
            return False

        changed_count = 0

        for win in windows:
            try:
                title = win.title or ""
            except Exception:
                continue

            if not title.strip():
                continue

            lower_title = title.lower()

            # 排除自己的 tkinter UI
            if "李傕列传" in title:
                continue

            is_browser = any(key in lower_title for key in browser_keywords)

            if not is_browser:
                continue

            try:
                self.log(f"调整浏览器窗口：{title}")

                # 最大化窗口必须先还原，否则 resizeTo 可能无效
                if getattr(win, "isMaximized", False):
                    win.restore()
                    time.sleep(0.3)

                # 最小化窗口也先还原
                if getattr(win, "isMinimized", False):
                    win.restore()
                    time.sleep(0.3)

                if move_to_left_top:
                    win.moveTo(0, 0)
                    time.sleep(0.15)

                win.resizeTo(width, height)
                time.sleep(0.25)

                changed_count += 1

            except Exception as e:
                self.log(f"调整窗口失败：{title} | {e}")

        if changed_count == 0:
            self.log("没有检测到浏览器窗口，跳过窗口尺寸调整")
            return False

        self.log(f"浏览器窗口尺寸调整完成，共处理 {changed_count} 个窗口")
        return True

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

    def _load_image_file(self, path, log_missing=False):
        if not path.exists():
            if log_missing:
                self.log(f"模板不存在：{path}")
            return None

        try:
            data = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception as e:
            self.log(f"模板读取异常：{path} | {e}")
            return None

        if img is None:
            self.log(f"模板读取失败：{path}")
            return None

        return img

    def template_candidate_paths(self, template_name):
        meta = get_template_meta(template_name)
        paths = [TEMPLATE_DIR / meta.path]
        legacy_path = TEMPLATE_DIR / template_name

        if legacy_path not in paths:
            paths.append(legacy_path)

        return paths

    def learned_template_dirs(self, template_name):
        meta = get_template_meta(template_name)
        dirs = [LEARNED_TEMPLATE_DIR / meta.learned_subdir]
        legacy_dir = LEARNED_TEMPLATE_DIR / Path(template_name).stem

        if legacy_dir not in dirs:
            dirs.append(legacy_dir)

        return dirs

    def load_template(self, template_name):
        for path in self.template_candidate_paths(template_name):
            image = self._load_image_file(path)

            if image is not None:
                return image

        paths_text = " 或 ".join(str(path) for path in self.template_candidate_paths(template_name))
        self.log(f"模板不存在：{paths_text}")
        return None

    def learned_template_dir(self, template_name):
        return self.learned_template_dirs(template_name)[0]

    def load_template_variants(self, template_name):
        variants = []
        display_name = get_template_display_name(template_name)

        for index, base_path in enumerate(self.template_candidate_paths(template_name)):
            base_template = self._load_image_file(base_path)

            if base_template is None:
                continue

            label = display_name
            if index > 0:
                label = f"{display_name} / 旧路径"

            variants.append({
                "label": label,
                "path": base_path,
                "image": base_template,
            })
            break

        if not variants:
            paths_text = " 或 ".join(str(path) for path in self.template_candidate_paths(template_name))
            self.log(f"模板不存在：{paths_text}")

        for learned_dir in self.learned_template_dirs(template_name):
            if not learned_dir.exists():
                continue

            for path in sorted(learned_dir.glob("*.png")):
                learned_template = self._load_image_file(path)

                if learned_template is None:
                    continue

                variants.append({
                    "label": f"{display_name} / 学习：{path.name}",
                    "path": path,
                    "image": learned_template,
                })

        return variants

    def save_learned_template(self, template_name, image):
        learned_dir = self.learned_template_dir(template_name)
        learned_dir.mkdir(parents=True, exist_ok=True)

        prefix = get_template_meta(template_name).learned_filename_prefix
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        path = learned_dir / filename

        try:
            image = np.ascontiguousarray(image)
            success, encoded_img = cv2.imencode(".png", image)

            if success:
                encoded_img.tofile(str(path))
                return path

            self.log(f"学习模板编码失败：{path}")
            return None

        except Exception as e:
            self.log(f"保存学习模板异常：{e}")
            return None

    # -------------------------
    # 模板匹配
    # -------------------------

    def game_search_region(self, screen=None):
        if screen is not None:
            screen_h, screen_w = screen.shape[:2]
        else:
            try:
                screen_w, screen_h = pyautogui.size()
            except Exception:
                return None

        game_w = int(getattr(self.settings, "GAME_REGION_WIDTH", 1280))
        game_h = int(getattr(self.settings, "GAME_REGION_HEIGHT", 800))
        padding = int(getattr(self.settings, "GAME_REGION_PADDING", 60))

        max_x = min(screen_w, game_w + padding)
        max_y = min(screen_h, game_h + padding)

        if max_x <= 0 or max_y <= 0:
            return None

        return 0, 0, max_x, max_y

    def intersect_regions(self, region_a, region_b):
        if region_a is None:
            return region_b

        if region_b is None:
            return region_a

        ax, ay, aw, ah = region_a
        bx, by, bw, bh = region_b
        x1 = max(int(ax), int(bx))
        y1 = max(int(ay), int(by))
        x2 = min(int(ax + aw), int(bx + bw))
        y2 = min(int(ay + ah), int(by + bh))

        if x2 <= x1 or y2 <= y1:
            return None

        return x1, y1, x2 - x1, y2 - y1

    def _search_area(self, screen, region):
        game_region = self.game_search_region(screen)
        search_region = self.intersect_regions(region, game_region)

        if search_region is None:
            return screen[0:0, 0:0], 0, 0

        x, y, w, h = search_region
        return screen[y:y + h, x:x + w], x, y

    def _match_one_template(self, screen, search_img, offset_x, offset_y, variant):
        template = variant["image"]
        th, tw = template.shape[:2]
        sh, sw = search_img.shape[:2]

        if sh < th or sw < tw:
            return None

        result = cv2.matchTemplate(search_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if not np.isfinite(max_val):
            return None

        top_left_x = offset_x + max_loc[0]
        top_left_y = offset_y + max_loc[1]
        crop = screen[top_left_y:top_left_y + th, top_left_x:top_left_x + tw]

        return {
            "x": top_left_x,
            "y": top_left_y,
            "w": tw,
            "h": th,
            "conf": float(max_val),
            "variant": variant,
            "crop": crop.copy(),
            "result": result,
        }

    def _best_template_match(self, template_name, region=None, screen=None):
        if screen is None:
            screen = self.screenshot_bgr()

        variants = self.load_template_variants(template_name)

        if not variants:
            return None

        search_img, offset_x, offset_y = self._search_area(screen, region)

        if search_img.size == 0:
            return None

        best = None

        for variant in variants:
            match = self._match_one_template(
                screen,
                search_img,
                offset_x,
                offset_y,
                variant
            )

            if match is None:
                continue

            if best is None or match["conf"] > best["conf"]:
                best = match

        return best

    def _match_to_rect(self, match):
        return match["x"], match["y"], match["w"], match["h"], match["conf"]

    def _remember_template_match(self, template_name, match):
        if match is None:
            return

        variant = match.get("variant") or {}
        path = variant.get("path")

        self.last_match_sources[template_name] = {
            "label": variant.get("label", template_name),
            "path": str(path) if path is not None else "",
            "x": match["x"],
            "y": match["y"],
            "w": match["w"],
            "h": match["h"],
            "conf": match["conf"],
        }

    def get_last_match_source_text(self, template_name):
        source = self.last_match_sources.get(template_name)

        if not source:
            return "来源=未知"

        label = source.get("label") or template_name
        path = source.get("path") or ""

        if path:
            return f"来源={label} ({path})"

        return f"来源={label}"

    def is_top_right_click(self, x, y):
        try:
            screen_w, screen_h = pyautogui.size()
        except Exception:
            return False

        return x >= screen_w * 0.75 and y <= screen_h * 0.25

    def log_if_top_right_click(self, desc, x, y, conf=None, source_text=None):
        if not self.is_top_right_click(x, y):
            return

        parts = [
            f"可疑点击：{desc}",
            f"坐标=({x}, {y})",
        ]

        if conf is not None:
            parts.append(f"置信度={conf:.3f}")

        if source_text:
            parts.append(source_text)

        parts.append("位置在屏幕右上区域")
        self.log(" | ".join(parts))

    def region_around_point(self, x, y, left=420, top=90, right=420, bottom=320):
        try:
            screen_w, screen_h = pyautogui.size()
        except Exception:
            return None

        x1 = max(0, int(x - left))
        y1 = max(0, int(y - top))
        x2 = min(screen_w, int(x + right))
        y2 = min(screen_h, int(y + bottom))

        if x2 <= x1 or y2 <= y1:
            return None

        region = x1, y1, x2 - x1, y2 - y1
        return self.intersect_regions(region, self.game_search_region())

    def popup_confirm_region(self, popup_x, popup_y):
        return self.region_around_point(
            popup_x,
            popup_y,
            left=420,
            top=80,
            right=420,
            bottom=360
        )

    def skill_popup_search_region(self):
        try:
            screen_w, screen_h = pyautogui.size()
        except Exception:
            return None

        # 完整流程会把游戏浏览器固定到左上角 1280x800。
        # 技能提示弹窗在游戏区域中下部，限制范围可避开浏览器/桌面右上角误匹配。
        game_w = min(screen_w, int(getattr(self.settings, "GAME_REGION_WIDTH", 1280)))
        game_h = min(screen_h, int(getattr(self.settings, "GAME_REGION_HEIGHT", 800)))
        top = int(game_h * 0.32)
        height = game_h - top

        if game_w <= 0 or height <= 0:
            return None

        region = 0, top, game_w, height
        return self.intersect_regions(region, self.game_search_region())

    def should_skip_rejected_popup(self, template_name, x, y):
        rejected = self.popup_reject_until.get(template_name)

        if not rejected:
            return False

        rejected_x, rejected_y, until_time = rejected

        if time.time() >= until_time:
            self.popup_reject_until.pop(template_name, None)
            return False

        distance = ((x - rejected_x) ** 2 + (y - rejected_y) ** 2) ** 0.5
        return distance < 80

    def reject_popup_candidate(self, template_name, x, y, seconds=3.0):
        self.popup_reject_until[template_name] = (x, y, time.time() + seconds)
        display_name = get_template_display_name(template_name)
        self.log(
            f"忽略疑似误识别弹窗：{display_name} | "
            f"坐标=({x}, {y}) | {seconds:.1f} 秒内不再处理附近候选"
        )

    def _maybe_accept_supervised_match(self, template_name, threshold, match):
        if match is None:
            return False

        display_name = get_template_display_name(template_name)

        if match["conf"] >= threshold:
            return True

        if not getattr(self.settings, "SUPERVISION_ENABLED", True):
            return False

        if self.supervision_func is None:
            return False

        min_conf = getattr(self.settings, "SUPERVISION_MIN_CONF", 0.50)

        if match["conf"] < min_conf:
            return False

        now = time.time()

        with self.supervision_lock:
            denied_until = self.supervision_denied_until.get(template_name, 0)

            if denied_until > now:
                return False

        crop = match.get("crop")

        if crop is None or crop.size == 0:
            return False

        try:
            accepted = self.supervision_func(
                template_name=template_name,
                confidence=match["conf"],
                threshold=threshold,
                image=crop.copy(),
            )
        except Exception as e:
            self.log(f"人工监督弹窗异常：{display_name} | {e}")
            return False

        if accepted:
            path = self.save_learned_template(template_name, crop)

            if path is not None:
                self.log(
                    f"人工确认通过：{display_name} | "
                    f"置信度={match['conf']:.3f} | 已保存学习模板：{path}"
                )
            else:
                self.log(
                    f"人工确认通过：{display_name} | "
                    f"置信度={match['conf']:.3f} | 学习模板保存失败"
                )

            with self.supervision_lock:
                self.supervision_denied_until.pop(template_name, None)

            return True

        with self.supervision_lock:
            self.supervision_denied_until[template_name] = time.time() + 6.0

        self.log(
            f"人工确认否定：{display_name} | "
            f"置信度={match['conf']:.3f} | 6 秒内不再询问此模板"
        )
        return False

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

        match = self._best_template_match(template_name, region)

        if not self._maybe_accept_supervised_match(template_name, threshold, match):
            return None

        self._remember_template_match(template_name, match)

        center_x = match["x"] + match["w"] // 2
        center_y = match["y"] + match["h"] // 2

        return center_x, center_y, match["conf"]

    def find_template_rect(self, template_name, threshold=None, region=None):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        match = self._best_template_match(template_name, region)

        if not self._maybe_accept_supervised_match(template_name, threshold, match):
            max_conf = 0.0 if match is None else match["conf"]
            self.log(
                f"匹配不足：{template_name} | "
                f"最高置信度={max_conf:.3f} | 阈值={threshold:.3f}"
            )
            return None

        self._remember_template_match(template_name, match)

        return self._match_to_rect(match)

    def find_all_templates(
        self,
        template_name,
        threshold=None,
        region=None,
        min_distance=20,
        allow_supervision=True
    ):
        if threshold is None:
            threshold = self.settings.DEFAULT_THRESHOLD

        screen = self.screenshot_bgr()
        variants = self.load_template_variants(template_name)

        if not variants:
            return []

        search_img, offset_x, offset_y = self._search_area(screen, region)

        if search_img.size == 0:
            return []

        candidates = []
        best = None

        for variant in variants:
            match = self._match_one_template(
                screen,
                search_img,
                offset_x,
                offset_y,
                variant
            )

            if match is None:
                continue

            if best is None or match["conf"] > best["conf"]:
                best = match

            result = match["result"]
            th = match["h"]
            tw = match["w"]
            ys, xs = np.where(result >= threshold)

            for x, y in zip(xs, ys):
                conf = result[y, x]
                cx = offset_x + x + tw // 2
                cy = offset_y + y + th // 2
                candidates.append((cx, cy, float(conf)))

        if allow_supervision and not candidates and self._maybe_accept_supervised_match(template_name, threshold, best):
            self._remember_template_match(template_name, best)
            cx = best["x"] + best["w"] // 2
            cy = best["y"] + best["h"] // 2
            candidates.append((cx, cy, best["conf"]))

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
    # 将灵技能询问检测
    # -------------------------

    def detect_require_prompt(self):
        template_name = self.spirit_profile.prompt_template
        threshold_name = self.spirit_profile.prompt_threshold_name

        if not template_name or not threshold_name:
            self.log(f"{self.spirit_profile.name} 没有将灵技能触发模板，跳过检测")
            return False

        threshold = getattr(self.settings, threshold_name)

        found = self.find_template(
            template_name,
            threshold=threshold
        )

        if found is None:
            self.log(f"没有检测到 {template_name}")
            return False

        x, y, conf = found
        self.log(f"检测到 {template_name} | 置信度={conf:.3f} | 坐标=({x}, {y})")
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
        source_text = self.get_last_match_source_text(template_name)

        self.log(
            f"找到并点击：{desc or template_name} | "
            f"置信度={conf:.3f} | 坐标=({x}, {y}) | {source_text}"
        )
        self.log_if_top_right_click(desc or template_name, x, y, conf, source_text)

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
                source_text = self.get_last_match_source_text(template_name)
                self.log(
                    f"已出现：{desc or template_name} | "
                    f"置信度={conf:.3f} | 坐标=({x}, {y}) | {source_text}"
                )
                return found

            time.sleep(0.25)

        self.log(f"等待超时：{desc or template_name}")
        return None

    def wait_template_rect(self, template_name, threshold=None, timeout=5, region=None, desc=None):
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

            rect = self.find_template_rect(template_name, threshold, region)

            if rect is not None:
                x, y, w, h, conf = rect
                source_text = self.get_last_match_source_text(template_name)
                self.log(
                    f"已出现：{desc or template_name} | "
                    f"置信度={conf:.3f} | 区域=({x}, {y}, {w}, {h}) | {source_text}"
                )
                return rect

            time.sleep(0.25)

        self.log(f"等待超时：{desc or template_name}")
        return None

    def wait_and_click_template(self, template_name, threshold=None, timeout=5, region=None, desc=None):
        found = self.wait_template(template_name, threshold, timeout, region, desc)

        if found is None:
            return False

        x, y, conf = found
        source_text = self.get_last_match_source_text(template_name)
        self.log_if_top_right_click(desc or template_name, x, y, conf, source_text)
        self.safe_click(x, y)
        self.log(f"等待后点击：{desc or template_name} | 坐标=({x}, {y}) | {source_text}")
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

        popup_region = self.skill_popup_search_region()
        found = self.find_template_quiet(
            "increase_damage.png",
            threshold=self.settings.THRESH_POPUP,
            region=popup_region
        )

        if found is None:
            return False

        x, y, conf = found

        if self.should_skip_rejected_popup("increase_damage.png", x, y):
            return False

        confirm_region = self.popup_confirm_region(x, y)
        self.log(
            f"检测到 increase_damage.png | 置信度={conf:.3f} | "
            f"坐标=({x}, {y}) | 弹窗搜索区域={popup_region} | "
            f"确认按钮搜索区域={confirm_region}"
        )

        ok = self.click_template(
            "confirm.png",
            threshold=max(self.settings.THRESH_CONFIRM, 0.60),
            region=confirm_region,
            desc="increase_damage-确定"
        )

        if ok:
            self.increase_damage_last_click_time = time.time()
            self.log("已处理 increase_damage：点击确定")
            return True

        self.log("检测到 increase_damage，但没有找到 confirm.png")
        self.reject_popup_candidate("increase_damage.png", x, y)
        return False

    def handle_xiaorui(self):
        now = time.time()

        if now - self.xiaorui_last_click_time < 0.8:
            return False

        popup_region = self.skill_popup_search_region()
        found = self.find_template_quiet(
            "xiaorui.png",
            threshold=self.settings.THRESH_POPUP,
            region=popup_region
        )

        if found is None:
            return False

        x, y, conf = found

        if self.should_skip_rejected_popup("xiaorui.png", x, y):
            return False

        confirm_region = self.popup_confirm_region(x, y)
        self.log(
            f"检测到 xiaorui.png | 置信度={conf:.3f} | "
            f"坐标=({x}, {y}) | 弹窗搜索区域={popup_region} | "
            f"确认按钮搜索区域={confirm_region}"
        )

        ok = self.click_template(
            "confirm.png",
            threshold=max(self.settings.THRESH_CONFIRM, 0.60),
            region=confirm_region,
            desc="xiaorui-确定"
        )

        if ok:
            self.xiaorui_last_click_time = time.time()
            self.log("已处理 xiaorui：点击确定")
            return True

        self.log("检测到 xiaorui，但没有找到 confirm.png")
        self.reject_popup_candidate("xiaorui.png", x, y)
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
        当前武将部位模板没检测到时调用。

        逻辑：
        1. 检测 save.png
        2. 如果检测到 save.png，则点击 cancel.png
        3. 然后在 victory_timeout 秒内等待 victory.png
        4. 检测到 victory.png 返回 "victory"
        5. 没检测到返回 "not_found"
        """
        target_template = self.general_profile.target_template or "武将部位模板"

        self.log(f"{context}：未检测到 {target_template}，开始检测 save.png")

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

        如果检测到当前武将部位模板：
            点击头部、胸部，返回 "handled"

        如果没检测到当前武将部位模板：
            检测 save.png，点击 cancel.png，然后 15 秒内检测 victory.png。
        """
        target_template = self.general_profile.target_template

        if not target_template:
            self.log(f"{self.general_profile.name} 无部位选择技能效果，跳过部位选择流程")
            return "skipped"

        target_threshold = getattr(self.settings, self.general_profile.target_threshold_name)

        self.log(f"等待{self.general_profile.target_desc} {target_template} 出现")

        rect = None
        start = time.time()
        timeout = 6

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log(f"收到停止信号，停止等待 {target_template}")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            rect = self.find_template_rect(
                target_template,
                threshold=target_threshold
            )

            if rect is not None:
                break

            time.sleep(0.25)

        if rect is None:
            self.log(f"未检测到{self.general_profile.target_desc} {target_template}")
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
            f"检测到 {target_template} | 置信度={conf:.3f} | "
            f"模板区域=({x}, {y}, {w}, {h})"
        )

        self.log(f"先点击头部位置=({head_x}, {head_y})")
        self.log_if_top_right_click(f"{target_template}-头部位置", head_x, head_y, conf)
        self.safe_click(head_x, head_y, jitter=2)

        time.sleep(0.4)

        self.log(f"再点击胸部位置=({chest_x}, {chest_y})")
        self.log_if_top_right_click(f"{target_template}-胸部位置", chest_x, chest_y, conf)
        self.safe_click(chest_x, chest_y, jitter=2)

        return "handled"

    def wait_head_after_attack(self, timeout=10):
        """
        出牌阶段出杀后使用。

        如果检测到当前武将部位模板：
            点击头部、胸部，返回 "handled"

        如果没检测到当前武将部位模板：
            检测 save.png，点击 cancel.png，然后 15 秒内检测 victory.png。
        """
        target_template = self.general_profile.target_template

        if not target_template:
            self.log(f"{self.general_profile.name} 无出杀后部位选择技能效果，跳过部位选择流程")
            return "skipped"

        target_threshold = getattr(self.settings, self.general_profile.target_threshold_name)

        self.log(f"出杀后等待 {target_template}，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log(f"收到停止信号，停止等待出杀后的 {target_template}")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            rect = self.find_template_rect(
                target_template,
                threshold=target_threshold
            )

            if rect is not None:
                x, y, w, h, conf = rect

                head_x = int(x + w * self.settings.BODY_HEAD_REL_X)
                head_y = int(y + h * self.settings.BODY_HEAD_REL_Y)

                chest_x = int(x + w * self.settings.BODY_CHEST_REL_X)
                chest_y = int(y + h * self.settings.BODY_CHEST_REL_Y)

                self.log(
                    f"出杀后检测到 {target_template} | 置信度={conf:.3f} | "
                    f"模板区域=({x}, {y}, {w}, {h})"
                )

                self.log(f"先点击头部位置=({head_x}, {head_y})")
                self.log_if_top_right_click(f"出杀后 {target_template}-头部位置", head_x, head_y, conf)
                self.safe_click(head_x, head_y, jitter=2)

                time.sleep(0.4)

                self.log(f"再点击胸部位置=({chest_x}, {chest_y})")
                self.log_if_top_right_click(f"出杀后 {target_template}-胸部位置", chest_x, chest_y, conf)
                self.safe_click(chest_x, chest_y, jitter=2)

                return "handled"

            time.sleep(0.25)

        self.log(f"出杀后没有检测到 {target_template}")
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
        2. 等待当前武将的技能阶段模板出现。
        3. 如果 timeout 秒内没等到武将技能模板，再额外检测一次 victory.png。
           - 有 victory.png：返回 victory，让完整流程进入下一局。
           - 没有 victory.png：返回 timeout。
        """
        template_name = self.general_profile.skill_template
        threshold = getattr(self.settings, self.general_profile.skill_threshold_name)

        self.log(f"进入下一轮清理阶段：持续点击 cancel.png，直到 {template_name} 出现，最长 {timeout} 秒")

        start = time.time()

        while time.time() - start < timeout:
            if self.stop_flag:
                self.log("收到停止信号，退出下一轮清理阶段")
                return "stopped"

            if self.paused:
                time.sleep(0.2)
                continue

            acquire_found = self.find_template_quiet(
                template_name,
                threshold=threshold
            )

            if acquire_found is not None:
                x, y, conf = acquire_found
                self.log(f"检测到武将技能阶段 {template_name} | 置信度={conf:.3f}")
                return "next_turn"

            if self.handle_cancel_only():
                time.sleep(0.3)
                continue

            time.sleep(0.3)

        self.log(f"下一轮清理阶段超时：{timeout} 秒内未检测到 {template_name}，开始额外检测 victory.png")

        victory_found = self.find_template_quiet(
            "victory.png",
            threshold=self.settings.THRESH_VICTORY
        )

        if victory_found is not None:
            x, y, conf = victory_found
            self.log(f"超时后检测到 victory.png | 置信度={conf:.3f} | 判定本局胜利")
            return "victory"

        self.log(f"下一轮清理阶段超时：未检测到 {template_name}，也未检测到 victory.png")
        return "timeout"

    # -------------------------
    # 轲比能出牌阶段辅助
    # -------------------------

    def bottom_right_action_region(self):
        game_region = self.game_search_region()

        if game_region is None:
            return None

        x, y, w, h = game_region
        left = x + int(w * 0.62)
        top = y + int(h * 0.70)
        region = left, top, x + w - left, y + h - top
        return self.intersect_regions(region, game_region)

    def kebineng_card_points_from_anchor(self, anchor_x=None, anchor_y=None):
        """
        full.png 中 select_all.png 中心为 (846, 614)，首排手牌中心约在 y=593。
        用全选按钮作为锚点，避免直接写死屏幕绝对坐标。
        """
        if anchor_x is not None and anchor_y is not None:
            offsets = [
                (-716, -21),
                (-631, -21),
                (-545, -21),
                (-460, -21),
                (-373, -21),
                (-288, -21),
                (-202, -21),
                (-115, -21),
                (-29, -21),
            ]
            return [
                (int(anchor_x + dx), int(anchor_y + dy))
                for dx, dy in offsets
            ]

        game_region = self.game_search_region()

        if game_region is None:
            return []

        x, y, w, h = game_region
        reference_w = 1159
        reference_h = 639
        reference_points = [
            (130, 593),
            (215, 593),
            (301, 593),
            (386, 593),
            (473, 593),
            (558, 593),
            (644, 593),
            (731, 593),
            (817, 593),
        ]

        return [
            (int(x + w * px / reference_w), int(y + h * py / reference_h))
            for px, py in reference_points
        ]

    def kebineng_hand_card_region(self, screen=None):
        game_region = self.game_search_region(screen)

        if game_region is None:
            return None

        x, y, w, h = game_region
        left = x + int(w * 0.04)
        top = y + int(h * 0.76)
        right = x + int(w * 0.76)
        bottom = y + h

        if right <= left or bottom <= top:
            return None

        return left, top, right - left, bottom - top

    def detect_kebineng_hand_card_points(self):
        """
        每次出牌前重新识别当前手牌卡位。

        牌面每局都会变，不能依赖固定卡牌模板；这里只检测底部手牌区域
        连续的卡牌亮色区域，再按当前宽度估算卡位中心。
        """
        screen = self.screenshot_bgr()
        region = self.kebineng_hand_card_region(screen)

        if region is None:
            return []

        x, y, w, h = region
        roi = screen[y:y + h, x:x + w]

        if roi.size == 0:
            return []

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        light_mask = gray > 135
        paper_mask = (hsv[:, :, 1] < 85) & (gray > 80)
        mask = np.where(light_mask | paper_mask, 255, 0).astype(np.uint8)

        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9))
        open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel, iterations=1)

        projection = (mask > 0).sum(axis=0)
        active_threshold = max(12, int(h * 0.22))
        active = projection > active_threshold

        segments = []
        in_segment = False
        start = 0

        for index, is_active in enumerate(active):
            if is_active and not in_segment:
                start = index
                in_segment = True
            elif not is_active and in_segment:
                if index - start >= 20:
                    segments.append((start, index - 1))
                in_segment = False

        if in_segment and len(active) - start >= 20:
            segments.append((start, len(active) - 1))

        merged_segments = []

        for start, end in segments:
            if merged_segments and start - merged_segments[-1][1] <= 18:
                last_start, _ = merged_segments[-1]
                merged_segments[-1] = (last_start, end)
            else:
                merged_segments.append((start, end))

        game_region = self.game_search_region(screen)
        game_w = w if game_region is None else game_region[2]
        card_pitch = max(55, min(105, int(game_w * 86 / 1159)))
        card_y = y + int(h * 0.70)
        points = []

        for start, end in merged_segments:
            segment_w = end - start + 1

            if segment_w < 24:
                continue

            count = max(1, int(round(segment_w / card_pitch)))
            count = min(count, 12)
            pitch = segment_w / count

            for index in range(count):
                card_x = int(x + start + pitch * (index + 0.5))
                points.append((card_x, card_y))

        final_points = []

        for card_x, card_y in sorted(points):
            if not final_points or abs(card_x - final_points[-1][0]) > 35:
                final_points.append((card_x, card_y))

        return final_points

    def detect_kebineng_card_marker_points(self):
        region = self.kebineng_hand_card_region()
        found = self.find_all_templates(
            "kebineng_card_marker.png",
            threshold=max(self.settings.THRESH_CARD, 0.70),
            region=region,
            min_distance=45,
            allow_supervision=False
        )

        points = []

        for marker_x, marker_y, conf in sorted(found):
            card_x = int(marker_x)
            card_y = int(marker_y - 30)
            points.append((card_x, card_y, conf))

        return points

    def choose_kebineng_hand_card_point(self, rejected_xs):
        marker_points = self.detect_kebineng_card_marker_points()

        if marker_points:
            points = [(x, y) for x, y, _ in marker_points]
            source = "寇旌杀模板识别"
        else:
            points = self.detect_kebineng_hand_card_points()
            source = "截图识别"

        if not points:
            anchor = self.kebineng_last_select_all_anchor

            if anchor is not None:
                points = self.kebineng_card_points_from_anchor(*anchor)
                source = "锚点兜底"
            else:
                points = self.kebineng_card_points_from_anchor()
                source = "固定兜底"

        if not points:
            return None, [], source

        for point in points:
            if all(abs(point[0] - rejected_x) > 35 for rejected_x in rejected_xs):
                return point, points, source

        return None, points, source

    def detect_victory_quiet(self, context):
        found = self.find_template_quiet(
            "victory.png",
            threshold=self.settings.THRESH_VICTORY
        )

        if found is None:
            return False

        x, y, conf = found
        self.log(f"{context}：检测到 victory.png | 置信度={conf:.3f} | 坐标=({x}, {y})")
        return True

    def detect_current_general_skill_quiet(self, context, region=None):
        template_name = self.general_profile.skill_template
        threshold = getattr(self.settings, self.general_profile.skill_threshold_name)

        found = self.find_template_quiet(
            template_name,
            threshold=threshold,
            region=region
        )

        if found is None:
            return False

        x, y, conf = found
        self.log(f"{context}：检测到 {template_name} | 置信度={conf:.3f} | 坐标=({x}, {y})")
        return True

    def handle_kebineng_koujing_prompt(self):
        prompt_region = self.skill_popup_search_region()

        found = self.wait_template(
            "koujing.png",
            threshold=getattr(self.settings, self.general_profile.skill_threshold_name),
            timeout=8,
            region=prompt_region,
            desc="轲比能-寇旌"
        )

        if found is None:
            self.log("轲比能出牌阶段：没有检测到寇旌提示")
            return None

        all_region = self.bottom_right_action_region()
        select_all_rect = self.wait_template_rect(
            "select_all.png",
            threshold=max(self.settings.THRESH_BUTTON, 0.60),
            timeout=3,
            region=all_region,
            desc="寇旌-全选"
        )

        if select_all_rect is None:
            self.log("轲比能出牌阶段失败：没有找到 select_all.png")
            return None

        all_left, all_top, all_w, all_h, all_conf = select_all_rect
        all_x = int(all_left + max(4, all_w * 0.25))
        all_y = int(all_top + all_h * 0.50)
        self.log(
            f"轲比能出牌阶段：点击全选 | "
            f"置信度={all_conf:.3f} | 点击坐标=({all_x}, {all_y}) | "
            f"模板区域=({all_left}, {all_top}, {all_w}, {all_h}) | 搜索区域={all_region}"
        )
        self.safe_click(all_x, all_y, jitter=1)

        self.log("轲比能出牌阶段：已点击全选，不做状态二次确认，直接点击确定")

        if not self.wait_and_click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            timeout=3,
            region=self.popup_confirm_region(found[0], found[1]),
            desc="寇旌-确认"
        ):
            self.log("轲比能出牌阶段失败：全选后没有找到 confirm.png")
            return None

        self.log("轲比能出牌阶段：寇旌全选确认完成")
        time.sleep(0.8)
        self.kebineng_last_select_all_anchor = (all_x, all_y)
        return all_x, all_y

    def try_kebineng_play_one_card(self, card_x, card_y):
        self.log(f"轲比能出牌阶段：点击手牌坐标=({card_x}, {card_y})")
        self.safe_click(card_x, card_y, jitter=2)

        select_found = self.wait_any_template(
            ["select_figure.png", "select_figure_2.png"],
            threshold=self.settings.THRESH_SMALL,
            timeout=1.5,
            desc="轲比能-选择目标"
        )

        if select_found is None:
            self.log("轲比能出牌阶段：未检测到选择目标提示，仍尝试点击李傕")

        if not self.click_template(
            "lijue.png",
            threshold=self.settings.THRESH_BOSS,
            desc="轲比能-选择李傕"
        ):
            self.log("轲比能出牌阶段：点击手牌后没有找到 lijue.png")
            self.handle_cancel_only()
            return "no_target"

        if not self.wait_and_click_template(
            "confirm.png",
            threshold=self.settings.THRESH_CONFIRM,
            timeout=2.5,
            desc="轲比能-选择李傕后确认"
        ):
            self.log("轲比能出牌阶段：点击李傕后没有找到 confirm.png")
            self.handle_cancel_only()
            return "no_confirm"

        self.log("轲比能出牌阶段：已出一张手牌并确认李傕")
        self.log("轲比能出牌阶段：等待 2 秒过场动画")
        time.sleep(2.0)
        self.handle_after_lijue_prompts(duration=1.5)
        self.handle_save_by_cancel()
        return "played"

    # =========================================================
    # 阶段函数：确定流程
    # =========================================================

    def stage_start_challenge(self, retry_depth=0, max_retry=5):
        self.log("执行阶段：开始挑战")

        start_ok = self.click_template(
            "start_challenge.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="开始挑战"
        )

        if start_ok:
            self.log("开始挑战点击成功")
            return True

        self.log("没有点到 start_challenge.png，开始执行新增逻辑：检测胜利并尝试重新选将")
        return self.handle_victory_to_new_challenge(
            retry_depth=retry_depth,
            max_retry=max_retry
        )

    def handle_victory_to_new_challenge(self, retry_depth=0, max_retry=5):
        """
        开始挑战按钮没点到时调用。

        逻辑：
        1. 检测 victory.png
        2. 如果检测为真：
           ① 检测并点击 cancel_2.png，等待 0.5s 后检测并点击 war.png
           ② 检测并点击 add_hero.png
           ③ 将 UI 最小化
           ④ 点击 search.png
           ⑤ 输入当前武将搜索词 + 回车
           ⑥ 等待 0.5s
           ⑦ 检测并点击当前武将的搜索结果模板
           ⑧ 再次调用 stage_start_challenge()
        """
        if retry_depth >= max_retry:
            self.log(f"胜利后重新开始流程达到最大重试次数 {max_retry}，停止递归")
            return False

        self.log("新增逻辑：开始检测胜利界面 victory.png")

        if not self.stage_check_victory():
            self.log("新增逻辑结束：没有检测到 victory.png")
            return False

        self.log("检测到 victory.png，开始执行胜利后重新选将流程")

        if not self.click_template(
            "cancel_2.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="胜利界面-取消 cancel_2"
        ):
            self.log("胜利后重新选将失败：没有找到 cancel_2.png")
            return False

        time.sleep(0.5)

        if not self.click_template(
            "war.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="征战 war"
        ):
            self.log("胜利后重新选将失败：没有找到 war.png")
            return False

        time.sleep(0.5)

        if not self.click_template(
            "add_hero.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="添加武将 add_hero"
        ):
            self.log("胜利后重新选将失败：没有找到 add_hero.png")
            return False

        time.sleep(0.5)

        self.log("准备最小化 UI，避免遮挡 search.png")
        self.minimize_ui_window()

        time.sleep(0.5)

        if not self.click_template(
            "search.png",
            threshold=self.settings.THRESH_BUTTON,
            desc="搜索框 search"
        ):
            self.log("胜利后重新选将失败：没有找到 search.png")
            return False

        time.sleep(0.3)

        self.log(f"搜索框输入：{self.general_profile.name}（{self.general_profile.search_text.strip()}）")
        pyautogui.write(self.general_profile.search_text, interval=0.03)
        pyautogui.press("enter")

        time.sleep(0.5)

        select_template = self.general_profile.select_template

        if not select_template:
            self.log(
                f"胜利后重新选将失败：{self.general_profile.name} "
                "缺少选将搜索结果模板，暂不能自动重新选将"
            )
            return False

        if not self.click_template(
            select_template,
            threshold=self.settings.THRESH_BUTTON,
            desc=self.general_profile.select_desc
        ):
            self.log(f"胜利后重新选将失败：没有找到 {select_template}")
            return False

        time.sleep(0.8)

        self.log("胜利后重新选将流程完成，重新调用开始挑战")
        return self.stage_start_challenge(
            retry_depth=retry_depth + 1,
            max_retry=max_retry
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

        if getattr(self.general_profile, "change_card_strategy", "standard") == "cancel_only":
            self.log(f"换牌阶段：{self.general_profile.name} 不检测【杀】数量，直接点击取消")
            cancel_ok = self.click_template(
                "cancel.png",
                threshold=self.settings.THRESH_BUTTON,
                desc="换牌阶段-直接取消"
            )

            if not cancel_ok:
                self.log("换牌阶段失败：直接取消时没有找到 cancel.png")
                return False

            self.log("换牌阶段完成：已直接点击取消")
            return True

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
        template_name = self.general_profile.skill_template
        threshold = getattr(self.settings, self.general_profile.skill_threshold_name)

        self.log(f"执行牌局阶段②：武将技能阶段（{self.general_profile.name}）")

        if getattr(self.general_profile, "attack_strategy", "standard") == "kebineng":
            self.log("轲比能的寇旌选择在出牌阶段处理，本阶段跳过")
            return True

        return self.click_template(
            template_name,
            threshold=threshold,
            desc=self.general_profile.skill_desc
        )

    # =========================================================
    # 牌局阶段 ③：将灵技能阶段 require
    # =========================================================

    def battle_phase_repairing_skill(self):
        template_name = self.spirit_profile.prompt_template
        target_template = self.general_profile.target_template

        self.log(f"执行牌局阶段③：将灵技能阶段（{self.spirit_profile.name}）")

        if not template_name or not self.spirit_profile.prompt_threshold_name:
            self.log(f"{self.spirit_profile.name} 无将灵技能触发，本阶段跳过")
            return True

        require_found = self.detect_require_prompt()

        if not require_found:
            self.log(f"没有检测到 {template_name}，本阶段不需要操作")
            return True

        self.log(f"检测到 {template_name}，开始执行将灵技能流程")

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

        if target_template:
            self.log(f"将灵技能：弹窗检测结束，休息 1 秒后等待 {target_template}")
        else:
            self.log("将灵技能：当前武将无部位选择技能效果，休息 1 秒后跳过该流程")
        time.sleep(1.0)

        head_result = self.click_head_target()

        if head_result in ("handled", "skipped"):
            self.log("将灵技能阶段完成")
            return True

        if head_result == "victory":
            show_template = target_template or "武将部位模板"
            self.log(f"将灵技能阶段完成：未检测到 {show_template}，但通过 save.png 后检测到胜利")
            return "victory"

        if head_result == "stopped":
            self.log("将灵技能阶段中止")
            return False

        show_template = target_template or "武将部位模板"
        self.log(f"将灵技能失败：未检测到 {show_template}，也没有通过 save.png 检测到胜利")
        return False

    # =========================================================
    # 牌局阶段 ④：出牌阶段
    # =========================================================

    def battle_phase_attack(self):
        if getattr(self.general_profile, "attack_strategy", "standard") == "kebineng":
            return self.battle_phase_attack_kebineng()

        return self.battle_phase_attack_standard()

    def battle_phase_attack_kebineng(self, require_koujing=True, allow_next_turn=True):
        self.log("执行牌局阶段④：出牌阶段（轲比能）")

        anchor = None

        if require_koujing:
            anchor = self.handle_kebineng_koujing_prompt()

        if require_koujing and anchor is None:
            if self.detect_victory_quiet("轲比能出牌阶段"):
                return "victory"

            clear_result = self.clear_cancel_until_acquire(timeout=30)

            if clear_result == "next_turn":
                return "next_turn"

            if clear_result == "victory":
                return "victory"

            return "failed"

        if not require_koujing:
            self.log("轲比能出牌阶段：跳过寇旌/全选，直接按手牌坐标出牌")
            anchor = self.kebineng_last_select_all_anchor

        rejected_card_xs = []
        miss_count = 0
        max_card_attempts = 36

        for attempt in range(1, max_card_attempts + 1):
            if self.stop_flag:
                self.log("轲比能出牌阶段中止")
                return "failed"

            if self.paused:
                time.sleep(0.2)
                continue

            if self.detect_victory_quiet("轲比能出牌阶段"):
                return "victory"

            if allow_next_turn:
                prompt_region = self.skill_popup_search_region()
                if self.detect_current_general_skill_quiet("轲比能出牌阶段", region=prompt_region):
                    self.log("轲比能出牌阶段：检测到下一轮寇旌提示")
                    return "next_turn"

            card_point, card_points, point_source = self.choose_kebineng_hand_card_point(rejected_card_xs)

            if card_point is None:
                self.log(
                    f"轲比能出牌阶段：{point_source} 没有可用手牌坐标，"
                    f"已识别候选={card_points}"
                )

                if self.detect_victory_quiet("轲比能出牌阶段"):
                    return "victory"

                if not allow_next_turn:
                    rejected_card_xs = []
                    time.sleep(0.6)
                    continue

                clear_result = self.clear_cancel_until_acquire(timeout=30)

                if clear_result == "next_turn":
                    self.log("轲比能出牌阶段完成：已进入下一轮寇旌")
                    return "next_turn"

                if clear_result == "victory":
                    self.log("轲比能出牌阶段完成：清理阶段检测到胜利")
                    return "victory"

                if clear_result == "stopped":
                    self.log("轲比能出牌阶段中止")
                    return "failed"

                rejected_card_xs = []
                continue

            card_x, card_y = card_point
            self.log(
                f"轲比能出牌阶段：第 {attempt} 次尝试出牌 | "
                f"{point_source}到 {len(card_points)} 个手牌坐标 | "
                f"选择=({card_x}, {card_y}) | 候选={card_points}"
            )

            result = self.try_kebineng_play_one_card(card_x, card_y)

            if result == "played":
                rejected_card_xs = []
                miss_count = 0
                self.log("轲比能出牌阶段：本次出牌成功，下次重新识别当前手牌")
                continue

            rejected_card_xs.append(card_x)
            miss_count += 1

            if miss_count >= len(card_points):
                self.log("轲比能出牌阶段：一轮候选手牌都未成功，开始检测胜利或下一轮")

                if self.detect_victory_quiet("轲比能出牌阶段"):
                    return "victory"

                if not allow_next_turn:
                    self.log("轲比能出牌阶段：当前为直接出牌轮，休息后继续尝试候选手牌")
                    rejected_card_xs = []
                    miss_count = 0
                    time.sleep(0.6)
                    continue

                clear_result = self.clear_cancel_until_acquire(timeout=30)

                if clear_result == "next_turn":
                    self.log("轲比能出牌阶段完成：已进入下一轮寇旌")
                    return "next_turn"

                if clear_result == "victory":
                    self.log("轲比能出牌阶段完成：清理阶段检测到胜利")
                    return "victory"

                if clear_result == "stopped":
                    self.log("轲比能出牌阶段中止")
                    return "failed"

                self.log("轲比能出牌阶段：清理阶段未检测到胜利或下一轮，继续尝试")
                rejected_card_xs = []
                miss_count = 0

        if self.detect_victory_quiet("轲比能出牌阶段"):
            return "victory"

        if not allow_next_turn:
            self.log("轲比能出牌阶段失败：直接出牌轮达到最大出牌尝试次数")
            return "failed"

        clear_result = self.clear_cancel_until_acquire(timeout=30)

        if clear_result == "next_turn":
            return "next_turn"

        if clear_result == "victory":
            return "victory"

        self.log("轲比能出牌阶段失败：达到最大出牌尝试次数")
        return "failed"

    def battle_phase_attack_standard(self):
        target_template = self.general_profile.target_template

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

        if target_template:
            self.log(f"出牌阶段：弹窗检测结束，休息 1.5 秒后等待 {target_template}")
        else:
            self.log("出牌阶段：当前武将无部位选择技能效果，休息 1.5 秒后跳过该流程")
        time.sleep(1.5)

        head_result = self.wait_head_after_attack(timeout=10)

        if head_result == "stopped":
            self.log("出牌阶段中止")
            return "failed"

        if head_result == "victory":
            show_template = target_template or "武将部位模板"
            self.log(f"出牌阶段完成：未检测到 {show_template}，但通过 save.png 后检测到胜利")
            return "victory"

        if head_result == "handled":
            self.log(f"出牌阶段：{target_template} 已处理，开始检测 save.png")
            self.handle_save_by_cancel()
        elif head_result == "skipped":
            self.log("出牌阶段：已跳过部位选择技能效果，继续检测胜利")
        else:
            show_template = target_template or "武将部位模板"
            self.log(f"出牌阶段：未出现 {show_template}，且没有通过 save.png 检测到胜利，继续后续流程")

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
        if getattr(self.general_profile, "attack_strategy", "standard") == "kebineng":
            return self.run_battle_until_victory_kebineng(max_turns=max_turns)

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
                self.log(f"牌局循环：检测到 {self.general_profile.skill_template}，进入下一轮")
                continue

            if attack_result == "failed":
                self.log("牌局循环中断：出牌阶段失败")
                return "failed"

        self.log(f"牌局循环结束：超过最大轮数 {max_turns}")
        return "timeout"

    def run_battle_until_victory_kebineng(self, max_turns=30, require_koujing=True):
        self.log("开始执行轲比能牌局循环：直到胜利或停止")

        turn_id = 0

        while not self.stop_flag and turn_id < max_turns:
            turn_id += 1
            self.log(f"========== 轲比能牌局循环：第 {turn_id} 轮 ==========")

            if self.stage_check_victory():
                self.log("轲比能牌局循环：检测到胜利")
                return "victory"

            if require_koujing:
                self.log("轲比能牌局循环：第一轮进入寇旌出牌阶段")
            else:
                self.log("轲比能牌局循环：跳过武将/将灵技能阶段，直接出牌")

            attack_result = self.battle_phase_attack_kebineng(
                require_koujing=require_koujing,
                allow_next_turn=require_koujing
            )

            if attack_result == "victory":
                self.log("轲比能牌局循环：出牌阶段检测到胜利")
                return "victory"

            if attack_result == "next_turn":
                self.log("轲比能牌局循环：进入后续直接出牌轮")
                require_koujing = False
                continue

            if attack_result == "failed":
                self.log("轲比能牌局循环中断：出牌阶段失败")
                return "failed"

        self.log(f"轲比能牌局循环结束：超过最大轮数 {max_turns}")
        return "timeout"

    def battle_phase_attack_and_continue(self):
        self.log(f"执行出牌阶段，并在检测到 {self.general_profile.skill_template} 后继续后续轮次")

        attack_result = self.battle_phase_attack()

        if attack_result == "victory":
            self.log("出牌阶段连续流程：已胜利")
            return True

        if attack_result == "next_turn":
            self.log(f"出牌阶段连续流程：检测到 {self.general_profile.skill_template}，继续执行下一轮")
            if getattr(self.general_profile, "attack_strategy", "standard") == "kebineng":
                result = self.run_battle_until_victory_kebineng(
                    max_turns=30,
                    require_koujing=False
                )
                return result == "victory"

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

        # 所有流程第一步：统一调整所有浏览器窗口尺寸
        self.resize_all_browser_windows(width=1280, height=800, move_to_left_top=True)

        # 等待窗口尺寸和页面重绘稳定，否则后续模板匹配可能对不上
        if not self.sleep_with_pause(1.0):
            self.running = False
            return

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
