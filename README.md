# 李傕列传脚本说明文档

作者：By 莲莲の锋刃

---

<h1 style="color:red; font-size:32px;">一、使用前注意事项</h1>

## 1. 启动前请确认游戏窗口在前台

运行脚本前，请先打开游戏，并进入到可以正常操作的界面。

如果游戏窗口被其他窗口遮挡，脚本可能会识别不到模板图片，导致流程中断。

---

## 2. 本脚本适用性有限，刚需适配<span style="color:red;">神黄忠+曹纯

囿于本人水平，整个程序基于神黄忠和曹纯技能实现，无法使用其他将灵或武将。

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
│  ├─ start_challenge.png
│  ├─ victory.png
│  ├─ acquire.png
│  ├─ require.png
│  ├─ attack.png
│  ├─ confirm.png
│  ├─ cancel.png
│  ├─ change_cards.png
│  ├─ sort.png
│  ├─ lijue.png
│  ├─ select_figure.png
│  ├─ select_figure_2.png
│  ├─ head.png
│  ├─ save.png
│  ├─ increase_damage.png
│  └─ xiaorui.png
├─ _internal/
└─ README.md
```

其中：

- `李傕列传.exe`：主程序
- `templates/`：识别模板图片
- `_internal/`：程序运行所需文件，不能删除
- `README.md`：说明文档

---

## 2. templates 文件夹不能删除

`templates` 文件夹用于存放所有识别图片。  
如果删除或移动，程序会找不到模板，日志里会出现类似：

```text
模板不存在：templates/xxx.png
```

---

## 3. 模板图片说明

| 文件名 | 作用 |
|---|---|
| `start_challenge.png` | 开始挑战按钮 |
| `victory.png` | 胜利界面 |
| `acquire.png` | 武将技能：摸体力值张牌 |
| `require.png` | 将灵技能询问，例如是否发动缝甲 |
| `attack.png` | 手牌中的【杀】 |
| `confirm.png` | 确定按钮 |
| `cancel.png` | 取消按钮 |
| `change_cards.png` | 换牌按钮 |
| `sort.png` | 整理手牌按钮 |
| `lijue.png` | 李傕头像 |
| `select_figure.png` | 选择一名其他角色提示 |
| `select_figure_2.png` | 选择目标的备用提示 |
| `head.png` | 人体部位选择图 |
| `save.png` | 求桃提示 |
| `increase_damage.png` | 增加伤害提示 |
| `xiaorui.png` | 骁锐提示 |

---

## 4. 阈值设置说明

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

## 5. 各阈值含义

| 参数 | 中文含义 | 说明 |
|---|---|---|
| `THRESH_BUTTON` | 通用按钮阈值 | 用于开始挑战、取消、整理手牌等普通按钮 |
| `THRESH_SMALL` | 小图标/提示阈值 | 用于 `select_figure.png`、`select_figure_2.png` |
| `THRESH_CARD` | 手牌识别阈值 | 用于识别 `attack.png`，也就是【杀】 |
| `THRESH_BOSS` | Boss 头像阈值 | 用于识别 `lijue.png` |
| `THRESH_HEAD` | 人体图阈值 | 用于识别 `head.png` |
| `THRESH_VICTORY` | 胜利界面阈值 | 用于识别 `victory.png` |
| `THRESH_SAVE` | 求桃阈值 | 用于识别 `save.png` |
| `THRESH_ACQUIRE` | 武将技能阈值 | 用于识别 `acquire.png` |
| `THRESH_REQUIRE` | 将灵技能询问阈值 | 用于识别 `require.png` |
| `THRESH_POPUP` | 弹窗技能阈值 | 用于识别 `increase_damage.png` 和 `xiaorui.png` |
| `THRESH_CONFIRM` | 确认按钮阈值 | 用于识别 `confirm.png` |

---

## 6. 推荐初始阈值

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

## 7. 什么时候调高阈值？

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

## 8. 什么时候调低阈值？

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

## 9. 保存截图用于调试

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

