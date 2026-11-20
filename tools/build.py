# -*- coding: utf-8 -*-
"""构建站点数据。

输入  : sources/（docx、config、语言文件） + tools/data/（别名表、截图转录、发布日、主程序日志）
输出  : data/changelog.json（原始数据） / data/changelog.js（供站点 <script> 直接加载）

用法  : python tools/build_alias.py && python tools/build.py
"""
import os, re, json, io
from docx import Document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
READ = os.path.join(SRC, "readme")
TOOLDATA = os.path.join(ROOT, "tools", "data")
OUTDIR = os.path.join(ROOT, "data")

# sources/ 为原始参考资料，按 .gitignore 不纳入仓库，只保留在本地
if not os.path.isdir(SRC):
    raise SystemExit(
        "找不到 sources/ 目录。\n"
        "该目录存放原始参考资料（各版本 docx、config、zh-CN.json），出于不公开原始资料的要求\n"
        "未纳入 git 仓库，需要从本地备份恢复后才能重建数据。\n"
        "若只想更新站点成品，data/changelog.js 已随仓库提供，无需重新构建。"
    )

alias = json.load(open(os.path.join(TOOLDATA, "alias_map.json"), encoding="utf-8"))
alias2id = alias["alias2id"]
official = alias["official"]


def norm(s):
    return s.replace("·", "・").replace(" ", "").replace("　", "").replace("（", "(").replace("）", ")")


def lookup(name, parent=None):
    n = name.strip().rstrip("：:")
    n = re.sub(r'[（(]\s*调整负责[：:][^)）]*[)）]', '', n).strip()
    n = re.sub(r'^(新角色|角色重置|新辅助|新增|新人物)\s*', '', n).strip()
    # if this is a generic form word and we have a parent, try combined name first
    candidates = [n]
    if parent and GENERIC_FORM.match(n.strip()):
        pclean = re.sub(r'[（(]\s*调整负责[：:][^)）]*[)）]', '', parent).strip().rstrip("：:")
        candidates.append(pclean + " " + n.strip())
        candidates.append(pclean + n.strip())
    for cand in candidates:
        nc = norm(cand)
        if nc in alias2id:
            return alias2id[nc]
    # longest partial (on the plain name)
    best = None
    nc = norm(n)
    for a, fid in alias2id.items():
        if len(a) >= 2 and a in nc:
            if best is None or len(a) > len(best[0]):
                best = (a, fid)
    return best[1] if best else None


# ---------- docx parsing ----------
DOCX_MAP = [
    ("3.8.8", ["3.8.8更新内容.docx"]),
    ("3.8.6.5", ["历史留档/3.8.6.5更新内容.docx"]),
    ("3.8.6", ["历史留档/3.8.6更新内容.docx"]),
    ("3.8.5.8", ["历史留档/3.8.5.8更新内容.docx"]),
    ("3.8.5", ["历史留档/3.8.5更新内容.docx"]),
    ("3.8.4", ["历史留档/3.8.4并阶改动.docx"]),
    ("3.8.3", ["历史留档/3.8.3并阶改动.docx"]),
    ("3.8.2", ["历史留档/3.8.2并阶改动.docx"]),
    ("3.8.1", ["历史留档/3.8.1并阶改动.docx"]),
    ("3.8", ["历史留档/3.8并阶改动.docx"]),
]
SECTION_WORDS = {"主人物", "人物", "辅助", "系统级改动", "主程序改动", "人物：", "辅助：", "主人物：", "系统级改动："}
SKILL_TOKEN = re.compile(r'^(adj|adu|ad|kj|sj|wj|ku|su|wu|ki|wi|si|j|u|i|k|o|l|ksj|kwj|ksu|kwu|s)\b|^[adjkuwiso]{1,4}\s*[:：]', re.I)
CHANGE_VERB = re.compile(r'^(修复|调整|优化|新增|重置|移除|改为|删除|更换|重做|回调|削弱|加强|统一|补全|补充|加快|减慢|增加|减少|提升|降低|修改|取消|禁用|启用|适配|同步|限定|上调|下调|实现|现|若|当|为|将|携带|获得|角色存在|任意一方)')
ITEM_HINT = re.compile(r'[→\+\-\d]|，|、|；|。|bug|BUG|帧|伤害|僵直|攻击面|后摇|前摇|无敌|霸体|破防|集气|纽带|判定|位移|击退|击飞|特效|音效|语音|捕捉|吸附|闪花|白钢|钢身|术中|受击|命中|重击|轻击|形态|cd|CD|地图|场景|台阶|防御|起身|倒地|空中|地面|墙角|碰撞|子弹|道具|受身|替身|气量|耐力|血量|生命|位移|镜头|AI')

