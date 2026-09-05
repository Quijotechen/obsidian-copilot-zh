# -*- coding: utf-8 -*-
"""
用法: python extract.py <main.js> <输出.md>

按锚点提取候选 UI 字符串，带上下文，输出 markdown 供人工甄别。
这一步是只读的，绝不修改源文件——甄别质量决定最终汉化质量。
"""
import io, re, sys
from collections import Counter, defaultdict

ANCHORS = [
    ("obj:title",        r'\btitle:'),
    ("obj:label",        r'\blabel:'),
    ("obj:description",  r'\bdescription:'),
    ("obj:placeholder",  r'\bplaceholder:'),
    ("obj:message",      r'\bmessage:'),
    ("obj:tooltip",      r'\btooltip:'),
    ("obj:text",         r'\btext:'),
    ("obj:emptyMessage", r'\bemptyMessage:'),
    ("api:setTitle",     r'\.setTitle\('),
    ("api:setPlaceholder", r'\.setPlaceholder\('),
    ("api:setTooltip",   r'\.setTooltip\('),
    ("api:Notice",       r'Notice\('),   # 含命名空间前缀
]


def build_regex(pre):
    return re.compile(r'(' + pre + r'\s*)'
                      + r'(?:"([^"\\\n]{1,300})"'
                      + r"|'([^'\\\n]{1,300})'" + ')')


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]

    raw = io.open(src, "r", encoding="utf-8", errors="replace").read()
    N = len(raw)

    by = defaultdict(Counter)
    ctx1 = {}
    for name, pre in ANCHORS:
        for m in build_regex(pre).finditer(raw):
            s = m.group(2) if m.group(2) is not None else m.group(3)
            by[name][s] += 1
            if s not in ctx1:
                ctx1[s] = raw[max(0, m.start() - 140):m.end() + 60].replace("\n", " ")

    out = ["# UI 候选字符串清单（只读提取）", "",
           "来源: `%s`" % src, "", "| 锚点 | unique | total |", "|---|---|---|"]
    for name in sorted(by, key=lambda k: -sum(by[k].values())):
        out.append("| `%s` | %d | %d |" % (name, len(by[name]), sum(by[name].values())))

    for name in sorted(by, key=lambda k: -sum(by[k].values())):
        out += ["", "## %s" % name, "", "次数 | 字符串 | 上下文", "---|---|---"]
        for s, n in by[name].most_common():
            c = ctx1.get(s, "").replace("|", "\\|")
            if len(c) > 220:
                c = c[:220] + "…"
            out.append("%d | `%s` | `%s`" % (n, s.replace("|", "\\|"), c))

    io.open(dst, "w", encoding="utf-8").write("\n".join(out))

    tot = sum(sum(c.values()) for c in by.values())
    print("锚点 %d 类 | unique %d | total %d" % (len(by), len(ctx1), tot))
    for name in sorted(by, key=lambda k: -sum(by[k].values())):
        print("  %-20s unique=%4d total=%4d" % (name, len(by[name]), sum(by[name].values())))
    print("已写出 %s" % dst)


if __name__ == "__main__":
    main()
