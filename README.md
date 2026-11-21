# 死神VS火影 竞技版 · 角色改动档案

以**角色**为核心的版本改动档案站点。把各版本《更新内容 / 并阶改动》文档与官方补丁长图里的调整，
按角色聚合到一张卡片上，并标注版本发布日；主程序开发日志作为补充。

- 站点：`index.html`（Vue 3，**运行时库已内置于 `assets/vendor/`，无任何外部请求**）
- 数据：`data/changelog.js`（构建产物）
- 当前规模：135 个角色 / 形态（其中 4 个辅助暂无改动记录，仅保留位置）、2724 条改动、33 个版本、30 个查证到的发布日

### 角色档案页的筛选与排序

- **阵营**：死神 / 火影忍者 / 其他，取自 `config/*.xml` 的 `comic_type`（联动角色按作品归属修正）。
- **类型**：主人物 / 辅助。
- **分阶**：低阶 / 中阶 / 高阶 / 神阶，取自 `config/select.xml` 的分行注释（`黑屋隐藏阶` = 神阶）。辅助不分阶，选中具体阶时只列主人物。
- **排序**：按改动条数（默认）/ 按最近改动 / 按选人顺序 / 按名称。**无论怎么排，辅助始终沉底到角色之后**。
  「按最近改动」以版本号新旧判定（3.8.8 比 3.8.4.5 新，非字符串比较），取该角色最近一次有改动的版本；无改动记录的角色排在本组最后。
- **形态徽章**：角色名里代表形态的后缀（如「黑崎·一护 虚化暴走 卍解」的「虚化暴走」「卍解」）单独渲染成标签，与主名分开。
- 角色卡以 `select.xml` 为**唯一权威**：覆盖其中全部可选主人物 / 辅助；`selects.xml` 含未完成角色，**不采用**。`fighter.xml` 中被注释掉的停放角色（如浦原·喜助的主人物节点）即使有文档提及也不建卡。
- 例外：**香燐**已不是可选主人物（`fighter.xml` 的主人物节点被注释、`select.xml` 主人物清单无此位，仅辅助位仍在列），按要求保留其历史改动主人物卡，但不分阶、不计入神阶，标记为「未列阶」。

---

## 目录结构

站点文件与源数据、工具严格分开，只有下面「站点」部分会对外发布。
`sources/`（原始参考资料）**不纳入仓库**，只保留在本地。

```
.
├── index.html                  # 【站点】唯一页面
├── assets/
│   ├── style.css               # 【站点】样式
│   ├── app.js                  # 【站点】Vue 应用逻辑
│   └── vendor/
│       └── vue.global.prod.min.js   # 【站点】Vue 3.5.22 本地副本
├── data/
│   ├── changelog.json          # 【站点】构建产物（原始 JSON，供外部复用）
│   └── changelog.js            # 【站点】同一份数据的 JS 包装，页面直接 <script> 加载
├── face/                       # 【站点】角色头像 <角色ID>.png
├── media/
│   ├── patches/                # 【站点】补丁调整长图原图
│   └── refs/                   # 【站点】玩家俗称表参考图
│
├── sources/                    # 【本地·已被 gitignore】原始参考资料
│   ├── readme/                 #   各版本 docx、主程序开发日志、历史留档
│   ├── config/                 #   游戏内 fighter.xml / assist.xml（阵营来源）、select.xml（分阶与角色清单）
│   └── zh-CN.json              #   中文语言文件（角色正式名来源）
│
└── tools/                      # 【非站点】整理数据的脚本与中间数据
    ├── build.py                #   主构建：sources + tools/data → data/
    ├── build_alias.py          #   生成别名映射表
    ├── build_screenshots.py    #   生成补丁截图转录文本
    └── data/
        ├── alias_map.json      #   别名 → 角色ID（含人工修正）
        ├── screenshots.json    #   3.8.8 起补丁长图的逐字转录
        ├── docx_shots.json     #   3.8.8 以前各版本 docx 内嵌补丁截图的逐字转录
        ├── patch_notes.json    #   3.8.0.1~3.8.1.1 等无 docx/长图的小补丁文字转录
        ├── mainlog.json        #   主程序开发日志解析结果
        └── release_dates.json  #   版本发布日与来源
```

### 收录口径

- **版本名以游戏内为准**：`3.8并阶改动.docx` 对应的是 **3.8.0**（不是「3.8」），
  构建时按 `VERSION_ORDER` 里的 `3.8.0` 归集，否则数据会挂在不存在的版本名下、前端版本列表里看不到。
- **不收录的条目**：
  - `游戏主程序BUG修复*n` 等主程序改动（属引擎层，另有「主程序日志」页）；
  - `旧XX文件包删除用不到的段数` 一类资源打包瘦身；
  - 带 `[真厉害]` 前缀的改动——那是「真厉害」改版的专属内容，角色（死门凯 / 幽香 / 孙悟空）不在 BVN 名单里。
- **3.8.0.1 / 3.8.0.2 / 3.8.0.3 / 3.8.1.1** 没有 docx 也没有补丁长图，内容来自官方补丁调整文字截图，
  逐条转录在 `patch_notes.json`，按角色 / 辅助归属后并入对应卡片。

### 关于原始资料与依赖

- **原始资料不公开**：`sources/` 被 `.gitignore` 排除，克隆仓库拿不到 docx / config / 语言文件。
  要让这些文件不进入 git 历史，仓库只保留站点成品与构建脚本；重建数据需自备 `sources/`。