# lines that are NOT real characters (maps, section leftovers, mis-split change lines)
MAP_WORDS = re.compile(r'^(雾隐村|宇智波村|木叶村|砂隐村|双极之丘|森林|现世|流魂街|瀞灵廷|地图|场景)')
NON_CHAR = re.compile(r'^(任意一方|下调至低阶|上调至高阶|特殊机制|角色设计稿|注[:：]|说明[:：]|详情见|※|天赋|换人|站起|其他)')


def read_paras(path):
    doc = Document(path)
    out = []
    for pa in doc.paragraphs:
        t = pa.text.strip()
        if not t:
            continue
        bold = any(r.bold for r in pa.runs)
        out.append((t, bold))
    for tb in doc.tables:
        for row in tb.rows:
            cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            j = " | ".join(c for c in cells if c)
            if j:
                out.append((j, False))
    return out


def is_meta(t):
    return (t.startswith("主程序改动内容见") or t.startswith("“真厉害”活动人物改动内容见") or
            t.startswith("详细") or re.match(r'^\d+(\.\d+)*\s*更新内容$', t) or
            t.startswith("角色设计稿") or t.startswith("人物设计稿"))


def looks_like_item(t):
    if SKILL_TOKEN.match(t):
        return True
    if CHANGE_VERB.match(t):
        return True
    if len(t) > 22:
        return True
    if ITEM_HINT.search(t):
        return True
    if re.search(r'[:：]', t):
        return True
    return False


GENERIC_FORM = re.compile(r'^(始解|卍解|常态|归刃|义骸|虚化|暴走|完全体|二阶|一阶|超|改|改版|强化)$')


def parse_doc(paras):
    entries = []
    cur_section = "主人物"
    cur_name = None
    last_bold = None
    root_bold = None
    has_bold = any(b and t not in SECTION_WORDS for t, b in paras)
    for t, bold in paras:
        if t in SECTION_WORDS or t.rstrip("：:") in SECTION_WORDS:
            cur_section = t.rstrip("：:")
            if cur_section in ("人物", "人物："):
                cur_section = "主人物"
            cur_name = None
            last_bold = None
            root_bold = None
            continue
        if is_meta(t):
            continue
        if MAP_WORDS.match(t):
            continue  # map names even if bold
        if bold:
            if NON_CHAR.match(t):  # change-fragment wrongly bolded -> attach to previous char
                if cur_name is not None:
                    cur_name["items"].append(t)
                continue
            parent = last_bold
            # root = nearest ancestor that is not itself a generic form word
            if not GENERIC_FORM.match(t.strip().rstrip("：:")):
                root_bold = t
            entries.append({"section": cur_section, "name": t, "items": [], "parent": parent, "root": root_bold})
            cur_name = entries[-1]
            last_bold = t
            continue
        if has_bold:
            if cur_name is not None:
                cur_name["items"].append(t)
            continue
        if MAP_WORDS.match(t):
            continue  # map names: not characters, not changes -> skip entirely
        if NON_CHAR.match(t):
            # "下调至低阶"/"特殊机制"/"任意一方..." are change-line fragments
            if cur_name is not None:
                cur_name["items"].append(t)
            continue
        if looks_like_item(t):
            if cur_name is not None:
                cur_name["items"].append(t)
        else:
            entries.append({"section": cur_section, "name": t, "items": []})
            cur_name = entries[-1]
    return [e for e in entries if e["items"]]


# ---------- aggregate ----------
VERSION_ORDER = ["3.8.8.6", "3.8.8.5", "3.8.8.4", "3.8.8.3", "3.8.8.2", "3.8.8.1", "3.8.8",
                 "3.8.6.6", "3.8.6.5", "3.8.6", "3.8.5.11", "3.8.5.10", "3.8.5.9", "3.8.5.8", "3.8.5.2", "3.8.5.1", "3.8.5",
                 "3.8.4.5", "3.8.4.4", "3.8.4.3", "3.8.4.2", "3.8.4.1", "3.8.4", "3.8.3.1", "3.8.3",
                 "3.8.2.1", "3.8.2", "3.8.1.1", "3.8.1", "3.8.0.3", "3.8.0.2", "3.8.0.1", "3.8.0"]

# 有版本号但暂时没有任何改动记录的版本（后续拿到资料再补）
PENDING_VERSIONS = {"3.8.5.10": "该版本暂无改动记录，待补充"}


def doc_key(v):
    parts = v.split(".")
    while len(parts) > 2 and parts[-1] == "0":
        parts.pop()
    return ".".join(parts)


# 主人物 / 辅助 分开：同一角色若两边都有改动，生成两条独立记录。
# key = (baseId, role)；role 取自 docx 段落所在分组 / 截图分组标题。
ROLE_MAIN, ROLE_ASSIST = "主人物", "辅助"
chars = {}   # key: (fid, role)
unmatched = {}


