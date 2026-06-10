# 李傕列传脚本说明文档

作者：By 莲莲の锋刃

---

<h1 style="color:red; font-size:32px;">一、使用前注意事项</h1>

## 1. 启动前请确认游戏窗口在前台

运行脚本前，请先打开游戏，并进入到可以正常操作的界面。

如果游戏窗口被其他窗口遮挡，脚本可能会识别不到模板图片，导致流程中断。

---

## 2. 本脚本适用性有限，当前仅适配<span style="color:red;">神黄忠+曹纯

程序启动后会先进入“出战配置”入口页，需要选择武将和将灵，再进入原来的流程控制页面。

当前内置的唯一组合是：

```text
武将：神黄忠
将灵：曹纯
```

后续如果要支持其他武将或将灵，需要补充对应模板图片、搜索词和判断流程。

---

## 3. 紧急停止方式

如果脚本点击异常，或者流程失控，可以用以下方式停止：

### 方法一：点击 UI 中的停止按钮

点击：

```text
停止
```

脚本会收到停止信号。

### 方法二：鼠标移动到屏幕左上角

程序使用了 PyAutoGUI 的安全机制。  
将鼠标快速移动到屏幕左上角，脚本会自动停止。

---

## 4. 不同电脑上可能需要重新调整阈值

由于不同电脑的分辨率、缩放比例、游戏画质、窗口大小可能不同，识别效果可能会变化。

如果在一台电脑上正常，换到另一台电脑后识别不到，一般需要：

- 调整阈值
- 检查游戏缩放比例
- 检查 UI 是否遮挡游戏画面

---

## 5. 不建议运行期间手动乱点

完整流程运行时，脚本会自动识别并点击。  
运行期间不要手动点击游戏内按钮，否则可能打乱当前流程。

---

<h1 style="color:red; font-size:32px;">二、运行前参数设置</h1>

## 1. 文件夹结构

程序文件夹建议保持如下结构：

```text
李傕列传/
├─ 李傕列传.exe
├─ templates/
│  ├─ 武将/
│  │  └─ 神黄忠/
│  │     ├─ acquire.png
│  │     └─ head.png
│  ├─ 将灵/
│  │  └─ 曹纯/
│  │     ├─ require.png
│  │     ├─ require (2).png
│  │     └─ xiaorui.png
│  └─ 通用/
│     ├─ BOSS/
│     │  └─ lijue.png
│     ├─ 卡牌/
│     │  └─ attack.png
│     ├─ 流程/
│     │  ├─ add_hero.png
│     │  ├─ cancel_2.png
│     │  ├─ change.png
│     │  ├─ search.png
│     │  ├─ select_figure.png
│     │  ├─ select_figure_2.png
│     │  ├─ select_hero.png
│     │  ├─ victory.png
│     │  └─ war.png
│     ├─ 流程按钮/
│     │  ├─ cancel.png
│     │  ├─ change_cards.png
│     │  ├─ confirm.png
│     │  ├─ sort.png
│     │  └─ start_challenge.png
│     └─ 流程字/
│        ├─ increase_damage.png
│        └─ save.png
├─ learned_templates/
├─ _internal/
└─ README.md
```

其中：

- `李傕列传.exe`：主程序
- `templates/`：识别模板图片
- `learned_templates/`：人工监督确认后自动保存的学习模板，目录结构跟随模板分类
- `_internal/`：程序运行所需文件，不能删除
- `README.md`：说明文档

---

## 2. templates 文件夹不能删除

`templates` 文件夹用于存放所有识别图片。
如果删除或移动，程序会找不到模板，日志里会出现类似：

```text
模板不存在：templates/武将/神黄忠/acquire.png 或 templates/acquire.png
```

代码仍兼容旧的平铺路径，例如 `templates/acquire.png`，但推荐使用上面的分类目录。

---

## 3. 模板图片说明

### 武将：神黄忠

| 文件名 | 作用 |
|---|---|
| `templates/武将/神黄忠/acquire.png` | 技能：裂穹摸牌 |
| `templates/武将/神黄忠/head.png` | 技能：裂穹击中 |

### 将灵：曹纯

| 文件名 | 作用 |
|---|---|
| `templates/将灵/曹纯/require.png` | 技能字：是否发动缮甲 |
| `templates/将灵/曹纯/require (2).png` | 技能：是否发动缮甲-全 |
| `templates/将灵/曹纯/xiaorui.png` | 技能字：是否发动骁锐 |

### 通用逻辑/流程

| 文件名 | 作用 |
|---|---|
| `templates/通用/流程按钮/start_challenge.png` | 流程按钮：立即挑战 |
| `templates/通用/流程/victory.png` | 流程：起始界面 |
| `templates/通用/流程/add_hero.png` | 流程：选择武将 |
| `templates/通用/卡牌/attack.png` | 卡牌：杀 |
| `templates/通用/流程按钮/confirm.png` | 流程按钮：确认 |
| `templates/通用/流程按钮/cancel.png` | 流程按钮：取消 |
| `templates/通用/流程/cancel_2.png` | 流程：窗口关闭 |
| `templates/通用/流程/change.png` | 流程：是否换牌 |
| `templates/通用/流程按钮/change_cards.png` | 流程按钮：换牌 |
| `templates/通用/流程按钮/sort.png` | 流程按钮：整理手牌 |
| `templates/通用/BOSS/lijue.png` | BOSS：李傕 |
| `templates/通用/流程/search.png` | 流程：搜索 |
| `templates/通用/流程/select_figure.png` | 流程：选择一个其他角色 |
| `templates/通用/流程/select_figure_2.png` | 流程：选择一个目标 |
| `templates/通用/流程/select_hero.png` | 流程：选择武将-神黄忠 |
| `templates/通用/流程字/save.png` | 流程字：是否出桃 |
| `templates/通用/流程/war.png` | 流程：关卡界面 |
| `templates/通用/流程字/increase_damage.png` | 流程字：是否增伤 |

