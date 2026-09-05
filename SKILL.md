---
name: obsidian-copilot-zh
description: 汉化 Obsidian Copilot 插件 4.0.6 的界面（esbuild 打包、英文硬编码、无 i18n 框架）。锚点整段替换 + 危险语境拦截 + node --check 校验，附 614 条现成翻译表。当用户说"汉化/中文化 Obsidian Copilot 插件"时使用。scripts/ 三个脚本可复用于同类插件，但翻译表需重新制作。
agent_created: true
---

# Obsidian Copilot 插件汉化（4.0.6）

> **本仓库的主目标是 Copilot 4.0.6。**
> `scripts/` 下的三个脚本是通用工具，`translations/copilot-4.0.6.py` 只对这一个版本有效 ——
> 换插件或换版本，翻译表必须重做，脚本可以复用。

## 覆盖范围：这是"基础汉化"，不是 100%

实测 **724 处替换 / 614 词条**，覆盖设置面板、聊天界面、右下角弹窗、按钮菜单。

**没翻的部分**（都是有意为之，不是遗漏）：

| 未翻 | 例子 | 原因 |
|---|---|---|
| 设置页顶部标签页 | `Basic` `BYOK` `Advanced` `Self-Host` | 写在 `value:` 字段里；为规避哨兵值风险整类排除了 |
| 品牌名 | `Miyo` `Copilot` `LM Studio` | 专有名词 |
| 模型 / 服务商 ID | `gpt-5.5` `claude-sonnet-4-6` | 标识符 |
| 发给 AI 的工具描述 | 39 条 `description:` | 改中文会**改变模型行为** |
| 模板变量 | `{activeNote}` `{$date}` `{$topic}` | 功能性占位符 |
| 键盘按键名 | `Enter` `Shift + Enter` | 用户要对得上键盘 |
| 第三方库报错 | Zod 的 `must NOT have additional properties` | 用户看不到，零收益 |

## 适用与不适用

**适用**：Obsidian Copilot 4.0.6（`main.js` md5 = `4cda257f5f1f7bdaa43c55830061fcc7`）。

**不适用**（改走别的路）：

**不适用**（改走别的路）：
- 插件已有 `lang/` 或 `locale/` 目录 → 直接加语言文件，并提交 PR 给作者
- 用户希望语言跟随 Obsidian 设置切换 → 需要改源码加 i18n，不是替换字符串能解决的
- 用户无法接受"每次插件更新都要重做" → 先说明这个代价，让用户决定

## 第一步：先判断，别急着改

```bash
# 1) 有没有 i18n 框架
grep -c 'i18next\|useTranslation' main.js        # 非 0 就别用本方案
# 2) 文件规模（决定能不能用编辑器打开）
wc -c main.js && wc -l main.js
```
平均行长 = bytes / lines。**超过 ~2000 字符就别让用户用 VS Code 打开**，会卡死；
直接用脚本改反而更安全。

## 核心原则：锚点整段替换

**只替换 `title:"Chat"` 这样的完整片段，绝不单独替换 `"Chat"`。**

原因：代码里常有 `if (mode === "Chat")` 这类判断。全局替换会把判断条件也改成
中文，导致功能静默失效——这类 bug 极难排查。带锚点替换能完全绕开它。

常用锚点（按"显示位置"选，不按"值位置"选）：

| 锚点 | 形态 | 说明 |
|---|---|---|
| `title:` `label:` `description:` | 对象属性 | 设置项、菜单项 |
| `placeholder:` `tooltip:` `text:` | 对象属性 | 输入框、提示 |
| `.setTitle(` `.setPlaceholder(` | Obsidian API | 设置面板 |
| `Notice(` | 弹窗提示 | **必须含命名空间前缀** |
| `,"..."` | createElement 文本子节点 | JSX 编译后的界面文字 |

> ⚠️ **Notice 的坑**：真实写法常是 `new nc.Notice(` / `new Sw.Notice(`。
> 正则要写 `Notice\(` 而不是 `new\s+Notice\(`，否则会漏掉绝大部分。

## 性能铁律：按锚点分组单遍扫描

**不要逐条扫全文**。500 条 × 5MB = 扫几十 GB，必然超时被杀。