def split_name(raw):
    """去掉「（调整负责：XXX）」这类近期版本的额外标签——它标注改动由谁完成，不属于角色名。"""
    s = re.sub(r'[（(]\s*调整负责[^）)]*[）)]', '', raw or '')
    return s.strip().rstrip("：:")


def add_change(fid, ver, item, role):
    disp = official.get(fid, fid)
    key = (fid, role)
    cid = fid if role == ROLE_MAIN else fid + "::assist"
    c = chars.setdefault(key, {
        "id": cid, "baseId": fid, "name": disp, "avatar": fid,
        "versions": {}, "isAssist": role == ROLE_ASSIST, "role": role
    })
    c["versions"].setdefault(ver, []).append(item)


# docx
for ver, files in DOCX_MAP:
    for f in files:
        paras = read_paras(os.path.join(READ, f))
        entries = parse_doc(paras)
        for e in entries:
            fid = lookup(e["name"], e.get("root"))
            if fid is None and e.get("root"):
                # form word whose combo failed: fall back to the root character
                fid = lookup(e["root"])
            role = ROLE_ASSIST if e.get("section") == "辅助" else ROLE_MAIN
            if fid is None:
                unmatched.setdefault(e["name"], []).append(ver)
                # still keep under raw name
                fid = "RAW::" + e["name"]
                key = (fid, role)
                c = chars.setdefault(key, {"id": fid, "baseId": fid, "name": split_name(e["name"]),
                                           "avatar": None, "versions": {}, "isAssist": role == ROLE_ASSIST, "role": role})
                for it in e["items"]:
                    c["versions"].setdefault(ver, []).append(it)
                continue
            for it in e["items"]:
                add_change(fid, ver, it, role)

# 截图中标注了形态的条目：归到该形态自己的角色卡片，而不是混进基础形态卡片。
# key = (基础角色ID, 形态名) -> 形态角色ID；形态即基础形态时指向自身。
FORM_SPLIT = {
    ("aizen", "队长"): "aizen_captain",
    ("gin", "卍解"): "gin_bankai", ("gin", "始解"): "gin",
    ("ichigo", "卍解"): "ichigo_bankai",
    ("ichigo", "虚化"): "ichigo_vizard", ("ichigo", "虚化 卍解"): "ichigo_vizard",
    ("ichigo", "虚化暴走"): "ichigo_half_mask", ("ichigo", "虚化暴走 卍解"): "ichigo_hmb",
    ("lee", "杜门"): "lee_tomon",
    ("naruto", "尾兽化暴走"): "naruto_ver2", ("naruto", "尾兽外衣"): "naruto_ver1",
    ("pain", "天道"): "pain_tendo",
    ("renji", "卍解"): "renji_bankai", ("renji", "始解"): "renji",
    ("rukia", "义骸"): "rukia", ("rukia", "始解"): "rukia_shikai",
    ("sasuke", "须佐能乎"): "sasuke_susanoo", ("sasuke", "鹰小队"): "sasuke_taka",
    ("uryuu", "银岭弧雀"): "uryuu_ginreigojiaku",
}
form_split_used = {}

# screenshots
shots = json.load(open(os.path.join(TOOLDATA, "screenshots.json"), encoding="utf-8"))
for ver, sobj in shots.items():
    for g in sobj.get("groups", []):
        role = ROLE_ASSIST if g.get("title") == "辅助" else ROLE_MAIN
        for ch in g.get("characters", []):
            raw = ch.get("name", "")
            fid = lookup(raw)
            form = ch.get("form")
            if fid is None:
                unmatched.setdefault(raw, []).append(ver + "(图)")
                fid = "RAW::" + raw
                key = (fid, role)
                c = chars.setdefault(key, {"id": fid, "baseId": fid, "name": split_name(raw),
                                           "avatar": None, "versions": {}, "isAssist": role == ROLE_ASSIST, "role": role})
            # 形态条目归到形态自己的卡片；形态前缀不再需要（卡片本身即该形态）
            target = fid
            if form and not fid.startswith("RAW::"):
                fclean = re.sub(r'[（(]\s*调整负责[^）)]*[）)]', '', form).strip()
                target = FORM_SPLIT.get((fid, fclean))
                if target is None:
                    form_split_used.setdefault((fid, fclean), 0)
                    form_split_used[(fid, fclean)] += len(ch.get("items", []))
                    target = fid  # 未知形态：保守起见仍留在基础角色
            for it in ch.get("items", []):
                txt = it
                if txt.startswith("〔"):  # 源数据若已有前缀则去掉
                    txt = re.sub(r'^〔.+?〕', '', txt)
                if fid.startswith("RAW::"):
                    c["versions"].setdefault(ver, []).append(txt)
                else:
                    add_change(target, ver, txt, role)


def vsort(v):
    return VERSION_ORDER.index(v) if v in VERSION_ORDER else 99


