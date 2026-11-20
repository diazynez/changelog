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
# 辅助位与主人物位并非一一对应（辅助只有 hiruko / starrk_resurrection 等），
# 辅助段落的解析必须落在 assist.xml 的节点上。
assist2id = alias.get("assist2id", {})
ASSIST_FROM_MAIN = alias.get("assistFromMain", {})
ASSIST_IDS = set(alias.get("assistIds", []))


def norm(s):
    return s.replace("·", "・").replace(" ", "").replace("　", "").replace("（", "(").replace("）", ")")


# 「父级角色 + 形态词」→ 角色ID。
# 没有这张表时，形态词会退化成裸词查询（如「始解」默认指向黑崎·一护），
# 把白哉/冬狮郎/恋次等角色的始解改动错误地并进一护卡片。
FORM_PARENT = {
    ("ichigo", "始解"): "ichigo",
    ("ichigo", "卍解"): "ichigo_bankai",
    ("ichigo", "虚化"): "ichigo_vizard",
    ("byakuya", "始解"): "byakuya",
    ("byakuya", "卍解"): "byakuya_bankai",
    ("toushirou", "始解"): "toushirou",
    ("toushirou", "卍解"): "toushirou_bankai",
    ("renji", "始解"): "renji",
    ("renji", "卍解"): "renji_bankai",
    ("rukia", "始解"): "rukia_shikai",
    ("rukia", "义骸"): "rukia",
    ("ogihci", "始解"): "ogihci",
    ("ogihci", "卍解"): "ogihci_bankai",
    ("zangetsu", "始解"): "zangetsu",
    ("uryuu", "常态"): "uryuu",
    ("ulquiorra", "常态"): "ulquiorra",
    ("ulquiorra", "归刃"): "ulquiorra_murcielago",
    # 「斩月 死神之力」= 白·一护；其下的始解/卍解就是白·一护的始解/卍解
    ("ogihci", "始解"): "ogihci",
    ("ogihci", "卍解"): "ogihci_bankai",
    # 3.8 的「卍护 › 虚化」其实是虚化卍解
    ("ichigo_bankai", "虚化"): "ichigo_vizard",
}


def lookup(name, parent=None, role=None):
    n = name.strip().rstrip("：:")
    n = re.sub(r'[（(]\s*调整负责[：:][^)）]*[)）]', '', n).strip()
    n = re.sub(r'^(新角色|角色重置|新辅助|新增|新人物)\s*', '', n).strip()
    # 辅助位有独立的角色集合：先按辅助表精确查，命中即用
    if role == ROLE_ASSIST:
        nc = norm(n)
        if nc in assist2id:
            return assist2id[nc]
    # 形态词（始解/卍解/虚化…）必须优先按「父级 + 形态」解析，
    # 否则裸词会先命中别名表里的默认角色，把别的角色的数据串进来。
    if parent and GENERIC_FORM.match(n.strip()):
        pclean = re.sub(r'[（(]\s*调整负责[：:][^)）]*[)）]', '', parent).strip().rstrip("：:")
        pid = lookup(pclean, role=role)          # 父级自身（非形态词，不会递归）
        if pid and (pid, n) in FORM_PARENT:
            return FORM_PARENT[(pid, n)]
        for cand in (pclean + " " + n, pclean + n):
            nc = norm(cand)
            if nc in alias2id:
                return alias2id[nc]
            if role == ROLE_ASSIST and nc in assist2id:
                return assist2id[nc]
        # 组合与表都没命中：宁可不猜，交给调用方按父级兜底
        return None
    fid = None
    nc = norm(n)
    if nc in alias2id:
        fid = alias2id[nc]
    else:
        # longest partial (on the plain name)
        best = None
        for a, aid in alias2id.items():
            if len(a) >= 2 and a in nc:
                if best is None or len(a) > len(best[0]):
                    best = (a, aid)
        fid = best[1] if best else None
    if role == ROLE_ASSIST and fid:
        # 主人物位解析结果若不在辅助节点集合里，按历史对应关系换到辅助形态；
        # 换不到就判为未匹配（绝不生成「主人物的辅助卡」这种错数据）。
        if fid in ASSIST_IDS:
            return fid
        return ASSIST_FROM_MAIN.get(fid)
    return fid


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
# 「角色设计稿：黑崎·一护 半虚 卍解」这类标题自带角色名，是角色标题而不是说明文字。
# 旧逻辑把它当元信息丢掉，导致紧随其后的整段正文被追加到上一条角色名下
# （3.8.3 的恋次卍解设计稿就是这样整段进了八千流）。
DESIGN_DRAFT = re.compile(r'^(?:角色|人物)设计稿\s*[：:]\s*(.+)$')
DESIGN_GROUP = re.compile(r'^(?:角色|人物)设计稿\s*$')


