# -*- coding: utf-8 -*-
"""
用法: python apply.py <原main.js> <输出文件> <translations.py>

按锚点分组单遍扫描替换（性能关键：不要逐条扫全文）。
翻译表格式（translations.py 中定义 T）:
    T = [ (英文, 中文, [锚点...]), ... ]

可用锚点:
  title label description placeholder message tooltip text emptyMessage
  setTitle setPlaceholder notice cetext
"""
import io, re, sys
import importlib.util

ANCHORS = [
    ("title",        r'\btitle:'),
    ("label",        r'\blabel:'),
    ("description",  r'\bdescription:'),
    ("placeholder",  r'\bplaceholder:'),
    ("message",      r'\bmessage:'),
    ("tooltip",      r'\btooltip:'),
    ("text",         r'\btext:'),
    ("emptyMessage", r'\bemptyMessage:'),
    ("setTitle",     r'\.setTitle\('),
    ("setPlaceholder", r'\.setPlaceholder\('),
    ("notice",       r'Notice\('),   # 含 nc.Notice / Sw.Notice 等命名空间前缀
    ("cetext",       r','),          # createElement 文本子节点
]

RISKY_TAIL = ("===", "!==", "==", "!=", "case ", ".includes(", ".startsWith(",
              ".endsWith(", "indexOf(", ".setAttribute(", "value:", "id:", "key:")


def build_regex(pre):
    # 双引号串允许含 ' ；单引号串允许含 "
    return re.compile(r'(' + pre + r'\s*)'
                      + r'(?:"([^"\\\n]{1,400})"'
                      + r"|'([^'\\\n]{1,400})'" + ')')


def find_all(hay, needle):
    r, i = [], hay.find(needle)
    while i != -1:
        r.append(i)
        i = hay.find(needle, i + 1)
    return r


def audit(raw, en):
    """逐处检测危险语境。返回 (危险数, 类型集, 是否对象键)"""
    hits, kinds, is_key = 0, set(), False
    for q in ('"', "'"):
        nd = q + en + q
        for pos in find_all(raw, nd):
            pre = raw[max(0, pos - 24):pos]
            suf = raw[pos + len(nd): pos + len(nd) + 6]
            for t in RISKY_TAIL:
                if pre.endswith(t):
                    hits += 1
                    kinds.add(t.strip())
                    break
            if re.match(r'^\s*:', suf):
                # 只有前邻 { 或 , 的冒号才是对象键；? 是三元，case 是分支
                left = pre.rstrip()
                if left.endswith('{') or left.endswith(','):
                    is_key = True
    return hits, kinds, is_key


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    src, dst, tbl = sys.argv[1:4]

    raw = io.open(src, "r", encoding="utf-8", errors="replace").read()
    print("原文 %d bytes" % len(raw))

    spec = importlib.util.spec_from_file_location("tr", tbl)
    tr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tr)

    # 版本指纹校验：翻译表若声明了 SOURCE_MD5，就与输入文件比对。
    # 打包后的 main.js 里通常搜不到版本号，只能靠指纹确认"这份翻译表配不配得上"。
    _want = getattr(tr, "SOURCE_MD5", None)
    if _want:
        import hashlib
        _got = hashlib.md5(io.open(src, "rb").read()).hexdigest()
        _ver = getattr(tr, "SOURCE_VERSION", "?")
        if _got == _want:
            print("版本指纹 匹配 -> %s" % _ver)
        else:
            print("!! 版本指纹不匹配：期望 %s (%s)，实际 %s" % (_want, _ver, _got))
            print("   仍会继续替换，但可能有词条失效 —— 留意下方 [零命中] 数量。")

    D = {n: {} for n, _ in ANCHORS}
    for en, zh, anchors in tr.T:
        for a in anchors:
            if a not in D:
                raise SystemExit("未知锚点: %s" % a)
            D[a][en] = zh

    blocked, warn = [], []
    for en, zh, anchors in tr.T:
        hits, kinds, is_key = audit(raw, en)
        if is_key:
            blocked.append((en, zh, "对象键"))
        elif hits:
            warn.append((en, zh, sorted(kinds)))
    for e in {b[0] for b in blocked}:
        for a in D:
            D[a].pop(e, None)
    print("对象键拦截 %d 条 | 比较语境提示 %d 条" % (len(blocked), len(warn)))
    for en, zh, kinds in warn:
        print("  [提示] %-28s 同时出现在 %s 语境（锚点替换不受影响，仅告知）"
              % (en, ",".join(kinds)))

    out, counts, total = raw, {}, 0
    for name, pre in ANCHORS:
        dic = D[name]
        if not dic:
            continue
        rx, local = build_regex(pre), {}

        def rep(m, dic=dic, local=local):
            s = m.group(2) if m.group(2) is not None else m.group(3)
            zh = dic.get(s)
            if zh is None:
                return m.group(0)
            q = '"' if m.group(2) is not None else "'"
            local[s] = local.get(s, 0) + 1
            return m.group(1) + q + zh + q

        out, _ = rx.subn(rep, out)
        for k, v in local.items():
            counts[(name, k)] = counts.get((name, k), 0) + v
        print("  %-15s %4d 处" % (name, sum(local.values())))
        total += sum(local.values())

    io.open(dst, "w", encoding="utf-8").write(out)

    blocked_en = {b[0] for b in blocked}
    missed = [(en, zh, a) for en, zh, a in tr.T
              if en not in blocked_en and not any((aa, en) in counts for aa in a)]

    print("\n总替换 %d 处 | 生效 %d 词条 | 拦截 %d | 零命中 %d"
          % (total, len({k[1] for k in counts}), len(blocked), len(missed)))
    for en, zh, why in blocked:
        print("  [拦截] %s <- %s (%s)" % (en, zh, why))
    for en, zh, a in missed:
        print("  [零命中] %s (锚点 %s)" % (en, ",".join(a)))
    print("输出 %s (%d bytes)" % (dst, len(out)))


if __name__ == "__main__":
    main()