# 阵营映射：直接读取游戏 config 的 comic_type（0=死神, 1=火影, -1/缺省=其他）
CAMP_FROM_CONFIG = {}
for _fn in ("config/fighter.xml", "config/assist.xml"):
    _s = io.open(os.path.join(SRC, _fn), encoding="utf-8").read()
    for _m in re.finditer(r'<fighter\s+id="([^"]+)"[^>]*?comic_type="(-?\d+)"', _s):
        _fid, _t = _m.group(1), _m.group(2)
        CAMP_FROM_CONFIG[_fid] = {"0": "bleach", "1": "naruto"}.get(_t, "other")


def camp_of(fid):
    return CAMP_FROM_CONFIG.get(fid, "other")


# reverse map: fid -> list of aliases
id2alias = {}
for a, fid in alias2id.items():
    id2alias.setdefault(fid, []).append(a)

for (fid, role), c in chars.items():
    c["versions"] = {v: c["versions"][v] for v in sorted(c["versions"], key=vsort)}
    c["changeCount"] = sum(len(x) for x in c["versions"].values())
    alias_set = set(id2alias.get(fid, []))
    # 别名仅供内部检索；剔除带「调整负责」标签的写法与正式名本身
    alias_set = {a for a in alias_set if "调整负责" not in a}
    alias_set.discard(c["name"])
    alias_set.discard(c["name"].replace(" ", ""))
    c["aliases"] = sorted(alias_set, key=lambda x: -len(x))[:8]
    c["camp"] = camp_of(fid)

# mainlog
mainlog = json.load(open(os.path.join(TOOLDATA, "mainlog.json"), encoding="utf-8"))
logdate = {v["version"]: v["date"] for v in mainlog}

release = json.load(open(os.path.join(TOOLDATA, "release_dates.json"), encoding="utf-8"))
rel = {}
for v in VERSION_ORDER:
    d = release.get(v, {})
    rel[v] = {"releaseDate": d.get("date"), "confidence": d.get("confidence"),
              "source": d.get("source", ""),
              "note": d.get("note", "") or PENDING_VERSIONS.get(v, ""),
              "logDate": logdate.get(v, "")}

all_images = [{"version": v, "path": f"media/patches/{v}补丁调整.png", "title": f"{v} 补丁调整"}
              for v in ["3.8.8.6", "3.8.8.5", "3.8.8.4", "3.8.8.3", "3.8.8.2", "3.8.8.1"]]
ref_images = [
    {"path": "media/refs/角色俗称表.jpg", "title": "玩家俗称表"},
    {"path": "media/refs/辅助俗称图.jpg", "title": "辅助俗称图 3.8.8.5"},
]

out = {
    "characters": sorted(chars.values(), key=lambda c: (-c["changeCount"], c["name"])),
    "unmatched": sorted(unmatched.items(), key=lambda x: -len(x[1])),
    "versions": VERSION_ORDER,
    "pendingVersions": PENDING_VERSIONS,
    "releaseDates": rel,
    "mainlog": mainlog,
    "allImages": all_images,
    "refImages": ref_images,
    "generatedAt": "2026-11-20",
    "generatedFrom": "sources/readme（各版本更新 / 并阶改动 docx + 补丁调整长图转录 + 中文语言文件正式命名 + 玩家俗称表别名）+ sources/config（阵营）+ 主程序开发日志（补充），发布日经官方渠道查证",
    "stats": {
        "characters": len([c for c in chars.values() if not c["id"].startswith("RAW::")]),
        "withAvatar": len([c for c in chars.values() if c["avatar"]]),
        "versionCount": len(VERSION_ORDER),
        "versionsWithData": len(set(v for c in chars.values() for v in c["versions"])),
        "totalChangeEntries": sum(c["changeCount"] for c in chars.values()),
        "releaseDatesFound": sum(1 for v in rel.values() if v["releaseDate"]),
    }
}

os.makedirs(OUTDIR, exist_ok=True)
txt = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
io.open(os.path.join(OUTDIR, "changelog.json"), "w", encoding="utf-8").write(txt)
io.open(os.path.join(OUTDIR, "changelog.js"), "w", encoding="utf-8").write(
    "/* 由 tools/build.py 生成，请勿手工编辑。源数据见 sources/ 与 tools/data/ */\n"
    "window.CHANGELOG_DATA=" + txt + ";\n")

print("STATS", out["stats"])
print("json bytes:", len(txt.encode("utf-8")))
print("\nTOP:")
for c in out["characters"][:8]:
    print(" ", c["name"], "|", c["id"], "|", c["changeCount"], "条 |", len(c["versions"]), "版本")
if form_split_used:
    print("\n未映射的形态组合(仍留在基础角色):", dict(form_split_used))
print("\nUNMATCHED", len(unmatched))
for n, vs in out["unmatched"][:20]:
    print(" ", n, vs[:3])