def parse_doc(paras):
    entries = []
    cur_section = "主人物"
    cur_name = None
    last_bold = None
    root_bold = None
    skip_after = False   # 地图等非角色标题之后，正文不属于任何角色
    draft_mode = False   # 「角色设计稿」分组之后的内容属于主人物
    has_bold = any(b and t not in SECTION_WORDS for t, b in paras)
    for t, bold in paras:
        if t in SECTION_WORDS or t.rstrip("：:") in SECTION_WORDS:
            cur_section = t.rstrip("：:")
            if cur_section in ("人物", "人物："):
                cur_section = "主人物"
            cur_name = None
            last_bold = None
            root_bold = None
            skip_after = False
            draft_mode = False
            continue
        if bold and DESIGN_DRAFT.match(t):
            nm = DESIGN_DRAFT.match(t).group(1).strip()
            entries.append({"section": ROLE_MAIN, "name": nm, "items": [], "parent": None, "root": nm})
            cur_name = entries[-1]
            last_bold = nm
            root_bold = nm
            skip_after = False
            draft_mode = True      # 设计稿后紧跟的多半还是主人物，直到下一个分组标题
            continue
        if bold and DESIGN_GROUP.match(t):
            cur_name = None
            last_bold = None
            root_bold = None
            draft_mode = True
            continue
        if is_meta(t):
            continue
        if MAP_WORDS.match(t):
            # 地图名的后续行是场景改动，不是角色改动：整段丢弃
            skip_after = True
            cur_name = None
            continue
        if bold:
            if NON_CHAR.match(t):  # change-fragment wrongly bolded -> attach to previous char
                if cur_name is not None:
                    cur_name["items"].append(t)
                continue
            skip_after = False
            parent = last_bold
            # root = nearest ancestor that is not itself a generic form word
            if not GENERIC_FORM.match(t.strip().rstrip("：:")):
                root_bold = t
            sec = ROLE_MAIN if draft_mode else cur_section
            entries.append({"section": sec, "name": t, "items": [], "parent": parent, "root": root_bold})
            cur_name = entries[-1]
            last_bold = t
            continue
        if skip_after:
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
PENDING_VERSIONS = {}


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


# 个别版本里同一个标题指向不同角色，只能按版本区分。
# 3.8.5.8 的「黑崎一护」带「角色素材、技能组翻新，重新还原了一护在早期剧情中…」的重做说明，
# 指的是零段（无始解的基础一护），不是一护包的基础形态。
VERSION_NAME_OVERRIDE = {
    ("3.8.5.8", "黑崎一护"): "ichigo_zero",
    ("3.8.5.8", "黑崎·一护"): "ichigo_zero",
}

# 文档里的层级笔误：3.8.4 在「恋次」段末多写了「义骸」，这三条是露琪亚义骸的改动
# （义骸是露琪亚专属形态，恋次没有该形态）。按「版本 + 父级 + 标题」定向修正。
ENTRY_OVERRIDE = {
    ("3.8.4", "恋次", "义骸"): "rukia",
}

# docx
for ver, files in DOCX_MAP:
    for f in files:
        paras = read_paras(os.path.join(READ, f))
        entries = parse_doc(paras)
        for e in entries:
            role = ROLE_ASSIST if e.get("section") == "辅助" else ROLE_MAIN
            fid = ENTRY_OVERRIDE.get((ver, split_name(e.get("root") or ""), split_name(e["name"])))
            if fid is None:
                fid = VERSION_NAME_OVERRIDE.get((ver, split_name(e["name"])))
            if fid is not None and role == ROLE_ASSIST and fid not in ASSIST_IDS:
                fid = ASSIST_FROM_MAIN.get(fid)
            if fid is None:
                fid = lookup(e["name"], e.get("root"), role)
            if fid is None and e.get("root"):
                # form word whose combo failed: fall back to the root character
                fid = lookup(e["root"], None, role)
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
    ("sasuke", "鹰佐"): "sasuke_taka", ("sasuke", "须佐"): "sasuke_susanoo",
    # 旧版补丁截图里的简写形态
    ("aizen", "崩玉一阶"): "aizen",
    ("byakuya", "始解"): "byakuya", ("byakuya", "吭景"): "byakuya_bankai",
    ("ichigo", "始解"): "ichigo", ("ichigo", "半卍"): "ichigo_hmb",
    ("kimimaro", "音忍五人众"): "kimimaro_goninshu",
    ("naruto", "渣鸣"): "naruto",
    ("naruto_sennin", "仙鸣"): "naruto_sennin", ("naruto_sennin", "金鸣"): "naruto_kyubi",
    ("pain", "六道"): "pain",
    ("toushirou", "卍解"): "toushirou_bankai", ("toushirou", "始解"): "toushirou",
    ("uryuu", "银岭弧雀"): "uryuu_ginreigojiaku",
    # 「斩月 死神之力」= 白·一护，其下始解/卍解分别为白·一护与白·一护 卍解
    ("ogihci", "始解"): "ogihci", ("ogihci", "卍解"): "ogihci_bankai",
}
form_split_used = {}

