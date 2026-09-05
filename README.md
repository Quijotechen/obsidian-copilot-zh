# obsidian-copilot-zh

把 **Obsidian Copilot 插件 4.0.6** 的英文界面汉化成中文的skill。

不改源码结构，只替换界面文案。**724 处替换 / 614 条词条**，覆盖设置面板、聊天界面、  
右下角弹窗、按钮菜单 —— 日常使用基本都是中文。

> ⚠️ **这是"基础汉化"，不是 100% 汉化。**  
> 设置页顶部的标签页（`Basic` / `BYOK` / `Advanced` / `Self-Host` 等）仍是英文，  
> 品牌名、模型 ID、发给 AI 的工具描述也刻意保留原文。原因见下方[未翻译的部分](#未翻译的部分)。

---

## 实测结果

| 项目                        | 结果        |
| ------------------------- | --------- |
| 替换处数 / 词条数                | 724 / 614 |
| `node --check`            | ✅ 通过      |
| 不变量（16 项必须保持英文的片段）        | ✅ 全部还在    |
| 新增中文泄漏（11 类扫描）            | ✅ 0 处     |
| 属性名计数（`aria-label` 等 5 项） | ✅ 与原文完全一致 |

## 安装为 AI 技能

```bash
# WorkBuddy
cp -r . ~/.workbuddy/skills/obsidian-copilot-zh

# Claude Code
cp -r . ~/.claude/skills/obsidian-copilot-zh
```

装好后，对 AI 说「把 Obsidian Copilot 插件汉化」就会自动加载。

## 开始前：确认版本对得上

打包后的 `main.js` 里**搜不到版本号**（`grep '4.0.6'` = 0 命中），所以只能比对指纹：

```bash
md5sum main.js
# 期望：4cda257f5f1f7bdaa43c55830061fcc7   （4,847,247 字节）
```

`scripts/apply.py` 会自动做这个比对，不匹配会警告。**版本不对也能跑**，但会有词条失效 ——  
留意输出里的 `[零命中]` 数量，那是要补译的部分。

## 快速开始

```bash
# 1) 备份你的原文件（放工作区，别放插件目录）
cp "<vault>/.obsidian/plugins/copilot/main.js" ./main.js.bak

# 2) 执行替换（输出新文件，绝不原地改）
python scripts/apply.py main.js main.zh.js translations/copilot-4.0.6.py

# 3) 校验
node --check main.zh.js
python scripts/verify.py main.js main.zh.js

# 4) 安装并重启 Obsidian
cp main.zh.js "<vault>/.obsidian/plugins/copilot/main.js"
```

> ⚠️ Obsidian 在运行就**必须重启**才生效 —— 插件是启动时加载的。

## 为什么不能"全局替换字符串"

这是最容易踩的坑：

```js
if (mode === "Chat") { ... }        // 判断条件
label: "Chat"                        // 界面文字
```

两处都是 `"Chat"`。全局替换会把判断条件也改成中文，导致功能**静默失效** ——  
不报错、不崩溃，只是悄悄不对，这类 bug 极难排查。

本仓库用三条防线规避：

| 防线         | 做法                                                  |
| ---------- | --------------------------------------------------- |
| **锚点整段替换** | 只替换 `label:"Chat"` 这个完整片段，绝不单独替换 `"Chat"`           |
| **危险语境拦截** | 逐处检查：出现在 `===` / `!==` / `case` / 对象键 / 枚举数组里的，拒绝翻译 |
| **三重校验**   | `node --check` 语法闸门 + 不变量 + 中文泄漏扫描                  |

## 未翻译的部分

**这些是刻意保留的，不是遗漏。**

| 类别          | 例子                                           | 原因                          |
| ----------- | -------------------------------------------- | --------------------------- |
| 设置页顶部标签页    | `Basic` `BYOK` `Advanced` `Self-Host`        | 写在 `value:` 字段；为规避哨兵值风险整类排除 |
| 发给 AI 的工具描述 | 39 条 `description:`                          | 改中文会**改变模型行为**              |
| 品牌名         | `Miyo` `Copilot` `LM Studio` `OpenArtifacts` | 专有名词                        |
| 模型 / 服务商 ID | `gpt-5.5` `claude-sonnet-4-6`                | 标识符                         |
| 模板变量        | `{activeNote}` `{$date}` `{$topic}`          | 功能性占位符，改了功能就废               |
| 键盘按键名       | `Enter` `Shift + Enter`                      | 用户要对得上键盘                    |
| 行业缩写 / 协议   | `BYOK` `MCP`                                 | 中文圈通用                       |
| 第三方库报错      | Zod 的 `must NOT have additional properties`  | 用户看不到，零收益                   |

## 插件更新后怎么办

Obsidian 社区插件一更新，`main.js` 就被覆盖，汉化**全部失效**。这是字符串替换方案的  
固有代价，没法绕开。

重做时**旧翻译表能直接复用**：

```bash
python scripts/apply.py 新版main.js main.zh.js translations/copilot-4.0.6.py
```

看输出里的 `[零命中]` —— 那些就是新版本里失效的词条，只需补译这些。  
补完记得把文件另存为 `copilot-新版本.py`。

## 想拿去汉化别的插件？

**脚本可以复用，翻译表不能。**

`scripts/` 下三个脚本是通用工具，适用于任何「esbuild 打包 + 英文硬编码 + 无 i18n 框架」  
的插件。但 `translations/copilot-4.0.6.py` 里的 614 条是 Copilot 专属的，换个插件就是空表。

自制翻译表的步骤：

```bash
# 1) 提取候选（只读，不动源文件）
python scripts/extract.py main.js candidates.md

# 2) 人工甄别 candidates.md，写成 translations/你的插件-版本.py
#    格式见 translations/README.md

# 3) 替换 + 校验
python scripts/apply.py main.js main.zh.js translations/你的插件-版本.py
python scripts/verify.py main.js main.zh.js
```

**先判断插件适不适用**：

```bash
grep -c 'i18next\|useTranslation' main.js
```

- 非 0 → 插件有 i18n 框架，别用本方案，直接加语言文件并给作者提 PR
- 0 → 适用

另外，如果插件已有 `lang/` 或 `locale/` 目录，也应该走官方语言文件那条路。

## 目录结构

```
.
├── SKILL.md                     技能定义（WorkBuddy / Claude 加载用）
├── README.md                    本文件
├── LICENSE                      MIT
├── scripts/
│   ├── extract.py               提取候选字符串，带上下文
│   ├── apply.py                 按锚点分组替换 + 版本指纹校验
│   └── verify.py                不变量 + 中文泄漏 + 属性名计数三重校验
└── translations/
    ├── README.md                翻译表格式与锚点说明
    └── copilot-4.0.6.py         Copilot 4.0.6，614 条（可直接用）
```



## 环境要求

- Python 3.8+（标准库，无第三方依赖）
- Node.js（仅用于 `node --check`）

> **Windows / Git Bash 注意**：调 Windows 版 python / node 时，`/g/xxx` 会被解析成  
> `E:\g\xxx`。路径要写成 `G:/xxx`，否则报 `FileNotFoundError`。

## 许可

MIT。详见 [LICENSE](LICENSE)。

翻译表内容是对插件界面文字的翻译，仅用于个人学习交流；  
请在插件作者许可的范围内使用。