正确做法：每种锚点编译一个正则，全文只扫一遍，命中后查字典。
12 个锚点 = 12 遍，秒级完成。见 `scripts/apply.py`。

## 危险语境拦截

替换前逐处检查每个英文字符串，**只有前邻 `{` 或 `,` 的冒号才算对象键**：

- `{"Chat": {...}` → 前邻 `{` → 对象键，**拦截**
- `[...,"Edit"]` → 工具名/枚举数组，**拦截**
- `x==="tags"?"Tags"` → 前邻 `?` → 三元表达式，**放行**
- `case"cancel":` → 前邻 `case` → switch 分支，**放行**（改的是另一处副本）

> ⚠️ 早期版本把所有 `":"` 都当对象键，误伤了 15 条三元表达式。这个判定必须精确。

## 必须跳过的类别

| 类别 | 例子 | 原因 |
|---|---|---|
| 发给 AI 的工具描述 | `description:"Get the file tree..."` | 改了会**改变模型行为** |
| 模板变量 | `{activeNote}` `{$date}` `{$topic}` | 功能性占位符 |
| 模型 / 服务商 ID | `gpt-5.5` `claude-sonnet-4-6` | 标识符 |
| 品牌名 | `Miyo` `OpenArtifacts` `LM Studio` | 专有名词 |
| 文件路径 / 目录 | `.claude/skills/` `AGENTS.md` | 功能性字符串 |
| 第三方库报错 | Zod 的 `must NOT have additional properties` | 用户看不到，零收益 |
| 对象键 / 枚举值 | `allowedTools:["Read","Write","Edit"]` | 改了功能失效 |

## 校验（不可省略）

1. `node --check main.js` —— 语法闸门
2. 不变量校验 —— `verify.py` 的 `MUST_KEEP` 里填"必须保持英文"的片段，逐个确认还在
3. 中文泄漏扫描 —— `verify.py` 自动比对原文，**只报新增的泄漏**。
   很多插件打包了第三方库（如 Zod）自带的中/日文错误包，那是原文就有的，
   不是我们改的，不报出来。
4. 属性名计数 —— `aria-label` / `data-testid` / `type` / `id` 数量应与原文完全一致

> ⚠️ **Git Bash 的路径坑**：调 Windows 版 node / python 时，`/g/xxx` 会被解析成 `E:\g\xxx`。
> 路径必须写成 `G:/xxx` 或用 PowerShell。
> Python 同样中招——`python scripts/apply.py /e/foo/main.js ...` 会报
> `FileNotFoundError`，把 `/e/` 改成 `E:/` 就好了。

## 安装

1. 先备份原文件到**工作区**（不要放在插件目录里，避免 Obsidian 混淆）
2. 复制到插件目录
3. 检查 Obsidian 是否在运行：`tasklist | grep -i obsidian`
   —— 在运行就必须**重启 Obsidian** 才生效（插件在启动时加载）

## 脚本

- `scripts/extract.py` —— 提取候选字符串，带上下文，输出 markdown 供人工甄别
- `scripts/apply.py` —— 按锚点分组执行替换，输出新文件（不原地改）
- `scripts/verify.py` —— 语法 + 不变量 + 泄漏三重校验

## 翻译表

统一放 `translations/` 目录，按 `插件名-版本.py` 命名：

```python
T = [
    ("Cancel", "取消", ["title", "text"]),
    ("Confirm Delete", "确认删除", ["title"]),
]
```

**现成可直接用的**：`translations/copilot-4.0.6.py`（616 条 / 726 处替换，已实战验证）。

给新插件做翻译表：复制那份文件改内容即可，格式说明见 `translations/README.md`。

用 `\u2019` `\u201c` `\u2026` 等转义写特殊字符，避免手抄出错。

## 完整流程示例

```bash
# 1) 提取候选（只读，不动源文件）
python scripts/extract.py main.js candidates.md

# 2) 人工甄别 candidates.md，挑出真正要翻的，写成 translations/我的插件.py

# 3) 执行替换（输出新文件，不原地改）
python scripts/apply.py main.js main.zh.js translations/我的插件.py

# 4) 三重校验
node --check main.zh.js
python scripts/verify.py main.js main.zh.js

# 5) 备份后安装，重启 Obsidian
```