# 补丁长图：screenshots.json 为 3.8.8 起的补丁长图转录，
# docx_shots.json 为 3.8.8 以前各版本 docx 里内嵌的补丁截图转录。
for _src in ("screenshots.json", "docx_shots.json"):
    shots = json.load(open(os.path.join(TOOLDATA, _src), encoding="utf-8"))
    for ver, sobj in shots.items():
        for g in sobj.get("groups", []):
            role = ROLE_ASSIST if g.get("title") == "辅助" else ROLE_MAIN
            for ch in g.get("characters", []):
                raw = ch.get("name", "")
                fid = lookup(raw, None, role)
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
# config 把联动角色塞进了死神槽位（comic_type=0），但它们不属于《死神》IP，
# 按作品归到「其他」；带二同理，缺配置时按 IP 归火影。
CAMP_OVERRIDE = {
    "kenshin": "other", "kenshin_battousai": "other",   # 浪客剑心
    "shishio": "other",                                  # 浪客剑心
    "obito_trueColors": "naruto",                        # 火影忍者
}
FIGHTER_IDS = set()
for _fn in ("config/fighter.xml", "config/assist.xml"):
    _s = io.open(os.path.join(SRC, _fn), encoding="utf-8").read()
    for _m in re.finditer(r'<fighter\s+id="([^"]+)"[^>]*?comic_type="(-?\d+)"', _s):
        _fid, _t = _m.group(1), _m.group(2)
        CAMP_FROM_CONFIG[_fid] = {"0": "bleach", "1": "naruto"}.get(_t, "other")
    if _fn.endswith("fighter.xml"):
        FIGHTER_IDS = set(re.findall(r'<fighter\s+id="([^"]+)"', _s))

# 防线：辅助卡必须落在 assist.xml 的节点上，主人物卡必须落在 fighter.xml 的节点上。
# 违反说明某个标题又被解析到了错误的一侧（历史 bug：辅助的蝎生成 sasori::assist）。
# 个别角色只在 select.xml 里注册（如带二的 trueColors），fighter.xml 只有其 _old 版
MAIN_ONLY_EXTRA = {"obito_trueColors"}
bad_assist = [(c["id"], c["name"]) for c in chars.values() if c["isAssist"] and c["baseId"] not in ASSIST_IDS]
bad_main = [(c["id"], c["name"]) for c in chars.values()
            if not c["isAssist"] and not c["id"].startswith("RAW::")
            and c["baseId"] not in FIGHTER_IDS and c["baseId"] not in MAIN_ONLY_EXTRA]


def camp_of(fid):
    if fid in CAMP_OVERRIDE:
        return CAMP_OVERRIDE[fid]
    if fid in CAMP_FROM_CONFIG:
        return CAMP_FROM_CONFIG[fid]
    # 未直接登记时按同角色的旧版推断（带二的 trueColors 只在 select.xml 注册，
    # fighter.xml 里只有 obito_trueColors_old）
    return CAMP_FROM_CONFIG.get(fid + "_old", "other")


# reverse map: fid -> list of aliases
id2alias = {}
for a, fid in alias2id.items():
    id2alias.setdefault(fid, []).append(a)

# ---------------------------------------------------------------------------
# 分阶与完整角色清单：以 select.xml 为准（selects.xml 含未完成角色，不采用）
# select.xml 用注释把选人界面切成「低阶 / 中阶 / 高阶 / 黑屋隐藏阶」若干行，
# 辅助界面在 <assist_list> 里单独分「突进 / 功能 / 贴身 / 控场 / 范围」类型，不分阶。
# ---------------------------------------------------------------------------
SELECT_TIER, SELECT_ORDER, SELECT_MAIN_IDS, SELECT_ASSIST_IDS = {}, {}, [], []
_sel = io.open(os.path.join(SRC, "config", "select.xml"), encoding="utf-8").read()
_main_part, _assist_part = _sel.split("<assist_list>")
_TIER_PREFIX = [("低阶", "low"), ("中阶", "mid"), ("高阶", "high"), ("黑屋隐藏阶", "god")]


def _sel_items(body):
    """取 <item> 的 id；alterFighter 是可切换的同位形态，算同一位置。"""
    out = []
    for m in re.finditer(r'<item([^>]*)>([^<]*)</item>', body):
        attrs, txt = m.group(1), m.group(2).strip()
        if not txt or txt.startswith("random") or txt == "xb_placeholder_active":
            continue
        if txt not in out:
            out.append(txt)
        alt = re.search(r'alterFighter="([^"]+)"', attrs)
        if alt:
            for a in alt.group(1).split(","):
                a = a.strip()
                if a and a not in out:
                    out.append(a)
    return out


