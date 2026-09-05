# 翻译表目录

按 `插件名-版本.py` 命名，例如 `copilot-4.0.6.py`。

## 现有翻译表

| 文件 | 插件 | 版本 | 词条数 | 状态 |
|---|---|---|---|---|
| `copilot-4.0.6.py` | Obsidian Copilot | 4.0.6 | 614 | ✅ 实战验证（724 处替换，node --check 通过，新增中文泄漏 0 处） |

> **本仓库的主目标是 Obsidian Copilot。** 这里的翻译表只对这一个插件版本有效。
> 脚本（`scripts/`）可以复用于同类打包插件，但翻译表必须重新制作。
>
> Obsidian 社区插件一更新 `main.js` 就会被覆盖，翻译表需要重做。
> 版本写在文件名里，就是为了新旧版本能并存对照。

## 格式

```python
# -*- coding: utf-8 -*-
T = [
    ("英文原文", "中文译文", ["锚点1", "锚点2"]),
    ("Cancel",   "取消",     ["title", "text"]),
]
```

第三个参数是**允许匹配的锚点列表**：只有字符串出现在这些锚点后面时才替换。
这是安全设计的核心——避免在 `if (mode === "Cancel")` 这类逻辑判断里误改。

### 可用锚点

| 锚点 | 匹配形态 | 典型场景 |
|---|---|---|
| `title` | `title:"..."` | 设置项、弹窗标题 |
| `label` | `label:"..."` | 表单标签、菜单项 |
| `description` | `description:"..."` | 说明文字（⚠️ 发给 AI 的工具描述别翻） |
| `placeholder` | `placeholder:"..."` | 输入框占位符 |
| `message` | `message:"..."` | 提示信息 |
| `tooltip` | `tooltip:"..."` | 悬浮提示 |
| `text` | `text:"..."` | 通用文本 |
| `emptyMessage` | `emptyMessage:"..."` | 空状态提示 |
| `setTitle` | `.setTitle(...)` | Obsidian 设置面板 API |
| `setPlaceholder` | `.setPlaceholder(...)` | Obsidian 设置面板 API |
| `notice` | `Notice(...)` | 右下角弹窗（自动匹配 `nc.Notice` 等带前缀写法） |
| `cetext` | `,"..."` | JSX 编译后的文本子节点 |

## 制作新翻译表的步骤

1. `python ../scripts/extract.py main.js candidates.md` —— 提取候选（只读）
2. 打开 `candidates.md`，人工甄别，**决定每一条要不要翻**
3. 按上面格式写成 `你的插件-版本.py`
4. `python ../scripts/apply.py main.js main.zh.js 你的插件-版本.py`
5. 看输出的 `[拦截]` 和 `[零命中]` 提示，回头调整

## 翻译时应当跳过

| 类别 | 例子 | 原因 |
|---|---|---|
| 发给 AI 的工具描述 | `description:"Get the file tree..."` | 改了会**改变模型行为** |
| 模板变量 | `{activeNote}` `{$date}` `{$topic}` | 功能性占位符 |
| 模型 / 服务商 ID | `gpt-5.5` `claude-sonnet-4-6` | 标识符 |
| 品牌名 | `Miyo` `OpenArtifacts` `LM Studio` | 专有名词 |
| 文件路径 / 目录 | `.claude/skills/` `AGENTS.md` | 功能性字符串 |
| 键盘按键名 | `Enter` `Escape` | 用户要对得上键盘 |
| 第三方库报错 | Zod 的 `must NOT have additional properties` | 用户看不到，零收益 |

## 特殊字符

用 Unicode 转义写，避免编码问题：

```python
("Don\u2019t ask again", "不再询问", ["label"]),   # ’ 右单引号
("Loading\u2026", "加载中\u2026", ["text"]),        # … 省略号
```