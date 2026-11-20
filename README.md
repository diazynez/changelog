# 死神VS火影 竞技版 · 角色改动档案

以**角色**为核心的版本改动档案站点。把各版本《更新内容 / 并阶改动》文档与官方补丁长图里的调整，
按角色聚合到一张卡片上，并标注版本发布日；主程序开发日志作为补充。

- 站点：`index.html`（Vue 3，通过 Cloudflare CDN 加载，无需打包）
- 数据：`data/changelog.js`（构建产物）
- 当前规模：135 个角色 / 形态、2235 条改动、33 个版本、30 个查证到的发布日

---

## 目录结构

站点文件与源数据、工具严格分开，只有下面「站点」部分会对外发布。

```
.
├── index.html                  # 【站点】唯一页面
├── assets/
│   ├── style.css               # 【站点】样式
│   └── app.js                  # 【站点】Vue 应用逻辑
├── data/
│   ├── changelog.json          # 【站点】构建产物（原始 JSON，供外部复用）
│   └── changelog.js            # 【站点】同一份数据的 JS 包装，页面直接 <script> 加载
├── face/                       # 【站点】角色头像 <角色ID>.png
├── media/
│   ├── patches/                # 【站点】补丁调整长图原图
│   └── refs/                   # 【站点】玩家俗称表参考图
│
├── sources/                    # 【非站点】原始参考资料，不参与构建产物
│   ├── readme/                 #   各版本 docx、主程序开发日志、历史留档
│   ├── config/                 #   游戏内 fighter.xml / assist.xml（阵营来源）
│   └── zh-CN.json              #   中文语言文件（角色正式名来源）
│
└── tools/                      # 【非站点】整理数据的脚本与中间数据
    ├── build.py                #   主构建：sources + tools/data → data/
    ├── build_alias.py          #   生成别名映射表
    ├── build_screenshots.py    #   生成补丁截图转录文本
    └── data/
        ├── alias_map.json      #   别名 → 角色ID（含人工修正）
        ├── screenshots.json    #   补丁长图的逐字转录
        ├── mainlog.json        #   主程序开发日志解析结果
        └── release_dates.json  #   版本发布日与来源
```

---

## 本地预览

站点用 `<script>` 加载数据，直接双击 `index.html` 也能看（无需服务器）。
若要更接近线上环境：

```bash
python -m http.server 8899
# 打开 http://127.0.0.1:8899/index.html
```

## 重新构建数据

需要 Python 3.9+ 与 `python-docx`：

```bash
pip install python-docx
python tools/build_alias.py    # sources/zh-CN.json → tools/data/alias_map.json
python tools/build.py          # sources/ + tools/data/ → data/changelog.{json,js}
```

构建完刷新页面即可。`data/` 是产物，可以随时删掉重建。

## 维护指引

| 要做什么 | 改哪里 |
|---|---|
| 新增一个版本的改动 | 把 docx 放进 `sources/readme/`，在 `tools/build.py` 的 `DOCX_MAP` 加一行，并在 `VERSION_ORDER` 里加上版本号 |
| 补一个版本的发布日 | `tools/data/release_dates.json`：`"3.8.5.10": {"date": "2025-06-XX", "confidence": "high", "source": "B站补丁发布动态"}` |
| 版本存在但暂无资料 | 保留在 `VERSION_ORDER` 中，并写进 `PENDING_VERSIONS`，页面会显示「待补充 / 暂无改动记录」 |
| 角色别名归并错了 | `tools/build_alias.py` 里的 `ALIASES` 字典 |
| 角色不属于任何阵营或归错 | 由 `sources/config/*.xml` 的 `comic_type` 决定（0=死神 / 1=火影 / 其他），不要手写 |

### 日期口径

- **发布日**：官方渠道（B 站补丁发布动态、官方腾讯频道、官方视频简介等）查证的日期，页面标「发布」。
- **提交日**：`主程序开发日志.txt` 里的日期，只是代码最后提交时间，页面标「日志」，仅作参考。
- 两者不等价，不要把提交日当发布日。

## 部署到 GitHub Pages

```bash
git init
git add .
git commit -m "init: changelog site"
git branch -M main
git remote add origin https://github.com/<你的账号>/<仓库名>.git
git push -u origin main
```

然后在仓库 **Settings → Pages**：

- Source 选 **Deploy from a branch**
- Branch 选 **main**，目录选 **/(root)**
- 保存后等 1 分钟左右，访问 `https://<你的账号>.github.io/<仓库名>/`

站点全部使用相对路径，放在仓库根目录即可直接访问，无需任何构建步骤。
仓库内的 `sources/`、`tools/` 不会影响页面运行（只是同样会被镜像发布，介意可以改成 `/docs` 目录发布）。

## 待补充

- `3.8.5.10`：确认存在的版本，暂无改动记录与发布日期。
- `3.8.5.1`、`3.8.4.4`：暂未查到确切发布日。
