# -*- coding: utf-8 -*-
"""Build authoritative alias map from language file + fan nicknames + user corrections."""
import json, io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
OUT = os.path.join(ROOT, "tools", "data", "alias_map.json")

lang = json.load(io.open(os.path.join(SRC, "zh-CN.json"), encoding="utf-8"))
fighters = lang["name"]["fighter"]

assists = lang["name"].get("assist", {})
# 少数角色有头像与配置但语言文件里只留了旧版名，补上正式显示名
EXTRA_NAMES = {"obito_trueColors": "宇智波·带土"}
def official(fid):
    if fid in EXTRA_NAMES:
        return EXTRA_NAMES[fid]
    v = fighters.get(fid)
    if v is None:
        v = assists.get(fid)
    if v is None:
        return fid
    return v["name"] if isinstance(v, dict) else v

# alias (as written in docs/screenshots) -> fighter ID
# Sources: fan nickname chart (昵称表), user corrections, common knowledge
ALIASES = {
    # ---- 一护家族 ----
    "一护":"ichigo","黑崎一护":"ichigo","黑崎·一护":"ichigo","零段一护":"ichigo","零段":"ichigo",
    "始护":"ichigo","黑崎·一护 始解":"ichigo","始解":"ichigo",
    "半虚":"ichigo_half_mask","黑崎·一护 虚化暴走":"ichigo_half_mask","内虚":"ichigo_half_mask","白牛头":"ogihci_vasto_lord",
    "半卍":"ichigo_hmb","黑崎·一护 虚化暴走 卍解":"ichigo_hmb",
    "卍护":"ichigo_bankai","一护 卍解":"ichigo_bankai","黑崎·一护 卍解":"ichigo_bankai",
    "虚化":"ichigo_vizard","虚化卍解":"ichigo_vizard","虚化 卍解":"ichigo_vizard",
    "半虚":"ichigo_half_mask","虚化暴走":"ichigo_half_mask","虚化暴走 卍解":"ichigo_hmb",
    "天锁":"tensa","天锁斩月":"tensa","真正的天锁斩月":"ichigo_true_bankai",
    "卍虚":"ogihci_bankai","白·一护 卍解":"ogihci_bankai",
    "始虚":"ogihci","白一护":"ogihci","白·一护":"ogihci",
    "完全虚化":"ichigo_vasto_lord","黑崎·一护 完全虚化":"ichigo_vasto_lord",
    "修行":"ichigo_dangai","最后的月牙天冲":"ichigo_dangai",
    "黑崎一护-千年血战前篇（二段）":"ichigo_zero","黑崎一护-血战前篇Ⅱ":"ichigo_zero",

    # ---- 蓝染 ----
    "蓝染":"aizen","蓝剑":"aizen","崩玉一阶":"aizen","蓝染·惣右介":"aizen",
    "队蓝":"aizen_captain","蓝染 队长":"aizen_captain","蓝染惣右介 队长":"aizen_captain","蓝染·惣右介 队长":"aizen_captain",
    "蓝染 无间封印":"aizen_muken","蓝染惣右介 无间封印":"aizen_muken","蓝染·惣右介 无间封印":"aizen_muken","新增 蓝染惣右介 无间封印":"aizen_muken",

    # ---- 市丸银 ----
    "银":"gin","市丸银":"gin","市丸·银":"gin","市丸·银（调整负责：哈士奇）":"gin",
    "卍银":"gin_bankai","市丸·银 卍解":"gin_bankai","市丸银·卍解":"gin_bankai","新角色 市丸·银 卍解":"gin_bankai",
    "市丸银·卍解 by:B站昭泽安仁":"gin_bankai","市丸·银·卍解":"gin_bankai",

    # ---- 白哉/露琪亚/恋次 ----
    "白哉":"byakuya","朽木白哉":"byakuya","朽木·白哉":"byakuya","帝白":"byakuya_bankai","白哉卍解":"byakuya_bankai","吭景":"byakuya_bankai",
    "露琪亚":"rukia","义骸":"rukia","朽木·露琪亚 义骸":"rukia","露琪亚 义骸":"rukia",
    "始露":"rukia_shikai","露琪亚 始解":"rukia_shikai","露琪亚始解":"rukia_shikai",
    "恋次":"renji","阿散井恋次":"renji","阿散井·恋次":"renji","卍恋":"renji_bankai","恋次 卍解":"renji_bankai","新人物 卍解恋次":"renji_bankai",

    # ---- 冬狮郎/剑八/碎蜂 ----
    "冬狮郎":"toushirou","日番谷冬狮郎":"toushirou","日番谷·冬狮郎":"toushirou",
    "剑八":"kenpachi","更木剑八":"kenpachi","更木·剑八":"kenpachi","角色重置 更木·剑八":"kenpachi",
    "碎蜂":"soifon","角色重置 碎蜂":"soifon","8600":"yachiru",
    "八千流":"yachiru","草鹿八千流":"yachiru","草鹿·八千流":"yachiru",

    # ---- 十六番队/其他死神 ----
    "夜一":"yoruichi","四枫院夜一":"yoruichi","四枫院·夜一":"yoruichi","四枫院·夜一（调整负责：diaznez）":"yoruichi",
    "山本":"yamamoto","山本元柳斋":"yamamoto","山本·元柳斎·重国":"yamamoto",
    "春水":"shunsui","京乐春水":"shunsui","京乐·春水":"shunsui",
    "涅":"mayuri","涅茧利":"mayuri","涅·茧利":"mayuri","涅·茧利（调整负责 创意呈现：BVN素材组）":"mayuri",
    "涅·萤利":"mayuri","涅·萤利（调整负责 创意呈现：BVN 素材组）":"mayuri",
    "剑心":"kenshin","绯村剑心":"kenshin","绯村·剑心 浪客":"kenshin","浪客":"kenshin","拔刀斋":"kenshin_battousai","绯村·剑心 拔刀斋":"kenshin_battousai",
    "一角":"ikkaku","斑目一角":"ikkaku","斑目·一角":"ikkaku",
    "浦原喜助":"urahara","浦原·喜助":"urahara","店长":"urahara","新辅助浦原喜助":"urahara",
    "平子":"hirako","平子·真子":"hirako","日世里":"hiyori","猿柿日世里":"hiyori",
    "吉良":"kira","吉良伊鹤":"kira",
    "勇音":"isane","虎彻勇音":"isane","新辅助虎彻勇音":"isane",
    "六车拳西":"kensei","拳西":"kensei","新辅助 六车拳西":"kensei",
    "莉露卡":"riruka","毒峰莉露卡":"riruka","新辅助 毒峰莉露卡":"riruka",
    "香燐":"karin","香磷":"karin","新辅助 香燐":"karin",
    "音梦":"nemu","涅·音梦":"nemu","涅·音梦（调整负责 创意呈现：BVN 素材组）":"nemu",

    # ---- 破面/十刃 ----
    "葛六":"grimmjow","葛力姆乔":"grimmjow","葛力姆乔·贾卡杰克":"grimmjow","葛力姆乔·贾卡杰克（调整负责：油条）":"grimmjow","自称阿飞的男人":"tobi",
    "小乌":"ulquiorra","乌尔奇奥拉":"ulquiorra","乌尔奇奥拉·西法":"ulquiorra",
    "大乌":"ulquiorra_murcielago","乌尔奇奥拉 归刃":"ulquiorra_murcielago","乌尔奇奥拉·西法 归刃":"ulquiorra_murcielago",
    "史塔克":"starrk","柯雅泰·史塔克":"starrk","史塔克 归刃":"starrk_resurrection","史塔克·归刃":"starrk_resurrection",
    "赫利贝尔":"harribel","赫丽贝尔":"harribel","赫丽贝尔 归刃":"harribel_resurrection","赫丽贝尔 归刃":"harribel_resurrection","蒂雅·赫丽贝尔 归刃":"harribel_resurrection","三刃":"harribel_resurrection",
    "妮露":"nel","妮莉艾露·杜·欧德修凡克":"nelliel","妮露·归刃":"nelliel",
    "多鲁多尼":"dordoni",
    "萨尔阿波罗":"szayelaporro",
    "诺伊特拉":"nnoitra",

    # ---- 鸣人家族 ----
    "鸣人":"naruto","漩涡鸣人":"naruto","漩涡·鸣人":"naruto","渣鸣":"naruto",
    "仙鸣":"naruto_sennin","仙人":"naruto_sennin","仙人模式":"naruto_sennin","漩涡·鸣人 仙人模式":"naruto_sennin",
    "金鸣":"naruto_kyubi","九尾查克拉":"naruto_kyubi","九尾查克拉模式":"naruto_kyubi","鸣人 九尾查克拉":"naruto_kyubi","漩涡·鸣人 九尾查克拉模式":"naruto_kyubi",
    "尾兽外衣":"naruto_ver1","一尾":"naruto_ver1","漩涡·鸣人 尾兽外衣":"naruto_ver1","一尾：":"naruto_ver1",
    "尾兽化暴走":"naruto_ver2","二尾":"naruto_ver2","漩涡·鸣人 尾兽化暴走":"naruto_ver2","四尾：":"naruto_ver2","四尾":"naruto_ver2",

    # ---- 佐助/鼬/斑/带土 ----
    "佐助":"sasuke","宇智波佐助":"sasuke","宇智波·佐助":"sasuke","佐助 天手力":"sasuke_amenotejikara","宇智波·佐助 天手力":"sasuke_amenotejikara",
    "咒佐":"sasuke_juin","渣佐":"sasuke_juin","咒印佐助":"sasuke_juin",
    "鹰佐":"sasuke_taka","鹰小队":"sasuke_taka","佐助 鹰小队":"sasuke_taka","宇智波·佐助 鹰小队":"sasuke_taka",
    "须佐":"sasuke_susanoo","须佐能乎":"sasuke_susanoo","宇智波·佐助 须佐能乎":"sasuke_susanoo",
    "鼬":"itachi","宇智波鼬":"itachi","宇智波·鼬":"itachi","宇智波·鼬（调整负责：diaznez）":"itachi",
    "斑":"madara","宇智波斑":"madara","宇智波·斑":"madara",
    # 带引号的「"宇智波·斑"」正式名对应 obito（白面具时期带土），不是真·斑 madara
    "“宇智波·斑”":"obito",
    "带土":"obito","“宇智波·斑” 伊邪那岐":"obito","带一":"obito","带二":"obito_trueColors",
    "宇智波·带土":"obito_trueColors","obito_trueColors":"obito_trueColors",
    "六道":"pain","宇智波·带土 六道仙人":"obito_rikudou",
    "阿飞":"tobi","自称阿飞的男人":"tobi","水门":"minato","波风水门":"minato","波风·水门":"minato","波风·水门 by:Mitsune（御狐）":"minato",

    # ---- 佩恩/长门 ----
    "佩恩":"pain","佩恩 六道":"pain","佩恩·六道":"pain",
    "天道":"pain_tendo","佩恩 天道":"pain_tendo",
    "长门":"nagato","青年长门":"nagato","青年长门 by:黑咲_琉璃":"nagato",

    # ---- 卡卡西/凯/李/樱 ----
    "卡卡西":"kakashi","旗木卡卡西":"kakashi","旗木·卡卡西":"kakashi","渣卡":"kakashi",
    "神卡":"kakashi_kamui","卡卡西 神威":"kakashi_kamui","旗木·卡卡西 神威":"kakashi_kamui",
    "忍卡":"kakashi_gsw","忍战卡卡西":"kakashi_gsw","卡卡西 忍界大战":"kakashi_gsw","旗木·卡卡西 忍界大战":"kakashi_gsw",
    "凯":"guy","迈特凯":"guy","迈特·凯":"guy","李":"lee","小李":"lee","李洛克":"lee","李·洛克":"lee","李 洛克":"lee","李·洛克":"lee",
    "杜门":"lee_tomon","杜李":"lee_tomon","杜门李":"lee_tomon","李·洛克 杜门":"lee_tomon",
    "小樱":"sakura","春野樱":"sakura","春野·樱":"sakura","春野·樱（调整负责：油条）":"sakura",
    "百豪":"sakura_byakugo","百豪樱":"sakura_byakugo","春野·樱 百豪":"sakura_byakugo",

    # ---- 其他火影 ----
    "大蛇丸":"orochimaru","君麻吕":"kimimaro","君麻吕：":"kimimaro","君麻吕 音忍五人众":"kimimaro_goninshu",
    "我爱罗":"gaara","手鞠":"temari","迪达拉":"deidara","小迪":"deidara","蝎":"sasori","绯流琥":"hiruko","人傀儡·绯流琥":"hiruko",
    "鬼鲛":"kisame","干柿鬼鲛":"kisame","自来也":"jiraiya","纲手":"tsunade","鹿丸":"shikamaru","奈良鹿丸":"shikamaru",
    "雏田":"hinata","日向雏田":"hinata","日向·雏田":"hinata","井野":"ino","丁次":"choji","宁次":"neji","日向宁次":"neji","天天":"tenten","佐井":"sai",
    "重吾":"juggo","水月":"suigetsu","鬼灯水月":"suigetsu","兜":"kabuto","药师兜":"kabuto","药师·兜":"kabuto",
    "绝":"zetsu","小南":"konan","大野木":"onoki","土影":"onoki","奇拉比":"killerbee","羽高":"utakata","志志雄":"shishio","志志雄真实":"shishio","波妮":"bonnie",
    "雨龙":"uryuu","石田雨龙":"uryuu","石田·雨龙":"uryuu","雨龙 银岭弧雀":"uryuu_ginreigojiaku","银岭弧雀":"uryuu_ginreigojiaku","麻雀":"uryuu_ginreigojiaku","常态（弧雀）":"uryuu_ginreigojiaku",
    "茶渡":"chad","茶渡泰虎":"chad","茶渡·泰虎":"chad","魔人茶渡":"sado_muerte","二虎":"sado_muerte","茶渡·泰虎 魔人":"sado_muerte",

    # ---- generic-form combinations (parent + form) ----
    "恋次 卍解":"renji_bankai","恋次卍解":"renji_bankai","阿散井·恋次 卍解":"renji_bankai",
    "白哉 卍解":"byakuya_bankai","白哉卍解":"byakuya_bankai",
    "一护 卍解":"ichigo_bankai","一护卍解":"ichigo_bankai",
    "冬狮郎 卍解":"toushirou_bankai","日番谷·冬狮郎 卍解":"toushirou_bankai",
    "露琪亚 始解":"rukia_shikai","露琪亚始解":"rukia_shikai",
    "织姬":"orihime","井上织姬":"orihime","井上·织姬":"orihime",
    "队长":"aizen_captain","乱菊":"rangiku","松本乱菊":"rangiku","松本·乱菊":"rangiku",
    "牛头":"ogihci_vasto_lord","牛头一护":"ogihci_vasto_lord",
    "一尾":"naruto_ver1","四尾":"naruto_ver2",
    "新辅助深作&志麻（蛤蟆夫妇）":"fukasaku","深作":"fukasaku","志麻":"fukasaku",
    "斩月 死神之力":"zangetsu","斩月":"zangetsu","斩月死神之力":"zangetsu",
}

# remove duplicate-key accidents by normalizing at build time
def norm(s):
    return s.replace("·","・").replace(" ","").replace("　","").replace("（","(").replace("）",")")

alias_norm = {}
for a, fid in ALIASES.items():
    alias_norm[norm(a)] = fid

# build canon list from used fids
used = sorted(set(ALIASES.values()))
canon = [{"id": fid, "name": official(fid), "avatar": fid} for fid in used]

# 正式名映射必须同时覆盖 fighter 与 assist 两个节点：
# 部分角色（如 kon=魂、shishio=志志雄真实）只存在于 assist 节点，
# 若只遍历 fighters，这些 ID 会在网页上直接显示成原始 ID。
all_ids = set(fighters) | set(assists) | set(EXTRA_NAMES)
out = {"canon": canon, "alias2id": alias_norm, "official": {fid: official(fid) for fid in all_ids}}
json.dump(out, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("canon ids:", len(canon), "aliases:", len(alias_norm))
# show any aliases pointing to missing face files
missing = [c for c in canon if not os.path.exists(os.path.join(ROOT, "face", c["avatar"] + ".png"))]
print("canon missing face:", [(c["id"], c["name"]) for c in missing])
