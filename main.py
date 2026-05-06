import threading
import tkinter as tk
from tkinter import ttk, messagebox

from bot_core import (
    GameBot,
    BotSettings,
    THRESHOLD_META,
    DEFAULT_SETTING_VALUES,
)


class BotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("李傕列传")

        # 主 UI 稍微加高，并保持宽度
        # 这样底部日志框能稳定显示
        self.root.geometry("365x700+601+258")
        self.root.resizable(False, False)

        self.root.attributes("-topmost", True)

        self.settings = BotSettings()
        self.bot = GameBot(
            log_func=self.write_log,
            settings=self.settings,
            minimize_func=self.minimize_ui
        )

        self.setup_style()
        self.build_ui()

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

        author = ttk.Label(
            title_frame,
            text="By 莲莲の锋刃",
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

        # =====================================================
        # 底部按钮
        # =====================================================

        button_frame = tk.Frame(win, bg="#1f1a14")
        button_frame.pack(fill="x", padx=12, pady=(2, 10))

        def apply_thresholds():
            errors = []

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

                setattr(self.settings, name, value)

            if errors:
                messagebox.showerror(
                    "阈值设置错误",
                    "\n".join(errors),
                    parent=win
                )
                return

            self.write_log("[设置] 阈值已更新")
            messagebox.showinfo(
                "阈值设置",
                "阈值已更新，后续识别会使用新数值。",
                parent=win
            )

        def reset_defaults():
            for name, value in DEFAULT_SETTING_VALUES.items():
                if name in entry_vars:
                    entry_vars[name].set(f"{value:.2f}")

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