_blocks = re.split(r'<!--\s*([^>]*?)\s*-->', _main_part)
for _i in range(1, len(_blocks), 2):
    _name, _body = _blocks[_i], _blocks[_i + 1]
    _t = next((v for k, v in _TIER_PREFIX if _name.startswith(k)), None)
    if not _t:
        continue
    for _x in _sel_items(_body):
        if _x not in SELECT_TIER:
            SELECT_TIER[_x] = _t
            SELECT_ORDER[_x] = len(SELECT_ORDER)
            SELECT_MAIN_IDS.append(_x)
for _x in _sel_items(_assist_part):
    if _x != "debug" and _x not in SELECT_ASSIST_IDS:
        SELECT_ASSIST_IDS.append(_x)


def _bare(fid):
    return fid[:-4] if fid.endswith("_old") else fid


def tier_of(fid):
    """主人物分阶；select 里的 id 可能带 _old 后缀（如 obito_trueColors_old）。"""
    return SELECT_TIER.get(fid) or SELECT_TIER.get(fid + "_old")


def order_of(fid):
    return SELECT_ORDER.get(fid, SELECT_ORDER.get(fid + "_old", 999))


def name_tags(name):
    """把「黑崎·一护 虚化暴走 卍解」拆成主名 + 形态标签，供前端渲染成徽章。"""
    parts = [p for p in re.split(r'\s+', (name or '').strip()) if p]
    if not parts:
        return name or "", []
    return parts[0], parts[1:]


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
    c["tier"] = None if role == ROLE_ASSIST else tier_of(fid)
    c["order"] = order_of(fid)
    c["nameBase"], c["nameTags"] = name_tags(c["name"])

# ---------------------------------------------------------------------------
# 补全 select.xml 里存在、但历史文档没有任何改动的角色：给一张 0 条的空卡，
# 保证「角色一览」覆盖游戏内全部可选主人物 / 辅助。
# ---------------------------------------------------------------------------
_face_dir = os.path.join(ROOT, "face")
_have_faces = {f[:-4] for f in os.listdir(_face_dir) if f.endswith(".png")} if os.path.isdir(_face_dir) else set()
added_empty = []
for _fid in SELECT_MAIN_IDS:
    _f = _bare(_fid)
    if (_f, ROLE_MAIN) in chars or any(k[0] == _f and k[1] == ROLE_MAIN for k in chars):
        continue
    _nm = official.get(_f) or _f
    _base, _tags = name_tags(_nm)
    chars[(_f, ROLE_MAIN)] = {
        "id": _f, "baseId": _f, "name": _nm, "nameBase": _base, "nameTags": _tags,
        "avatar": _f if _f in _have_faces else None, "versions": {}, "isAssist": False,
        "role": ROLE_MAIN, "changeCount": 0, "aliases": [], "camp": camp_of(_f),
        "tier": tier_of(_f), "order": order_of(_f),
    }
    added_empty.append(_f)
for _fid in SELECT_ASSIST_IDS:
    _f = _bare(_fid)
    key = (_f, ROLE_ASSIST)
    if key in chars:
        continue
    _nm = official.get(_f) or _f
    _base, _tags = name_tags(_nm)
    chars[key] = {
        "id": _f + "::assist", "baseId": _f, "name": _nm, "nameBase": _base, "nameTags": _tags,
        "avatar": _f if _f in _have_faces else None, "versions": {}, "isAssist": True,
        "role": ROLE_ASSIST, "changeCount": 0, "aliases": [], "camp": camp_of(_f),
        "tier": None, "order": 999,
    }
    added_empty.append(_f + "::assist")

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
    # 默认顺序：主人物在前、辅助沉底；主人物内按改动条数降序
    "characters": sorted(chars.values(), key=lambda c: (c["isAssist"], -c["changeCount"], c["name"])),
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
        "withChanges": len([c for c in chars.values() if c["changeCount"]]),
        "noChanges": len([c for c in chars.values() if not c["changeCount"]]),
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
if added_empty:
    print("\n按 select.xml 补入的 0 改动角色:", added_empty)
print("json bytes:", len(txt.encode("utf-8")))
print("\nTOP:")
for c in out["characters"][:8]:
    print(" ", c["name"], "|", c["id"], "|", c["changeCount"], "条 |", len(c["versions"]), "版本")
if form_split_used:
    print("\n未映射的形态组合(仍留在基础角色):", dict(form_split_used))
print("\nUNMATCHED", len(unmatched))
for n, vs in out["unmatched"][:20]:
    print(" ", n, vs[:3])
if bad_assist:
    print("\n!! 辅助卡指向了非辅助节点:", bad_assist)
if bad_main:
    print("\n!! 主人物卡指向了非主人物节点:", bad_main)
