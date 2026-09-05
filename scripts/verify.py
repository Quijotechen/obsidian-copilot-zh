# -*- coding: utf-8 -*-
"""
用法: python verify.py <原main.js> <新main.js>

三道校验:
  1. node --check 语法（需外部调用）
  2. 不变量——必须保持英文的片段是否还在
  3. 中文泄漏——是否误改了对象键 / 分支 / 类名
"""
import io, re, sys

CJK = r'[\u4e00-\u9fff]'

# 必须保持英文的片段——翻译后它们必须原样还在，否则就是改坏了。
#
# 下面这份是 Obsidian Copilot 4.0.6 实测过的清单（每条都验证过在原文中存在）。
# 换插件/换版本时请按同样思路重列：模板变量、键盘映射、模型与服务商 ID、
# 品牌名、第三方库报错、哨兵值（被 === 判断引用的字符串）。
#
# 怎么找？先跑 scripts/extract.py 生成候选清单，人工挑出
# "长得像文案、其实是功能"的那些。
MUST_KEEP = [
    ('模板变量', '{activeNote}'),
    ('文件名模板', '{$date}_{$time}__{$topic}'),
    ('键盘映射', '13:"Enter"'),
    ('模型 ID', 'gpt-5.5'),
    ('模型 ID 2', 'claude-sonnet-4-6'),
    ('技能目录', '.claude/skills/'),
    ('代理文件', 'AGENTS.md'),
    ('品牌名', 'Miyo'),
    ('品牌名 2', 'LM Studio'),
    ('品牌名 3', 'OpenArtifacts'),
    ('第三方库报错', 'must NOT have additional properties'),
    ('行业缩写', 'BYOK'),
    ('哨兵值', 'Select Model'),
    ('工具名', 'allowedTools'),
    ('CSS 前缀', 'tw-'),
    ('协议缩写', 'MCP'),
]

LEAK_PATS = [
    ('中文对象键', '"[^"\\n]*' + CJK + '[^"\\n]*"\\s*:'),
    ('中文 switch 分支', r'case\s*"[^"\n]*' + CJK),
    ('中文 CSS 类名', r'"tw-[^"\n]*' + CJK),
    ('中文 === 比较', r'[!=]==\s*"[^"\n]*' + CJK),
    ('中文 .includes(', r'\.includes\(\s*"[^"\n]*' + CJK),
    ('中文 .startsWith(', r'\.startsWith\(\s*"[^"\n]*' + CJK),
    ('中文 value:', r'\bvalue:\s*"[^"\n]*' + CJK),
    ('中文 key:', r'\bkey:\s*"[^"\n]*' + CJK),
    ('中文 id:', r'\bid:\s*"[^"\n]*' + CJK),
    ('中文 return', r'return\s*"[^"\n]*' + CJK),
    ('中文 setAttribute', r'setAttribute\([^)]*' + CJK),
]

# 这些属性名的出现次数应与原文完全一致
ATTRS = ['"aria-label":', '"data-testid":', '"type":', '"id":', '"variant":']


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    old = io.open(sys.argv[1], "r", encoding="utf-8", errors="replace").read()
    new = io.open(sys.argv[2], "r", encoding="utf-8", errors="replace").read()

    print("原文 %d / 新文 %d / 增量 %+d" % (len(old), len(new), len(new) - len(old)))

    bad = 0
    print("\n===== 不变量 =====")
    for name, frag in MUST_KEEP:
        ok = frag in old and frag in new
        bad += 0 if ok else 1
        print("  %-4s %s" % ("OK" if ok else "FAIL", name))

    print("\n===== 中文泄漏 =====")
    leak = 0
    for label, pat in LEAK_PATS:
        # 只算"新增"的泄漏。原文已有的中文/日文不算——
        # 很多插件打包了第三方库（如 Zod）的多语言错误包，本来就带中/日文，
        # 那不是我们改的，报出来只会误导。
        old_hits = {m.group(0) for m in re.finditer(pat, old)}
        new_hits = {m.group(0) for m in re.finditer(pat, new)}
        delta = new_hits - old_hits
        leak += len(delta)
        print("  %-18s -> 新增 %d 处（原文已有 %d 处，已排除）"
              % (label, len(delta), len(old_hits)))
        for s in list(delta)[:3]:
            print("        ...%s..." % s[:110].replace("\n", " "))

    print("\n===== 属性名计数 =====")
    for k in ATTRS:
        co, cn = old.count(k), new.count(k)
        print("  %-16s 原:%5d 新:%5d  %s" % (k, co, cn, "OK" if co == cn else "差异!"))
        if co != cn:
            bad += 1

    old_cjk = set(re.findall(r'"[^"\n]*' + CJK + r'[^"\n]*"', old))
    new_cjk = set(re.findall(r'"[^"\n]*' + CJK + r'[^"\n]*"', new))
    print("\n新增中文字符串 %d 个（原文已有 %d 个）" % (len(new_cjk - old_cjk), len(old_cjk)))
    print("\n结论: %s" % ("通过" if bad == 0 and leak == 0 else "需人工复核"))


if __name__ == "__main__":
    main()