- **依赖零外链**：Vue 已下载到 `assets/vendor/vue.global.prod.min.js`（3.5.22 全局生产构建）。
  页面不会向任何 CDN 发请求，离线、内网、Pages 均可直接跑。
  升级 Vue 时替换该文件即可，`index.html` 无需改动。

---

## 本地预览

站点用 `<script>` 加载数据，直接双击 `index.html` 也能看（无需服务器）。
若要更接近线上环境：

```bash
python -m http.server 8899
# 打开 http://127.0.0.1:8899/index.html
```

## 重新构建数据

需要 Python 3.9+、`python-docx`，以及**本地自备的 `sources/` 目录**（不在仓库里）：

```bash
pip install python-docx
python tools/build_alias.py    # sources/zh-CN.json → tools/data/alias_map.json
python tools/build.py          # sources/ + tools/data/ → data/changelog.{json,js}
```

构建完刷新页面即可。`data/` 是产物，可以随时删掉重建。
`sources/` 缺失时脚本会直接报错退出，并提示成品 `data/changelog.js` 已在仓库中、
只更新站点内容时无需重新构建。

## 维护指引

| 要做什么 | 改哪里 |
|---|---|
| 新增一个版本的改动 | 把 docx 放进 `sources/readme/`，在 `tools/build.py` 的 `DOCX_MAP` 加一行，并在 `VERSION_ORDER` 里加上版本号 |
| 只有补丁文字截图、没有 docx / 长图 | 在 `tools/data/patch_notes.json` 里按「版本 → 分组 → 角色 → 条目」转录，构建会自动并入（`screenshots.json` / `docx_shots.json` 同结构） |
| 补一个版本的发布日 | `tools/data/release_dates.json`：`"3.8.5.10": {"date": "2025-06-XX", "confidence": "high", "source": "B站补丁发布动态"}` |
| 版本存在但暂无资料 | 保留在 `VERSION_ORDER` 中，并写进 `PENDING_VERSIONS`，页面会显示「待补充 / 暂无改动记录」 |
| 角色别名归并错了 | `tools/build_alias.py` 里的 `ALIASES` 字典 |
| 辅助位角色对不上 | 辅助段落的解析必须落在 `config/assist.xml` 的节点上（如辅助蝎=人傀儡·绯流琥、辅助史塔克=归刃）。简称写进 `build_alias.py` 的 `ASSIST_NICK`，主辅不对应关系写进 `ASSIST_FROM_MAIN`；`build.py` 末尾会校验并报警 |
| 文档标题写错角色 / 层级 | 在 `build.py` 的 `ENTRY_OVERRIDE` 里按「版本+父级+标题」定向修正 |
| 角色不属于任何阵营或归错 | 由 `sources/config/*.xml` 的 `comic_type` 决定（0=死神 / 1=火影 / 其他），不要手写 |
| 角色分阶不对 | `sources/config/select.xml` 里的行注释（低阶 / 中阶 / 高阶 / 黑屋隐藏阶）就是唯一依据，改注释即可 |
| 有角色没有卡片 | 构建会按 `select.xml` 自动补 0 改动空卡；若仍缺，说明该 id 不在 `select.xml` 也不在历史改动里 |
| 文档提到的角色不该有卡 / 主辅归类错 | `select.xml` 才是角色是否存在的依据；`fighter.xml` 里有 70+ 个被注释掉的停放角色，不构成在役角色。构建会按 select 清单过滤，并在 `REMOVED_MAIN_KEEP` 白名单里登记需保留历史的已移除角色 |

### 日期口径

- **发布日**：官方渠道（B 站补丁发布动态、官方腾讯频道、官方视频简介等）查证的日期，页面标「发布」。未查到确切日期则标「发布日未定」。
- **提交日**：`主程序开发日志.txt` 里的日期，只是代码最后提交时间，页面标「日志」，仅作参考。
- 两者不等价，不要把提交日当发布日。
- **展示范围**：角色档案页与按版本页统一只显示发布日；只有「主程序日志」页同时并列显示日志日与发布日。

## 部署到 GitHub Pages

仓库已初始化并推送到 `https://github.com/diazynez/changelog.git`（分支 `main`）。
日常更新只需：

```bash
git add -A
git commit -m "chore: 更新数据"
git push
```

仓库 **Settings → Pages** 设置一次即可：

- Source 选 **Deploy from a branch**
- Branch 选 **main**，目录选 **/(root)**
- 保存后等 1 分钟左右，访问 `https://<你的账号>.github.io/<仓库名>/`

站点全部使用相对路径，放在仓库根目录即可直接访问，无需任何构建步骤，也不依赖任何 CDN。
`.nojekyll` 已就位，避免 Jekyll 处理中文文件名。
`sources/` 不会被发布（已 gitignore），`tools/` 会随仓库公开但只是脚本，不含原始资料。

## 待补充

- `3.8.5.10`：改动已从 `3.8.5.8更新内容.docx` 的内嵌截图补齐，仅缺发布日。
- `3.8.5.1`、`3.8.4.4`：暂未查到确切发布日。
- `3.8.4.5` 辅助第 1 条「飞雷神互瞬回旋之术：移除此辅助」：该辅助换皮后成为「天手力」（宇智波·佐助 天手力），原节点已从 `assist.xml` 移除，因此不单独建卡。
