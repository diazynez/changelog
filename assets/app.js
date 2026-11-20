/* ==========================================================================
   死神VS火影 竞技版 · 角色改动档案 —— 应用逻辑（Vue 3）
   数据：data/changelog.js（由 tools/build.py 生成）
   ========================================================================== */
(function () {
  'use strict';

  const D = window.CHANGELOG_DATA;
  if (!D) {
    document.getElementById('app').innerHTML =
      '<div style="padding:60px;text-align:center;font-family:sans-serif;color:#666">' +
      '数据文件未加载：请确认 <code>data/changelog.js</code> 存在（运行 <code>python tools/build.py</code> 生成）。</div>';
    return;
  }

  const CAMP_LABEL = { bleach: '死神', naruto: '火影', other: '其他' };
  const SEC_LABEL = { add: '新增', fix: '修复', change: '更改', remove: '删除', note: '贴士' };
  const TIER_LABEL = { low: '低阶', mid: '中阶', high: '高阶', god: '神阶' };

  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const rxCache = {};
  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // 预计算：每个版本是否真的有改动记录
  const versionHasData = {};
  D.characters.forEach((c) => {
    Object.keys(c.versions).forEach((v) => { versionHasData[v] = true; });
  });

  const app = Vue.createApp({
    data() {
      // markRaw：这些数据只读，跳过深层响应式代理，加快首屏
      const raw = Vue.markRaw;
      return {
        // 静态数据
        versions: raw(D.versions),
        pendingVersions: raw(D.pendingVersions || {}),
        rel: raw(D.releaseDates || {}),
        mainlog: raw(D.mainlog || []),
        images: raw(D.allImages || []),
        refImages: raw(D.refImages || []),
        unmatched: raw(D.unmatched || []),
        stats: raw(D.stats || {}),
        all: raw(D.characters),
        generatedFrom: D.generatedFrom || '',

        // 界面状态
        view: 'chars',
        q: '',
        camp: 'all',
        type: 'all',
        tier: 'all',
        sortBy: 'count',
        ver: 'all',
        hideEmpty: false,
        selected: null,
        zoom: null,
        openVer: D.versions[0] || null,
        openLog: (D.mainlog && D.mainlog[0]) ? D.mainlog[0].version : null,
        closedGroups: {},
        broken: {},
        _silent: false,

        tabs: [
          { k: 'chars', label: '角色档案' },
          { k: 'versions', label: '按版本' },
          { k: 'supp', label: '主程序日志' }
        ],
        campChips: [
          { k: 'all', label: '全部' },
          { k: 'bleach', label: '死神' },
          { k: 'naruto', label: '火影忍者' },
          { k: 'other', label: '其他' }
        ],
        typeChips: [
          { k: 'all', label: '全部' },
          { k: 'main', label: '主人物' },
          { k: 'assist', label: '辅助' }
        ],
        // 分阶只对主人物有效；辅助不参与分阶
        tierChips: [
          { k: 'all', label: '全部' },
          { k: 'low', label: '低阶' },
          { k: 'mid', label: '中阶' },
          { k: 'high', label: '高阶' },
          { k: 'god', label: '神阶' }
        ],
        sortOptions: [
          { k: 'count', label: '按改动条数' },
          { k: 'recent', label: '按最近改动' },
          { k: 'order', label: '按选人顺序' },
          { k: 'name', label: '按名称' }
        ]
      };
    },

    computed: {
      heroStats() {
        const s = this.stats;
        return [
          [s.characters || 0, '个角色 / 形态'],
          [s.totalChangeEntries || 0, '条改动记录'],
          [s.versionCount || 0, '个版本'],
          [s.releaseDatesFound || 0, '个查证的发布日']
        ];
      },

      dateNote() {
        const hi = Object.entries(this.rel).filter(([k, v]) => v.releaseDate && v.confidence === 'high');
        const samples = hi.slice(0, 5).map(([v, r]) => `${esc(v)} → ${esc(r.releaseDate)}`).join('、');
        const pending = Object.keys(this.pendingVersions);
        return '<b>关于日期：</b>主程序日志里的日期只代表最后一次提交代码，并非版本发布时间。' +
          `此处列出官方渠道查证的 <b>${hi.length}</b> 个确切发布日` +
          (samples ? `，例如 ${samples}` : '') +
          '；其余版本或未查到确切日期的均在详情中标注「提交日」。' +
          (pending.length
            ? `另有 <b>${pending.join('、')}</b> 已确认存在但暂无改动记录，等待补充。`
            : '');
      },

      hasQuery() {
        return this.q.trim().length > 0;
      },

      /** 版本名 → 新旧名次（0 = 最新）。versions 已按新→旧排好 */
      verRank() {
        const m = {};
        this.versions.forEach((v, i) => { m[v] = i; });
        return m;
      },

      filteredChars() {
        const q = this.normQ();
        return this.sortChars(this.all.filter((c) => this.matchBase(c, q)));
      },

      groups() {
        const q = this.normQ();
        const list = this.hideEmpty
          ? this.versions.filter((v) => versionHasData[v] || this.pendingVersions[v])
          : this.versions;
        return list.map((v) => {
          const chars = this.all.filter((c) => c.versions[v] && this.matchBase(c, q));
          return {
            v: v,
            chars: chars,
            count: chars.reduce((a, c) => a + c.versions[v].length, 0),
            rel: this.rel[v] || {},
            pending: !!this.pendingVersions[v],
            pendingNote: this.pendingVersions[v] || ''
          };
        });
      },

      footerText() {
        const s = this.stats;
        return `数据来源：${this.generatedFrom} · 共 ${s.characters} 个角色 / ${s.totalChangeEntries} 条改动 · 发布日以官方渠道查证为准`;
      }
    },

    mounted() {
      this.applyHash();

      window.addEventListener('hashchange', () => this.applyHash());

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.selected = null;
          this.zoom = null;
        }
      });
    },

    watch: {
      view(v) {
        if (this._silent) return;
        history.replaceState(null, '', v === 'chars' ? location.pathname + location.search : '#' + v);
      },
      // 辅助不分阶：切到辅助时清掉分阶条件，避免筛出空列表
      type(v) {
        if (v === 'assist' && this.tier !== 'all') this.tier = 'all';
      }
    },

    methods: {
      /** 支持 #versions / #supp / #char=<id> 深链 */
      applyHash() {
        const h = decodeURIComponent(location.hash.replace(/^#/, ''));
        this._silent = true;
        if (h === 'versions' || h === 'supp' || h === 'chars') {
          this.view = h;
          this.selected = null;
        } else if (h.indexOf('char=') === 0) {
          const id = h.slice(5);
          const c = this.all.find((x) => x.id === id);
          if (c) {
            this.view = 'chars';
            this.open(c);
          }
        }
        this._silent = false;
      },

      normQ() {
        return this.q.trim().toLowerCase();
      },

      /**
       * 手风琴锚定：切换展开项后，把被点击的头部固定在屏幕原位置。
       * 同时只展开一项，收起上方内容会让页面高度骤减，若只改状态不补偿滚动，
       * 新展开的块会「跳」到视口外（上方内容越多跳得越远），用户得重新找。
       */
      toggleVer(v, ev) {
        this.accToggle('openVer', v, ev.currentTarget);
      },

      toggleLog(v, ev) {
        this.accToggle('openLog', v, ev.currentTarget);
      },

      accToggle(prop, key, head) {
        const before = head.getBoundingClientRect().top;
        this[prop] = this[prop] === key ? null : key;
        this.$nextTick(() => {
          const dy = head.getBoundingClientRect().top - before;
          if (Math.abs(dy) < 1) return; // 位置没变（展开最上方一项）就不用补偿
          const root = document.documentElement;
          const prev = root.style.scrollBehavior;
          root.style.scrollBehavior = 'auto'; // 全局是 smooth，补偿必须瞬时完成，否则会被动画拖走
          window.scrollBy({ top: dy, left: 0, behavior: 'instant' });
          root.style.scrollBehavior = prev;
        });
      },

      matchBase(c, q) {
        if (this.camp !== 'all' && (c.camp || 'other') !== this.camp) return false;
        if (this.type !== 'all' && (c.isAssist ? 'assist' : 'main') !== this.type) return false;
        // 分阶只筛主人物：辅助不参与分阶，选中具体阶时自动排除
        if (this.tier !== 'all') {
          if (c.isAssist) return false;
          if (c.tier !== this.tier) return false;
        }
        if (this.ver !== 'all' && !(c.versions && c.versions[this.ver])) return false;
        if (!q) return true;
        let t = c.name + ' ' + (c.aliases || []).join(' ');
        for (const v in c.versions) t += ' ' + c.versions[v].join(' ');
        return t.toLowerCase().indexOf(q) !== -1;
      },

      /** 该角色最近一次有改动的版本（按版本号新旧判定，非字符串比较） */
      latestVer(c) {
        const rank = this.verRank;
        let best = null, bi = Infinity;
        for (const v in c.versions) {
          const i = rank[v];
          if (i != null && i < bi) { bi = i; best = v; }
        }
        return best;
      },

      /** 排序：无论怎么排，辅助始终沉底到角色之后 */
      sortChars(list) {
        const by = this.sortBy;
        const nameOf = (c) => c.nameBase || c.name;
        const ord = (c) => (c.order == null ? 999 : c.order); // 注意 0 是合法序号，不能用 || 兜底
        const rank = this.verRank;
        // 最近改动：取最新版本的新旧名次，越小越近；无改动记录者排到最后
        const recent = (c) => {
          let best = Infinity;
          for (const v in c.versions) {
            const i = rank[v];
            if (i != null && i < best) best = i;
          }
          return best;
        };
        return list.slice().sort((a, b) => {
          if (a.isAssist !== b.isAssist) return a.isAssist ? 1 : -1;
          if (by === 'order') {
            const d = ord(a) - ord(b);
            return d || nameOf(a).localeCompare(nameOf(b), 'zh-Hans-CN');
          }
          if (by === 'name') {
            return nameOf(a).localeCompare(nameOf(b), 'zh-Hans-CN') || a.name.localeCompare(b.name, 'zh-Hans-CN');
          }
          if (by === 'recent') {
            const d = recent(a) - recent(b);
            return d || b.changeCount - a.changeCount || ord(a) - ord(b);
          }
          return b.changeCount - a.changeCount || ord(a) - ord(b);
        });
      },

      tierLabel(k) {
        return TIER_LABEL[k] || '';
      },

      campLabel(k) {
        return CAMP_LABEL[k] || '其他';
      },

      secLabel(k) {
        return SEC_LABEL[k] || k;
      },

      /** 关键词高亮（返回安全 HTML） */
      hl(s) {
        const safe = esc(s);
        const q = this.q.trim();
        if (!q) return safe;
        try {
          const key = q.toLowerCase();
          const re = rxCache[key] || (rxCache[key] = new RegExp('(' + escapeRe(q) + ')', 'gi'));
          return safe.replace(re, '<mark style="background:#ffe08a">$1</mark>');
        } catch (e) {
          return safe;
        }
      },

      /** 详情条目：拆出遗留的〔形态〕前缀 */
      itemParts(it) {
        const m = String(it).match(/^〔(.+?)〕/);
        return m ? { form: m[1], text: String(it).slice(m[0].length) } : { form: '', text: it };
      },

      previewText(c, v) {
        const items = c.versions[v] || [];
        return items.slice(0, 2).join('；') + (items.length > 2 ? ' …' : '');
      },

      logCount(m) {
        return Object.values(m.sections || {}).reduce((a, b) => a + (b ? b.length : 0), 0);
      },

      isPending(v) {
        return !!this.pendingVersions[v];
      },

      open(c) {
        this.selected = c;
        const closed = {};
        Object.keys(c.versions).forEach((v, i) => {
          if (i > 2) closed[c.id + v] = true;
        });
        this.closedGroups = closed;
      }
    }
  });

  app.mount('#app');
})();
