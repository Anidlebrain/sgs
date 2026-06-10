import threading
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

from bot_core import GameBot
from profile_registry import (
    AVAILABLE_GENERAL_PROFILES,
    AVAILABLE_SPIRIT_PROFILES,
    DEFAULT_GENERAL_PROFILE_KEY,
    DEFAULT_SPIRIT_PROFILE_KEY,
    resolve_general_profile,
    resolve_spirit_profile,
)
from settings_store import (
    THRESHOLD_META,
    DEFAULT_SETTING_VALUES,
    SETTINGS_FILE,
    load_bot_settings,
    save_bot_settings,
)
from template_registry import get_template_display_name


class BotUI:
    def __init__(self, root):
        self.root = root
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.general_profile = None
        self.spirit_profile = None
        self.settings = None
        self.settings_loaded = False
        self.settings_load_error = None
        self.bot = None

        self.setup_style()
        self.build_entry_ui()

    # =========================================================
    # 样式
    # =========================================================

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.root.configure(bg="#1f1a14")

        style.configure(
            "Main.TFrame",
            background="#1f1a14"
        )

        style.configure(
            "PanelInner.TFrame",
            background="#2b2118"
        )

        style.configure(
            "Panel.TLabelframe",
            background="#2b2118",
            foreground="#f4d38a",
            borderwidth=2,
            relief="ridge"
        )

        style.configure(
            "Panel.TLabelframe.Label",
            background="#1f1a14",
            foreground="#f4d38a",
            font=("Microsoft YaHei", 8, "bold")
        )

        style.configure(
            "Title.TLabel",
            background="#1f1a14",
            foreground="#ffd36b",
            font=("Microsoft YaHei", 17, "bold")
        )

        style.configure(
            "Author.TLabel",
            background="#1f1a14",
            foreground="#c8a66a",
            font=("Microsoft YaHei", 7)
        )

        style.configure(
            "Hint.TLabel",
            background="#1f1a14",
            foreground="#ff7777",
            font=("Microsoft YaHei", 7)
        )

        style.configure(
            "Muted.TLabel",
            background="#1f1a14",
            foreground="#c8a66a",
            font=("Microsoft YaHei", 8)
        )

        style.configure(
            "PanelText.TLabel",
            background="#2b2118",
            foreground="#f6e6bd",
            font=("Microsoft YaHei", 8)
        )

        style.configure(
            "PanelTextBold.TLabel",
            background="#2b2118",
            foreground="#ffe0a0",
            font=("Microsoft YaHei", 8, "bold")
        )

        style.configure(
            "Gold.TButton",
            font=("Microsoft YaHei", 8, "bold"),
            padding=2
        )

        style.map(
            "Gold.TButton",
            foreground=[("active", "#4b2b00")],
            background=[("active", "#f5c56b")]
        )

    # =========================================================
    # 入口选择 UI
    # =========================================================

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_entry_ui(self):
        self.clear_root()
        self.root.title("李傕列传 - 选择搭配")
        self.root.geometry("365x360+601+258")
        self.root.configure(bg="#1f1a14")

        main = ttk.Frame(self.root, style="Main.TFrame")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        title = ttk.Label(
            main,
            text="李傕列传",
            style="Title.TLabel"
        )
        title.pack(anchor="w", padx=2, pady=(2, 0))

        subtitle = ttk.Label(
            main,
            text="请选择武将和将灵后进入控制台",
            style="Muted.TLabel"
        )
        subtitle.pack(anchor="w", padx=3, pady=(0, 10))

        select_frame = ttk.LabelFrame(
            main,
            text="出战配置",
            style="Panel.TLabelframe"
        )
        select_frame.pack(fill="x", pady=(0, 8))

        select_frame.columnconfigure(0, weight=1)

        general_names = [profile.name for profile in AVAILABLE_GENERAL_PROFILES.values()]
        spirit_names = [profile.name for profile in AVAILABLE_SPIRIT_PROFILES.values()]

        self.general_name_to_key = {
            profile.name: profile.key
            for profile in AVAILABLE_GENERAL_PROFILES.values()
        }
        self.spirit_name_to_key = {
            profile.name: profile.key
            for profile in AVAILABLE_SPIRIT_PROFILES.values()
        }

        default_general = resolve_general_profile(DEFAULT_GENERAL_PROFILE_KEY)
        default_spirit = resolve_spirit_profile(DEFAULT_SPIRIT_PROFILE_KEY)

        self.general_var = tk.StringVar(value=default_general.name)
        self.spirit_var = tk.StringVar(value=default_spirit.name)

        self.add_profile_selector(
            select_frame,
            row=0,
            title="武将",
            variable=self.general_var,
            values=general_names
        )
        self.add_profile_selector(
            select_frame,
            row=1,
            title="将灵",
            variable=self.spirit_var,
            values=spirit_names
        )

        note_frame = ttk.LabelFrame(
            main,
            text="当前支持",
            style="Panel.TLabelframe"
        )
        note_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            note_frame,
            text="当前仅内置：武将「神黄忠」+ 将灵「曹纯」。",
            style="PanelText.TLabel"
        ).pack(anchor="w", padx=8, pady=(6, 2))

        ttk.Label(
            note_frame,
            text="后续新增武将或将灵时，在配置表中补充选项，再接入对应图片和判断流程。",
            style="PanelText.TLabel",
            wraplength=320,
            justify="left"
        ).pack(anchor="w", padx=8, pady=(0, 7))

        ttk.Button(
            main,
            text="进入控制台",
            style="Gold.TButton",
            command=self.enter_main_ui
        ).pack(fill="x", padx=4, pady=(2, 8))

        hint = ttk.Label(
            main,
            text="进入后仍是原来的流程控制页面",
            style="Hint.TLabel"
        )
        hint.pack(anchor="w", padx=3)

    def add_profile_selector(self, parent, row, title, variable, values):
        block = ttk.Frame(parent, style="PanelInner.TFrame")
        block.grid(row=row, column=0, sticky="ew", padx=8, pady=(7, 3))
        block.columnconfigure(0, weight=0)
        block.columnconfigure(1, weight=1)

        label = ttk.Label(
            block,
            text=title,
            style="PanelTextBold.TLabel"
        )
        label.grid(row=0, column=0, sticky="w", padx=(0, 8))

        combo = ttk.Combobox(
            block,
            textvariable=variable,
            values=values,
            state="readonly",
            font=("Microsoft YaHei", 9),
            width=18
        )
        combo.grid(row=0, column=1, sticky="ew")

    def enter_main_ui(self):
        general_key = self.general_name_to_key.get(
            self.general_var.get(),
            DEFAULT_GENERAL_PROFILE_KEY
        )
        spirit_key = self.spirit_name_to_key.get(
            self.spirit_var.get(),
            DEFAULT_SPIRIT_PROFILE_KEY
        )

        self.general_profile = resolve_general_profile(general_key)
        self.spirit_profile = resolve_spirit_profile(spirit_key)

        self.clear_root()
        self.root.title(f"李傕列传 - {self.general_profile.name} / {self.spirit_profile.name}")

        # 主 UI 稍微加高，并保持宽度
        # 这样底部日志框能稳定显示
        self.root.geometry("365x710+601+258")
        self.root.configure(bg="#1f1a14")

        self.settings, self.settings_loaded, self.settings_load_error = load_bot_settings()
        self.bot = GameBot(
            log_func=self.write_log,
            settings=self.settings,
            minimize_func=self.minimize_ui,
            supervision_func=self.confirm_template_supervision,
            general_profile=self.general_profile,
            spirit_profile=self.spirit_profile,
        )

        self.build_ui()
        self.write_log(f"[入口] 当前武将：{self.general_profile.name}；当前将灵：{self.spirit_profile.name}")

        if self.settings_loaded:
            self.write_log(f"[设置] 已读取本地阈值：{SETTINGS_FILE}")
        elif self.settings_load_error:
            self.write_log(f"[设置] {self.settings_load_error}，已使用默认阈值")

    # =========================================================
    # 主 UI
    # =========================================================

    def build_ui(self):
        main = ttk.Frame(self.root, style="Main.TFrame")
        main.pack(fill="both", expand=True, padx=8, pady=5)

        # -------------------------
        # 标题区
        # -------------------------

        title_frame = ttk.Frame(main, style="Main.TFrame")
        title_frame.pack(fill="x", pady=(0, 4))

        title = ttk.Label(
            title_frame,
            text="李傕列传",
            style="Title.TLabel"
        )
        title.pack(side="left", padx=(2, 0))

        profile_text = "当前：未选择"
        if self.general_profile is not None and self.spirit_profile is not None:
            profile_text = f"当前：{self.general_profile.name} / {self.spirit_profile.name}"

        profile_label = ttk.Label(
            title_frame,
            text=profile_text,
            style="Muted.TLabel"
        )
        profile_label.pack(side="left", padx=(8, 0), pady=(13, 0))

        author = ttk.Label(
            title_frame,
            text="By 莲莲の锋刃\nBy Anidlebrain",
            style="Author.TLabel"
        )
        author.pack(side="right", padx=(0, 2), pady=(10, 0))

        # -------------------------
        # 确定流程
        # -------------------------

        confirm_frame = ttk.LabelFrame(
            main,
            text="确定流程",
            style="Panel.TLabelframe"
        )
        confirm_frame.pack(fill="x", pady=2)

        confirm_frame.columnconfigure(0, weight=1)
        confirm_frame.columnconfigure(1, weight=1)

        ttk.Button(
            confirm_frame,
            text="开始挑战",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.stage_start_challenge)
        ).grid(row=0, column=0, sticky="ew", padx=7, pady=4)

        ttk.Button(
            confirm_frame,
            text="检测胜利",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.stage_check_victory)
        ).grid(row=0, column=1, sticky="ew", padx=7, pady=4)

        # -------------------------
        # 牌局阶段
        # -------------------------

        battle_frame = ttk.LabelFrame(
            main,
            text="牌局阶段",
            style="Panel.TLabelframe"
        )
        battle_frame.pack(fill="x", pady=2)

        battle_frame.columnconfigure(0, weight=1)
        battle_frame.columnconfigure(1, weight=1)

        ttk.Button(
            battle_frame,
            text="①换牌阶段",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.battle_phase_change_cards)
        ).grid(row=0, column=0, sticky="ew", padx=7, pady=3)

        ttk.Button(
            battle_frame,
            text="②武将技能",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.battle_phase_acquire_skill)
        ).grid(row=0, column=1, sticky="ew", padx=7, pady=3)

        ttk.Button(
            battle_frame,
            text="③将灵技能",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.battle_phase_repairing_skill)
        ).grid(row=1, column=0, sticky="ew", padx=7, pady=3)

        ttk.Button(
            battle_frame,
            text="④出牌阶段",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.battle_phase_attack_and_continue)
        ).grid(row=1, column=1, sticky="ew", padx=7, pady=3)

        # -------------------------
        # 流程：只保留完整流程
        # -------------------------

        flow_frame = ttk.LabelFrame(
            main,
            text="流程",
            style="Panel.TLabelframe"
        )
        flow_frame.pack(fill="x", pady=2)

        ttk.Button(
            flow_frame,
            text="完整流程",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.run_one_full_cycle)
        ).pack(fill="x", padx=7, pady=5)

        # -------------------------
        # 设置
        # -------------------------

        setting_frame = ttk.LabelFrame(
            main,
            text="设置",
            style="Panel.TLabelframe"
        )
        setting_frame.pack(fill="x", pady=2)

        setting_frame.columnconfigure(0, weight=1)
        setting_frame.columnconfigure(1, weight=1)

        ttk.Button(
            setting_frame,
            text="阈值设置",
            style="Gold.TButton",
            command=self.open_threshold_settings
        ).grid(row=0, column=0, sticky="ew", padx=7, pady=4)

        ttk.Button(
            setting_frame,
            text="保存截图",
            style="Gold.TButton",
            command=lambda: self.run_in_thread(self.bot.save_debug_screenshot)
        ).grid(row=0, column=1, sticky="ew", padx=7, pady=4)

        # -------------------------
        # 控制
        # -------------------------

        control_frame = ttk.LabelFrame(
            main,
            text="控制",
            style="Panel.TLabelframe"
        )
        control_frame.pack(fill="x", pady=2)

        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)

        ttk.Button(
            control_frame,
            text="暂停 / 继续",
            style="Gold.TButton",
            command=self.toggle_pause
        ).grid(row=0, column=0, sticky="ew", padx=7, pady=4)

        ttk.Button(
            control_frame,
            text="停止",
            style="Gold.TButton",
            command=self.stop_bot
        ).grid(row=0, column=1, sticky="ew", padx=7, pady=4)

        ttk.Button(
            control_frame,
            text="清空日志",
            style="Gold.TButton",
            command=self.clear_log
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=7, pady=(0, 4))

        # -------------------------
        # 日志：固定预留高度
        # -------------------------

        log_frame = ttk.LabelFrame(
            main,
            text="日志",
            style="Panel.TLabelframe"
        )
        log_frame.pack(fill="both", expand=True, pady=(3, 2))

        # 给日志框预留约 15% 高度
        log_frame.configure(height=105)
        log_frame.pack_propagate(False)

        self.log_text = tk.Text(
            log_frame,
            height=6,
            font=("Consolas", 7),
            wrap="word",
            bg="#14100c",
            fg="#f6e6bd",
            insertbackground="#f6e6bd",
            relief="flat",
            borderwidth=0
        )
        self.log_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

        scrollbar = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.log_text.yview
        )
        scrollbar.pack(side="right", fill="y", pady=5, padx=(0, 5))

        self.log_text.configure(yscrollcommand=scrollbar.set)

        hint = ttk.Label(
            main,
            text="紧急停止：鼠标移到屏幕左上角，或点击停止",
            style="Hint.TLabel"
        )
        hint.pack(pady=(1, 0))

    # =========================================================
    # 阈值设置窗口
    # =========================================================

    def open_threshold_settings(self):
        win = tk.Toplevel(self.root)
        win.title("阈值设置")
        win.geometry("560x640+945+258")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(bg="#1f1a14")

        title = tk.Label(
            win,
            text="阈值设置",
            font=("Microsoft YaHei", 16, "bold"),
            bg="#1f1a14",
            fg="#ffd36b"
        )
        title.pack(pady=(10, 2))

        tip = tk.Label(
            win,
            text="数值越高越严格，越低越容易匹配。常用范围：0.50 ~ 0.80",
            font=("Microsoft YaHei", 8),
            bg="#1f1a14",
            fg="#d8bf88"
        )
        tip.pack(pady=(0, 6))

        # =====================================================
        # 可滚动阈值区域
        # =====================================================

        outer = tk.Frame(
            win,
            bg="#2b2118",
            bd=2,
            relief="ridge"
        )
        outer.pack(fill="both", expand=True, padx=12, pady=6)

        canvas = tk.Canvas(
            outer,
            bg="#2b2118",
            highlightthickness=0
        )
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            outer,
            orient="vertical",
            command=canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        panel = tk.Frame(canvas, bg="#2b2118")
        panel_window = canvas.create_window((0, 0), window=panel, anchor="nw")

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_panel(event):
            canvas.itemconfig(panel_window, width=event.width)

        panel.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_panel)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        entry_vars = {}

        for row, item in enumerate(THRESHOLD_META):
            name = item["name"]
            title_text = item["title"]
            desc = item["desc"]

            value = getattr(self.settings, name)

            row_frame = tk.Frame(panel, bg="#2b2118")
            row_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=3)

            row_frame.columnconfigure(0, weight=1)
            row_frame.columnconfigure(1, weight=0)

            label = tk.Label(
                row_frame,
                text=f"{title_text}（{name}）",
                font=("Microsoft YaHei", 8, "bold"),
                bg="#2b2118",
                fg="#ffe0a0",
                anchor="w"
            )
            label.grid(row=0, column=0, sticky="w")

            var = tk.StringVar(value=f"{value:.2f}")
            entry_vars[name] = var

            spin = tk.Spinbox(
                row_frame,
                from_=0.00,
                to=1.00,
                increment=0.01,
                textvariable=var,
                width=7,
                font=("Consolas", 9),
                bg="#14100c",
                fg="#f6e6bd",
                insertbackground="#f6e6bd",
                buttonbackground="#3a2a18",
                relief="ridge"
            )
            spin.grid(row=0, column=1, sticky="e", padx=(8, 0))

            sub = tk.Label(
                row_frame,
                text=desc,
                font=("Microsoft YaHei", 7),
                bg="#2b2118",
                fg="#cdbb92",
                anchor="w",
                justify="left",
                wraplength=420
            )
            sub.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 0))

        supervision_row = len(THRESHOLD_META)
        supervision_enabled_var = tk.BooleanVar(value=self.settings.SUPERVISION_ENABLED)
        supervision_min_var = tk.StringVar(value=f"{self.settings.SUPERVISION_MIN_CONF:.2f}")

        supervision_frame = tk.Frame(panel, bg="#2b2118")
        supervision_frame.grid(row=supervision_row, column=0, sticky="ew", padx=10, pady=(8, 3))

        supervision_frame.columnconfigure(0, weight=1)
        supervision_frame.columnconfigure(1, weight=0)

        supervision_check = tk.Checkbutton(
            supervision_frame,
            text="启用人工监督学习",
            variable=supervision_enabled_var,
            font=("Microsoft YaHei", 8, "bold"),
            bg="#2b2118",
            fg="#ffe0a0",
            selectcolor="#14100c",
            activebackground="#2b2118",
            activeforeground="#ffe0a0",
            anchor="w"
        )
        supervision_check.grid(row=0, column=0, sticky="w")

        supervision_spin = tk.Spinbox(
            supervision_frame,
            from_=0.00,
            to=1.00,
            increment=0.01,
            textvariable=supervision_min_var,
            width=7,
            font=("Consolas", 9),
            bg="#14100c",
            fg="#f6e6bd",
            insertbackground="#f6e6bd",
            buttonbackground="#3a2a18",
            relief="ridge"
        )
        supervision_spin.grid(row=0, column=1, sticky="e", padx=(8, 0))

        supervision_tip = tk.Label(
            supervision_frame,
            text="最高置信度低于目标阈值、但不低于此下限时弹窗确认；确认后会保存学习模板。",
            font=("Microsoft YaHei", 7),
            bg="#2b2118",
            fg="#cdbb92",
            anchor="w",
            justify="left",
            wraplength=420
        )
        supervision_tip.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 0))

        # =====================================================
        # 底部按钮
        # =====================================================

        button_frame = tk.Frame(win, bg="#1f1a14")
        button_frame.pack(fill="x", padx=12, pady=(2, 10))

        def apply_thresholds():
            errors = []
            parsed_values = {}

            for name, var in entry_vars.items():
                text = var.get().strip()

                try:
                    value = float(text)
                except ValueError:
                    errors.append(f"{name} 不是有效数字")
                    continue

                if not 0 <= value <= 1:
                    errors.append(f"{name} 必须在 0 到 1 之间")
                    continue

                parsed_values[name] = value

            supervision_min_text = supervision_min_var.get().strip()

            try:
                supervision_min_value = float(supervision_min_text)
            except ValueError:
                errors.append("SUPERVISION_MIN_CONF 不是有效数字")
                supervision_min_value = None

            if supervision_min_value is not None and not 0 <= supervision_min_value <= 1:
                errors.append("SUPERVISION_MIN_CONF 必须在 0 到 1 之间")

            if errors:
                messagebox.showerror(
                    "阈值设置错误",
                    "\n".join(errors),
                    parent=win
                )
                return

            for name, value in parsed_values.items():
                setattr(self.settings, name, value)

            self.settings.SUPERVISION_ENABLED = supervision_enabled_var.get()
            self.settings.SUPERVISION_MIN_CONF = supervision_min_value

            saved, save_error = save_bot_settings(self.settings)

            if saved:
                self.write_log(f"[设置] 阈值已更新并保存：{SETTINGS_FILE}")
            else:
                self.write_log(f"[设置] 阈值已更新，但{save_error}")
                messagebox.showwarning(
                    "阈值保存失败",
                    f"阈值已在本次运行中生效，但没有写入本地文件。\n{save_error}",
                    parent=win
                )
                return

            messagebox.showinfo(
                "阈值设置",
                "阈值已更新并保存，后续启动会自动读取。",
                parent=win
            )

        def reset_defaults():
            for name, value in DEFAULT_SETTING_VALUES.items():
                if name in entry_vars:
                    entry_vars[name].set(f"{value:.2f}")

            supervision_enabled_var.set(DEFAULT_SETTING_VALUES["SUPERVISION_ENABLED"])
            supervision_min_var.set(f"{DEFAULT_SETTING_VALUES['SUPERVISION_MIN_CONF']:.2f}")

        apply_btn = tk.Button(
            button_frame,
            text="应用阈值",
            font=("Microsoft YaHei", 8, "bold"),
            bg="#b8863b",
            fg="white",
            activebackground="#d7a85a",
            activeforeground="white",
            relief="ridge",
            command=apply_thresholds
        )
        apply_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        reset_btn = tk.Button(
            button_frame,
            text="恢复默认",
            font=("Microsoft YaHei", 8),
            bg="#5a4632",
            fg="#f6e6bd",
            activebackground="#73583c",
            activeforeground="#ffffff",
            relief="ridge",
            command=reset_defaults
        )
        reset_btn.pack(side="left", fill="x", expand=True, padx=5)

        close_btn = tk.Button(
            button_frame,
            text="关闭",
            font=("Microsoft YaHei", 8),
            bg="#3a2d23",
            fg="#f6e6bd",
            activebackground="#5c4634",
            activeforeground="#ffffff",
            relief="ridge",
            command=win.destroy
        )
        close_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

    # =========================================================
    # UI 工具函数
    # =========================================================

    def minimize_ui(self):
        """
        给 bot_core 调用，用于把主 UI 最小化。
        因为 tkinter 不建议在子线程直接操作窗口，所以这里使用 root.after。
        """
        try:
            self.root.after(0, self.root.iconify)
            self.write_log("[UI] 主窗口已最小化")
        except Exception as e:
            self.write_log(f"[UI] 最小化失败：{e}")

    def confirm_template_supervision(self, template_name, confidence, threshold, image):
        result = {"accepted": False}
        done = threading.Event()

        def ask_on_ui_thread():
            try:
                result["accepted"] = self.open_template_supervision_dialog(
                    template_name,
                    confidence,
                    threshold,
                    image
                )
            finally:
                done.set()

        if threading.current_thread() is threading.main_thread():
            ask_on_ui_thread()
        else:
            self.root.after(0, ask_on_ui_thread)
            done.wait()

        return result["accepted"]

    def open_template_supervision_dialog(self, template_name, confidence, threshold, image):
        result = {"accepted": False}
        display_name = get_template_display_name(template_name)

        try:
            previous_state = self.root.state()
        except Exception:
            previous_state = "normal"

        try:
            if previous_state == "iconic":
                self.root.deiconify()
            self.root.lift()
        except Exception:
            pass

        win = tk.Toplevel(self.root)
        win.title("人工确认")
        win.geometry("420x430+980+258")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.configure(bg="#1f1a14")

        title = tk.Label(
            win,
            text="是否确认这是当前模板？",
            font=("Microsoft YaHei", 13, "bold"),
            bg="#1f1a14",
            fg="#ffd36b"
        )
        title.pack(pady=(12, 4))

        info = tk.Label(
            win,
            text=(
                f"模板：{display_name}\n"
                f"逻辑名：{template_name}\n"
                f"当前置信度：{confidence:.3f}\n"
                f"目标阈值：{threshold:.3f}"
            ),
            font=("Microsoft YaHei", 9),
            bg="#1f1a14",
            fg="#f6e6bd",
            justify="left",
            wraplength=380
        )
        info.pack(fill="x", padx=16, pady=(0, 8))

        preview_frame = tk.Frame(win, bg="#2b2118", bd=2, relief="ridge")
        preview_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        preview_added = False

        if Image is not None and ImageTk is not None and image is not None:
            try:
                rgb_image = image[:, :, ::-1].copy()
                preview = Image.fromarray(rgb_image)
                preview.thumbnail((360, 235))
                photo = ImageTk.PhotoImage(preview)

                image_label = tk.Label(
                    preview_frame,
                    image=photo,
                    bg="#2b2118"
                )
                image_label.image = photo
                image_label.pack(expand=True)
                preview_added = True
            except Exception:
                preview_added = False

        if not preview_added:
            tk.Label(
                preview_frame,
                text="预览不可用，但仍可根据当前游戏画面确认。",
                font=("Microsoft YaHei", 9),
                bg="#2b2118",
                fg="#f6e6bd"
            ).pack(expand=True)

        button_frame = tk.Frame(win, bg="#1f1a14")
        button_frame.pack(fill="x", padx=16, pady=(0, 14))

        def choose(value):
            result["accepted"] = value
            win.destroy()

        no_btn = tk.Button(
            button_frame,
            text="不是",
            font=("Microsoft YaHei", 9),
            bg="#5a4632",
            fg="#f6e6bd",
            activebackground="#73583c",
            activeforeground="#ffffff",
            relief="ridge",
            command=lambda: choose(False)
        )
        no_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        yes_btn = tk.Button(
            button_frame,
            text="是，保存学习",
            font=("Microsoft YaHei", 9, "bold"),
            bg="#b8863b",
            fg="white",
            activebackground="#d7a85a",
            activeforeground="white",
            relief="ridge",
            command=lambda: choose(True)
        )
        yes_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

        win.protocol("WM_DELETE_WINDOW", lambda: choose(False))
        win.bind("<Escape>", lambda event: choose(False))
        win.grab_set()
        yes_btn.focus_set()

        self.write_log(
            f"[人工监督] 等待确认：{display_name} | "
            f"置信度={confidence:.3f} | 阈值={threshold:.3f}"
        )

        self.root.wait_window(win)

        if previous_state == "iconic":
            self.root.after(100, self.root.iconify)

        return result["accepted"]

    def write_log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def run_in_thread(self, func):
        self.bot.stop_flag = False
        t = threading.Thread(target=func, daemon=True)
        t.start()

    def toggle_pause(self):
        self.bot.paused = not self.bot.paused

        if self.bot.paused:
            self.write_log("[控制] 已暂停")
        else:
            self.write_log("[控制] 已继续")

    def stop_bot(self):
        self.bot.stop_flag = True
        self.bot.running = False
        self.write_log("[控制] 已发送停止信号")


def main():
    root = tk.Tk()
    app = BotUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