人工监督学习弹窗会显示类似：

```text
武将：神黄忠 - acquire.png（技能：裂穹摸牌）
```

保存到 `learned_templates/` 的学习模板也会使用对应分类和中文前缀，方便后续查找。

---

## 4. 源码结构说明

| 文件名 | 作用 |
|---|---|
| `main.py` | UI 入口、出战配置入口、阈值设置窗口、人工监督弹窗 |
| `bot_core.py` | 自动化核心流程、截图、模板匹配、点击与完整战斗流程 |
| `app_paths.py` | 程序基础路径、模板目录、学习模板目录、设置文件路径 |
| `profile_registry.py` | 武将/将灵配置，例如神黄忠、曹纯 |
| `template_registry.py` | 模板分类路径、中文显示名、监督学习保存路径 |
| `settings_store.py` | 阈值配置、设置读写 |

---

## 5. 阈值设置说明

点击 UI 中的：

```text
阈值设置
```

可以打开参数设置窗口。

阈值越高，识别越严格。  
阈值越低，识别越宽松。

常用范围：

```text
0.50 ~ 0.80
```

---

## 6. 各阈值含义

| 参数 | 中文含义 | 说明 |
|---|---|---|
| `THRESH_BUTTON` | 通用按钮阈值 | 用于开始挑战、取消、整理手牌等普通按钮 |
| `THRESH_SMALL` | 小图标/提示阈值 | 用于 `select_figure.png`、`select_figure_2.png` |
| `THRESH_CARD` | 手牌识别阈值 | 用于识别 `attack.png`，也就是【杀】 |
| `THRESH_BOSS` | Boss 头像阈值 | 用于识别 `lijue.png` |
| `THRESH_HEAD` | 神黄忠部位图阈值 | 用于识别 `head.png`，也就是神黄忠技能效果的人体部位选择图 |
| `THRESH_VICTORY` | 胜利界面阈值 | 用于识别 `victory.png` |
| `THRESH_SAVE` | 求桃阈值 | 用于识别 `save.png` |
| `THRESH_ACQUIRE` | 武将技能阈值 | 用于识别 `acquire.png` |
| `THRESH_REQUIRE` | 将灵技能询问阈值 | 用于识别 `require.png` |
| `THRESH_POPUP` | 弹窗技能阈值 | 用于识别 `increase_damage.png` 和 `xiaorui.png` |
| `THRESH_CONFIRM` | 确认按钮阈值 | 用于识别 `confirm.png` |

---

## 7. 推荐初始阈值

如果没有特殊情况，可以先使用默认值：

```text
THRESH_BUTTON   = 0.65
THRESH_SMALL    = 0.65
THRESH_CARD     = 0.65
THRESH_BOSS     = 0.65
THRESH_HEAD     = 0.65
THRESH_VICTORY  = 0.65
THRESH_SAVE     = 0.65
THRESH_ACQUIRE  = 0.60
THRESH_REQUIRE  = 0.75
THRESH_POPUP    = 0.55
THRESH_CONFIRM  = 0.55
```

---

## 8. 什么时候调高阈值？

如果出现以下情况，建议调高对应阈值：

- 没出现按钮，但脚本误以为出现了
- 没有将灵技能，但误触发将灵技能流程
- 没有胜利，却误判胜利
- 没有【杀】，却误判有【杀】

例如：

```text
require.png 经常误识别
```

可以把：

```text
THRESH_REQUIRE
```

从 `0.75` 调高到 `0.78` 或 `0.80`。

---

## 9. 什么时候调低阈值？

如果出现以下情况，建议调低对应阈值：

- 明明有按钮，但脚本识别不到
- 明明有【杀】，但识别不到
- 明明进入胜利界面，但检测不到胜利
- 明明出现武将技能，但检测不到 `acquire.png`

例如：

```text
acquire.png 识别不到
```

可以把：

```text
THRESH_ACQUIRE
```

从 `0.60` 调低到 `0.55`。

---

## 10. 保存截图用于调试

点击 UI 中的：

```text
保存截图
```

程序会保存当前屏幕到：

```text
debug_screens/
```

如果识别异常，可以用保存下来的截图和 `templates/` 文件夹里的模板进行对比。

---

<h1 style="color:red; font-size:32px;">三、运行中报错怎么处理</h1>



## 1. 脚本一直点取消

如果脚本一直点击取消，通常说明这一回合没有秒杀李傕，在等待下一回合：

这是正常现象，无需担忧



## 2. 其他怪异现象

建议终止程序，重新运行

