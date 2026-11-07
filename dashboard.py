# -*- coding: utf-8 -*-
"""แดชบอร์ดแสดงผลวิเคราะห์ (HTML + CSS ล้วน ไม่ใช้ JavaScript/ไลบรารีกราฟ)

ทุกฟังก์ชันคืนสตริง HTML บรรทัดเดียวต่อบล็อก (ไม่มีบรรทัดว่าง) เพื่อให้ st.markdown(unsafe_allow_html=True) ไม่ตีความเป็น Markdown
"""
import html as _html

import football_quant_v58 as q

CSS = """
.fq { --acc:#14b8a6; --acc2:#6366f1; --up:#34d399; --down:#f87171; --warn:#fbbf24; --mut:#8fa3c0; --txt:#e6edf7;
      --line:rgba(255,255,255,.09); --panel:rgba(255,255,255,.045); font-variant-numeric:tabular-nums; color:var(--txt); }
.fq * { box-sizing:border-box; }
.fq-grid { display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); gap:12px; margin:12px 0; }
.fq-c2{grid-column:span 2}.fq-c3{grid-column:span 3}.fq-c4{grid-column:span 4}.fq-c5{grid-column:span 5}
.fq-c6{grid-column:span 6}.fq-c7{grid-column:span 7}.fq-c8{grid-column:span 8}.fq-c12{grid-column:span 12}
.fq-card { background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 16px; min-width:0; }
.fq-h { display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:.7rem; letter-spacing:.08em;
        text-transform:uppercase; color:var(--mut); font-weight:600; margin-bottom:10px; }
.fq-sec { display:flex; align-items:baseline; gap:10px; margin:22px 2px 4px; font-weight:700; font-size:1.02rem; }
.fq-sec small { color:var(--mut); font-weight:400; font-size:.78rem; }
.fq-sec::after { content:""; flex:1; height:1px; background:var(--line); }
.fq-mut { color:var(--mut); } .fq-up { color:var(--up); } .fq-down { color:var(--down); } .fq-warn { color:var(--warn); }
.fq-small { font-size:.78rem; }
.fq-chip { display:inline-flex; align-items:center; gap:4px; font-size:.74rem; padding:2px 10px; border-radius:99px;
           background:rgba(99,102,241,.16); color:#c7d2fe; border:1px solid rgba(165,180,252,.25); white-space:nowrap; }
.fq-chip.ok { background:rgba(52,211,153,.14); color:#6ee7b7; border-color:rgba(110,231,183,.3); }
.fq-chip.bad { background:rgba(248,113,113,.14); color:#fca5a5; border-color:rgba(252,165,165,.3); }
.fq-chip.warn { background:rgba(251,191,36,.12); color:#fde68a; border-color:rgba(253,224,71,.3); }
.fq-chip.off { background:rgba(255,255,255,.05); color:var(--mut); border-color:var(--line); }
.fq-chip.acc { background:rgba(20,184,166,.16); color:#5eead4; border-color:rgba(94,234,212,.3); }
.fq-chips { display:flex; flex-wrap:wrap; gap:6px; }

/* KPI */
.fq-kpi { display:flex; flex-direction:column; justify-content:space-between; min-height:132px; }
.fq-kpi .big { font-size:1.55rem; font-weight:700; line-height:1.18; margin:2px 0 6px; }
.fq-kpi .num { font-size:1.9rem; font-weight:700; line-height:1.1; }
.fq-hero { background:linear-gradient(135deg, rgba(20,184,166,.22), rgba(99,102,241,.2)); border-color:rgba(94,234,212,.35); }
.fq-hero.low { background:linear-gradient(135deg, rgba(100,116,139,.28), rgba(71,85,105,.22)); border-color:rgba(148,163,184,.3); }
.fq-donut { width:96px; height:96px; border-radius:50%; margin:0 auto;
            background:conic-gradient(var(--c,#14b8a6) calc(var(--p,0)*1%), rgba(255,255,255,.1) 0); display:grid; place-items:center; }
.fq-donut > div { width:74px; height:74px; border-radius:50%; background:#0e182b; display:flex; flex-direction:column;
                  align-items:center; justify-content:center; font-weight:700; font-size:1.2rem; line-height:1.1; }
.fq-donut small { font-weight:400; font-size:.64rem; color:var(--mut); }
.fq-meter { height:6px; border-radius:99px; background:rgba(255,255,255,.1); overflow:hidden; margin-top:8px; }
.fq-meter > i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,var(--acc),#22d3ee); }

/* ทีม */
.fq-teams { display:grid; grid-template-columns:1fr auto 1fr; gap:10px; align-items:start; text-align:center; }
.fq-team .nm { font-size:1.12rem; font-weight:700; margin:6px 0 2px; overflow-wrap:anywhere; }
.fq-team .rk { display:inline-block; font-size:.72rem; padding:1px 9px; border-radius:99px; background:rgba(255,255,255,.08); }
.fq-vs { align-self:center; font-weight:700; color:#64748b; padding-top:14px; }
.fq-dots { margin:6px 0 4px; } .fq-dot { display:inline-flex; width:21px; height:21px; border-radius:50%; align-items:center; justify-content:center;
           font-size:.66rem; font-weight:700; margin:0 2px; color:#0b1220; }
.fq-dot.w{background:#34d399}.fq-dot.d{background:#fbbf24}.fq-dot.l{background:#f87171}
.fq-kv { display:flex; justify-content:center; gap:14px; flex-wrap:wrap; font-size:.76rem; color:var(--mut); }
.fq-kv b { color:var(--txt); font-weight:600; }
.fq-h2h { display:flex; gap:6px; flex-wrap:wrap; justify-content:center; margin-top:6px; }
.fq-h2h span { font-size:.78rem; font-weight:600; padding:3px 10px; border-radius:8px; border:1px solid var(--line); }
.fq-h2h .w{color:#6ee7b7;background:rgba(52,211,153,.1)}.fq-h2h .d{color:#fde68a;background:rgba(251,191,36,.1)}.fq-h2h .l{color:#fca5a5;background:rgba(248,113,113,.1)}

/* กราฟแท่ง */
.fq-stack { display:flex; height:30px; border-radius:8px; overflow:hidden; font-size:.72rem; font-weight:600; }
.fq-stack.thin { height:8px; margin-top:5px; opacity:.55; }
.fq-stack > div { display:flex; align-items:center; justify-content:center; white-space:nowrap; overflow:hidden; color:#04201d; }
.fq-stack .h{background:#2dd4bf}.fq-stack .d{background:#94a3b8}.fq-stack .a{background:#818cf8;color:#0b1020}
.fq-cols3 { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:10px; text-align:center; }
.fq-cols3 .o { font-size:1.2rem; font-weight:700; } .fq-cols3 .s { font-size:.7rem; color:var(--mut); }
.fq-line { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.fq-line .t { font-size:.68rem; color:var(--mut); } .fq-line .v { font-size:1.15rem; font-weight:700; }
.fq-line .b { padding:4px 10px; border-radius:10px; background:rgba(255,255,255,.06); border:1px solid var(--line); }
.fq-line .b.cur { background:rgba(20,184,166,.16); border-color:rgba(94,234,212,.4); }
.fq-bar { display:grid; grid-template-columns:minmax(0,1.45fr) 1.7fr auto; gap:8px; align-items:center; margin:7px 0; font-size:.82rem; }
.fq-bar .tr { height:9px; border-radius:99px; background:rgba(255,255,255,.09); overflow:hidden; }
.fq-bar .tr > i { display:block; height:100%; border-radius:99px; background:linear-gradient(90deg,#14b8a6,#22d3ee); }
.fq-bar .tr > i.alt { background:linear-gradient(90deg,#6366f1,#a78bfa); }
.fq-bar .n { text-align:right; font-weight:600; white-space:nowrap; }
.fq-bar .nm { line-height:1.25; font-size:.78rem; overflow-wrap:anywhere; }

/* สกอร์บอร์ดฝั่งตรงข้าม */
.fq-div { display:grid; grid-template-columns:116px 1fr 1fr 116px; gap:8px; align-items:center; margin:12px 0; }
.fq-div .side { min-width:0; line-height:1.25; }
.fq-div .side.r { text-align:right; }
.fq-div .side .nm { display:block; color:var(--mut); font-size:.72rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.fq-div .side b { font-size:1.08rem; font-weight:700; }
.fq-div .side.win b { color:var(--acc); }
.fq-div .side .tg { font-size:.68rem; color:var(--down); margin-left:4px; font-weight:600; }
.fq-div .half { height:16px; background:rgba(255,255,255,.06); display:flex; }
.fq-div .half.l { justify-content:flex-end; border-radius:8px 0 0 8px; }
.fq-div .half.r { border-radius:0 8px 8px 0; }
.fq-div .half i { display:block; height:100%; background:#475569; }
.fq-div .half.l i { border-radius:8px 0 0 8px; } .fq-div .half.r i { border-radius:0 8px 8px 0; }
.fq-div .half.win i { background:linear-gradient(90deg,#14b8a6,#22d3ee); }
.fq-div .half.l.win i { background:linear-gradient(270deg,#14b8a6,#22d3ee); }
.fq-div .half.ban i { background:repeating-linear-gradient(45deg,#475569,#475569 4px,#334155 4px,#334155 8px); opacity:.5; }

/* ตารางสัญญาณ */
.fq-tbl { width:100%; }
.fq-row { display:grid; grid-template-columns:minmax(0,2.3fr) minmax(0,1.5fr) minmax(0,1.6fr) 74px; gap:10px; align-items:center;
          padding:9px 0; border-bottom:1px solid var(--line); font-size:.82rem; }
.fq-row:last-child { border-bottom:none; } .fq-row.head { color:var(--mut); font-size:.68rem; letter-spacing:.06em; text-transform:uppercase; padding-top:0; }
.fq-row .rn { min-width:0; } .fq-row .rn b { display:block; font-weight:600; overflow-wrap:anywhere; }
.fq-row .rn small { color:var(--mut); display:block; line-height:1.35; margin-top:2px; }
.fq-row .sc { display:flex; align-items:center; gap:8px; }
.fq-row .sc .tr { flex:1; height:7px; border-radius:99px; background:rgba(255,255,255,.09); overflow:hidden; }
.fq-row .sc .tr > i { display:block; height:100%; background:linear-gradient(90deg,#14b8a6,#22d3ee); border-radius:99px; }
.fq-row .sc b { min-width:44px; text-align:right; }
.fq-ev { margin:6px 0 0; padding-left:18px; color:#b8c7df; font-size:.84rem; line-height:1.6; }
.fq-check { display:grid; grid-template-columns:22px 1fr; gap:6px; font-size:.82rem; margin:6px 0; line-height:1.4; }

/* สถิติ */
.fq-pl { display:flex; align-items:stretch; gap:3px; height:130px; margin-top:6px; }
.fq-pl > div { flex:1; max-width:34px; position:relative; min-width:3px; }
.fq-pl .mid { position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(255,255,255,.18); }
.fq-pl i { position:absolute; left:10%; right:10%; border-radius:3px; }
.fq-pl i.p { bottom:50%; background:#34d399; } .fq-pl i.n { top:50%; background:#f87171; }
.fq-w { display:grid; grid-template-columns:minmax(0,1.6fr) 2fr 58px; gap:8px; align-items:center; margin:7px 0; font-size:.8rem; }
.fq-w .tr { height:8px; border-radius:99px; background:rgba(255,255,255,.09); position:relative; }
.fq-w .tr > i { display:block; height:100%; border-radius:99px; }
.fq-w .tr > u { position:absolute; top:-3px; width:2px; height:14px; background:rgba(255,255,255,.55); }
.fq-w .nm { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.fq-w .nm small { color:var(--mut); }
.fq-hist { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:10px; padding:9px 0; border-bottom:1px solid var(--line); font-size:.84rem; }
.fq-hist:last-child { border-bottom:none; } .fq-hist small { color:var(--mut); display:block; }
.fq-empty { padding:22px; text-align:center; color:var(--mut); border:1px dashed var(--line); border-radius:14px; }

@media (max-width: 820px) {
  .fq-grid > * { grid-column:span 12 !important; }
  .fq-grid > .fq-m6 { grid-column:span 6 !important; }
  .fq-kpi { min-height:0; }
  .fq-row { grid-template-columns:minmax(0,1fr) minmax(0,1fr); }
  .fq-row .ch, .fq-row .wt { display:none; }
  .fq-row.head { display:none; }
  .fq-div { grid-template-columns:74px 1fr 1fr 74px; gap:6px; }
  .fq-sec { flex-wrap:wrap; row-gap:2px; } .fq-sec small { flex-basis:100%; } .fq-sec::after { display:none; }
}
"""


def e(x):
    return _html.escape(str(x))


def _card(title, body, cls="", tag=""):
    return (f'<div class="fq-card {cls}"><div class="fq-h"><span>{e(title)}</span>{tag}</div>{body}</div>')


def _chip(text, kind=""):
    return f'<span class="fq-chip {kind}">{e(text)}</span>'


def _arrow(v, eps=1e-9):
    return ("fq-up", "▲") if v > eps else (("fq-down", "▼") if v < -eps else ("fq-mut", "■"))


def _market_th(mk, f):
    return {"HDP_HOME": f"แฮนดิแคป {f['home']}", "HDP_AWAY": f"แฮนดิแคป {f['away']}", "OU_OVER": "สูง (Over)",
            "OU_UNDER": "ต่ำ (Under)", "X12_HOME": f"1X2 {f['home']}", "X12_AWAY": f"1X2 {f['away']}"}.get(mk, mk)


def _dots(seq):
    cls = {"W": "w", "D": "d", "L": "l"}
    return "".join(f'<span class="fq-dot {cls.get(c, "d")}">{e(c)}</span>' for c in str(seq or "").upper())


# ------------------------------------------------------------------ ส่วนบน: KPI + แมตช์
def kpi_and_match(res):
    m, f, pick = res["m"], res["f"], res["pick"]
    low = pick["tier"] == "ต่ำ"
    chips = [_chip(f"ระดับ{pick['tier']}", "off" if low else "acc")]
    if pick.get("verify_fail"):
        chips.append(_chip("เหย้า/เยือนไม่ผ่าน", "bad"))
    if pick.get("move_only"):
        chips.append(_chip("มาจากการไหลของราคาล้วน", "warn"))
    for v in pick.get("veto", []):
        chips.append(_chip("แบน " + _market_th(v, f), "bad"))
    ru = [r for r in pick.get("runner_up", []) if r[1] > 0.05][:1]
    runner = (f'<div class="fq-small fq-mut" style="margin-top:6px">ทางเลือกรอง: {e(_market_th(ru[0][0], f))} '
              f'({ru[0][1]:.2f})</div>') if ru else ""
    c1 = (f'<div class="fq-card fq-c5 fq-kpi fq-hero{" low" if low else ""}"><div class="fq-h"><span>สัญญาณฟันธงเดี่ยว</span>'
          f'<span class="fq-chip off">ใช้ราคาปัจจุบัน</span></div><div><div class="big">{e(pick["label"])}</div>'
          f'<div class="fq-chips">{"".join(chips)}</div>{runner}</div></div>')
    conf = pick["confidence"]
    col = "#94a3b8" if low else "#14b8a6"
    c2 = _card("ความมั่นใจเชิงสัญญาณ",
               f'<div class="fq-donut" style="--p:{conf:.0f};--c:{col}"><div>{conf:.0f}%<small>ยังไม่สอบเทียบ</small></div></div>', "fq-c3 fq-m6 fq-kpi")
    c3 = _card("คะแนนสัญญาณ",
               f'<div><div class="num">{pick["strength"]:.2f}</div><div class="fq-small fq-mut">เต็ม ~4.0 ขึ้นไป</div>'
               f'<div class="fq-meter"><i style="width:{min(pick["strength"] / 4 * 100, 100):.0f}%"></i></div></div>', "fq-c2 fq-m6 fq-kpi")
    ok_n = sum(1 for ok, _ in f.get("verify", []) if ok)
    tot = len(f.get("verify", []))
    vkind = "bad" if f.get("verify_fail") else "ok"
    c4 = _card("ตรวจเหย้า/เยือน",
               f'<div><div class="num {"fq-down" if f.get("verify_fail") else "fq-up"}">{ok_n}/{tot}</div>'
               f'<div class="fq-small fq-mut" style="margin-top:6px">{_chip("ผ่านทุกข้อ" if not f.get("verify_fail") else "มีข้อไม่ผ่าน", vkind)}</div></div>', "fq-c2 fq-kpi")
    kpis = '<div class="fq-grid">' + c1 + c2 + c3 + c4 + '</div>'

    # การ์ดแมตช์
    tv, fm, st = m.get("team_value") or {}, m.get("form") or {}, m.get("stats") or {}
    rs = m.get("research") or {}

    def team(side, name):
        rk = f.get("rank_home") if side == "home" else f.get("rank_away")
        x = fm.get(side) or {}
        role = "เจ้าบ้าน" if side == "home" else "ทีมเยือน"
        is_fav = (f["fav"] == side)
        kv = []
        if tv.get(side):
            kv.append(f'มูลค่า <b>{tv[side]:g}</b>')
        if x.get("win_rate") is not None:
            kv.append(f'ชนะ <b>{x["win_rate"]:g}%</b>')
        if x.get("gf") is not None and x.get("ga") is not None:
            kv.append(f'ได้/เสีย <b>{x["gf"]:g}/{x["ga"]:g}</b>')
        return (f'<div class="fq-team"><div class="fq-chips" style="justify-content:center">{_chip(role, "off")}'
                f'{_chip("ทีมต่อ", "acc") if is_fav else ""}</div>'
                f'<div class="nm">{e(name)}</div>'
                f'{"<span class=rk>อันดับ " + e(f"{rk:g}") + "</span>" if rk is not None else ""}'
                f'<div class="fq-dots">{_dots(x.get("seq"))}</div><div class="fq-kv">{"".join(f"<span>{k}</span>" for k in kv)}</div></div>')
    comp = rs.get("competition") or f.get("league") or ""
    h2h = ""
    items = []
    for hh in (m.get("h2h") or [])[:5]:
        same = hh.get("home_is_current_home", True)
        ch, ca = (hh["hg"], hh["ag"]) if same else (hh["ag"], hh["hg"])
        k = "w" if ch > ca else "l" if ch < ca else "d"
        items.append(f'<span class="{k}">{ch}–{ca}</span>')
    if items:
        h2h = (f'<div style="margin-top:12px;text-align:center"><div class="fq-small fq-mut">H2H {len(items)} นัดล่าสุด · '
               f'สกอร์มองจากเจ้าบ้านปัจจุบัน (เขียว = เจ้าบ้านชนะ)</div><div class="fq-h2h">{"".join(items)}</div></div>')
    match = ('<div class="fq-grid"><div class="fq-c12 fq-card"><div class="fq-h"><span>แมตช์</span>'
             f'<span class="fq-chip off">{e(comp)}</span></div><div class="fq-teams">{team("home", f["home"])}'
             f'<div class="fq-vs">VS</div>{team("away", f["away"])}</div>{h2h}</div></div>')
    return '<div class="fq">' + kpis + match + '</div>'


# ------------------------------------------------------------------ ส่วนล่าง: ตลาดราคา / คะแนน / Rule / บริบท
def _water_bar(label, w, drop=None, alt=False):
    width = max(4, min(100, (w - 0.6) / 0.7 * 100))
    d = ""
    if drop is not None and abs(drop) >= 0.005:
        cls = "fq-up" if drop > 0 else "fq-down"
        d = f' <span class="{cls} fq-small">{-drop:+.2f}</span>'
    return (f'<div class="fq-bar"><span class="nm">{e(label)}</span><div class="tr"><i class="{"alt" if alt else ""}" style="width:{width:.0f}%"></i></div>'
            f'<span class="n">{w:.2f}{d}</span></div>')


def analysis_body(res):
    m, f, contribs, pick = res["m"], res["f"], res["contribs"], res["pick"]
    out = ['<div class="fq">']

    # ---- ตลาดราคา
    out.append('<div class="fq-sec">ตลาดราคา <small>ราคาปัจจุบันเป็นหลัก · ราคาเปิดอ้างอิงการไหล · ค่าน้ำที่เปลี่ยน: ลด = เขียว (เงินเข้า) · ขึ้น = แดง</small></div><div class="fq-grid">')
    xo, xc = q.implied(f["x12_open"]), q.implied(f["x12_cur"])
    o, c = f["x12_open"], f["x12_cur"]
    segs = "".join(f'<div class="{k}" style="width:{p * 100:.1f}%">{lab} {p:.0%}</div>' for k, lab, p in
                   (("h", "เหย้า", xc[0]), ("d", "เสมอ", xc[1]), ("a", "เยือน", xc[2])))
    segs_o = "".join(f'<div class="{k}" style="width:{p * 100:.1f}%"></div>' for k, p in (("h", xo[0]), ("d", xo[1]), ("a", xo[2])))
    cells = ""
    for i, lab in enumerate(("เหย้า", "เสมอ", "เยือน")):
        dpp = (xc[i] - xo[i]) * 100
        cl, ar = _arrow(dpp, 0.3)
        cells += (f'<div><div class="s">{lab}</div><div class="o">{c[i]:.2f}</div>'
                  f'<div class="s">เปิด {o[i]:.2f}</div><div class="s {cl}">{ar} {dpp:+.1f}pp</div></div>')
    out.append(_card("1X2 · โอกาสโดยนัย", f'<div class="fq-stack">{segs}</div><div class="fq-stack thin">{segs_o}</div>'
                     f'<div class="fq-small fq-mut" style="margin-top:3px">แท่งบาง = ราคาเปิด</div><div class="fq-cols3">{cells}</div>', "fq-c4"))

    sh = f["hdp_shift_fav"]
    cl, ar = _arrow(sh)
    word = "แรงขึ้น" if sh > 0 else "อ่อนลง" if sh < 0 else "คงที่"
    hbody = (f'<div class="fq-line"><div class="b"><div class="t">เปิด</div><div class="v">{e(q.fmt_line(f["line_o"]))}</div></div>'
             f'<span class="{cl}">→</span><div class="b cur"><div class="t">ปัจจุบัน</div><div class="v">{e(q.fmt_line(f["line_c"]))}</div></div>'
             f'<span class="{cl} fq-small">{ar} ทีมต่อ{word} {sh:+g}</span></div>')
    hbody += _water_bar(f"{f['fav_name']} (ต่อ)", f["fav_water_c"], f["fav_drop"])
    hbody += _water_bar(f"{f['dog_name']} (รอง)", f["dog_water_c"], f["dog_drop"], alt=True)
    if abs(sh) >= 0.01:
        hbody += (f'<div class="fq-small fq-mut">ปรับตามเรตแล้ว: ทีมต่อ {-f["fav_drop_adj"]:+.2f} · ทีมรอง {-f["dog_drop_adj"]:+.2f}</div>')
    hbody += (f'<div class="fq-small fq-mut" style="margin-top:6px">พูล 1X2 ทีมต่อ {f["x12_pp"]:+.1f}pp · ความขัดแย้ง {f["conflict"]:.0%}</div>')
    out.append(_card("แฮนดิแคป", hbody, "fq-c4", _chip(f"ทีมต่อ {f['fav_name']}", "acc")))

    if f["has_ou"]:
        cl, ar = _arrow(f["ou_shift"])
        obody = (f'<div class="fq-line"><div class="b"><div class="t">เปิด</div><div class="v">{f["ou_o"]:g}</div></div>'
                 f'<span class="{cl}">→</span><div class="b cur"><div class="t">ปัจจุบัน</div><div class="v">{f["ou_c"]:g}</div></div>'
                 f'<span class="{cl} fq-small">{ar} {f["ou_shift"]:+g}</span></div>')
        obody += _water_bar("สูง (Over)", f["over_water_c"], f["over_drop"])
        obody += _water_bar("ต่ำ (Under)", f["under_water_c"], f["under_drop"], alt=True)
        if f.get("exp_total") is not None:
            obody += f'<div class="fq-small fq-mut" style="margin-top:6px">ประตูรวมคาดการณ์จากสถิติ {f["exp_total"]:.2f}</div>'
        out.append(_card("สูง / ต่ำ", obody, "fq-c4"))
    else:
        out.append(_card("สูง / ต่ำ", '<div class="fq-mut">ไม่มีข้อมูล</div>', "fq-c4"))
    out.append('</div>')

    # ---- สกอร์บอร์ด
    tot = {}
    for ct in contribs:
        tot[ct["market"]] = tot.get(ct["market"], 0.0) + ct["eff"]
    veto = set(pick.get("veto", []))
    mx = max([1.0] + [v for k, v in tot.items() if k not in veto])

    def drow(lab_l, lab_r, kl, kr):
        vl, vr = (0.0 if kl in veto else tot.get(kl, 0.0)), (0.0 if kr in veto else tot.get(kr, 0.0))
        win_l, win_r = pick["market"] == kl, pick["market"] == kr
        tl = '<span class="tg">แบน</span>' if kl in veto else ""
        tr_ = '<span class="tg">แบน</span>' if kr in veto else ""
        return (f'<div class="fq-div"><div class="side l{" win" if win_l else ""}"><span class="nm">{e(lab_l)}</span><b>{vl:.2f}{" ★" if win_l else ""}</b>{tl}</div>'
                f'<div class="half l{" win" if win_l else ""}{" ban" if kl in veto else ""}"><i style="width:{vl / mx * 100:.0f}%"></i></div>'
                f'<div class="half r{" win" if win_r else ""}{" ban" if kr in veto else ""}"><i style="width:{vr / mx * 100:.0f}%"></i></div>'
                f'<div class="side r{" win" if win_r else ""}"><span class="nm">{e(lab_r)}</span><b>{"★ " if win_r else ""}{vr:.2f}</b>{tr_}</div></div>')
    cap = lambda t: f'<div class="fq-small fq-mut" style="margin:14px 0 -4px;letter-spacing:.04em">{t}</div>'
    sb = cap("แฮนดิแคป") + drow(f["home"], f["away"], "HDP_HOME", "HDP_AWAY") + (cap("สูง / ต่ำ") + drow("สูง (Over)", "ต่ำ (Under)", "OU_OVER", "OU_UNDER") if f["has_ou"] else "")
    out.append('<div class="fq-sec">คะแนนสัญญาณต่อทางเลือก <small>คะแนนรวมหลังคูณน้ำหนัก · ★ = ทางเลือกที่ฟันธง</small></div>')
    out.append(_card("แฮนดิแคป และ สูง/ต่ำ", sb, "fq-c12"))

    # ---- Rule ที่ทำงาน
    rows = ['<div class="fq-row head"><span>Rule</span><span class="ch">ทางเลือก</span><span>คะแนน</span><span class="wt">น้ำหนัก</span></div>']
    top = sorted(contribs, key=lambda c: -c["eff"])[:8]
    cm = max([0.01] + [c["eff"] for c in top])
    for ct in top:
        rid = ct["rule"]
        basis = ("ไหลราคา", "warn") if rid in q.MOVEMENT_RULES else ("ปัจจุบัน/บริบท", "ok")
        w = ct["eff"] / ct["raw"] if ct["raw"] else 1.0
        rows.append(
            f'<div class="fq-row"><div class="rn"><b>{e(q.RULE_NAMES.get(rid, "Rule ที่เรียนรู้เอง"))} <span class="fq-mut fq-small">{e(rid)}</span></b>'
            f'<small>{e(ct["note"])}</small></div><div class="ch">{_chip(_market_th(ct["market"], f), "info")} {_chip(*basis)}</div>'
            f'<div class="sc"><div class="tr"><i style="width:{ct["eff"] / cm * 100:.0f}%"></i></div><b>{ct["eff"]:+.2f}</b></div>'
            f'<div class="wt fq-mut">×{w:.2f}</div></div>')
    out.append('<div class="fq-sec">Rule ที่ทำงาน <small>แสดง 8 อันดับแรก</small></div>')
    body = "".join(rows) if top else '<div class="fq-empty">ไม่มี Rule ใดทำงาน</div>'
    out.append(_card("สัญญาณที่ใช้ตัดสิน", body, "fq-c12"))

    # ---- บริบท + ตรวจเหย้า/เยือน
    ctx = m.get("context") or {}
    labels = [("derby", "ดาร์บี้"), ("high_scoring_league", "ลีกประตูเยอะ"), ("high_draw_league", "ลีกเสมอสูง"),
              ("high_volatility", "ลีกผันผวนสูง"), ("cup_group_stage", "ถ้วยรอบแบ่งกลุ่ม"), ("knockout", "น็อคเอาต์"),
              ("continental_cup", "ถ้วยทวีป"), ("late_goal_tendency", "ยิงท้ายเกมสูง")]
    chips = [_chip({"league": "ลีก", "cup": "ถ้วย", "playoff": "เพลย์ออฟ"}.get(ctx.get("type", "league"), "ลีก"), "acc")]
    chips += [_chip(lb, "") for k, lb in labels if ctx.get(k)]
    if ctx.get("desperation") in ("home", "away"):
        chips.append(_chip("หนีตาย/ลุ้นหนัก: " + (f["home"] if ctx["desperation"] == "home" else f["away"]), "warn"))
    if len(chips) == 1:
        chips.append(_chip("ไม่พบบริบทพิเศษ", "off"))
    rs = m.get("research") or {}
    cbody = f'<div class="fq-chips">{"".join(chips)}</div>'
    if rs.get("evidence"):
        cbody += '<ul class="fq-ev">' + "".join(f"<li>{e(x)}</li>" for x in rs["evidence"]) + "</ul>"
    conf = {"high": "สูง", "medium": "ปานกลาง", "low": "ต่ำ"}.get(rs.get("confidence"))
    tag = _chip("ค้นหาอัตโนมัติ" + (f" · ความน่าเชื่อถือ{conf}" if conf else ""), "off") if rs else ""
    vb = "".join(f'<div class="fq-check"><span>{"✅" if ok else "❌"}</span><span>{e(t)}</span></div>' for ok, t in f.get("verify", []))
    out.append('<div class="fq-sec">บริบทแมตช์ และ การตรวจเหย้า/เยือน</div><div class="fq-grid">')
    out.append(_card("บริบทแมตช์", cbody, "fq-c6", tag))
    out.append(_card("Home/Away Verification", vb or '<div class="fq-mut">ไม่มีข้อมูลการตรวจ</div>', "fq-c6"))
    out.append('</div></div>')
    return "".join(out)


# ------------------------------------------------------------------ รายงาน HTML แบบไฟล์เดี่ยว (ดาวน์โหลด)
def report_document(res):
    f = res["f"]
    body = kpi_and_match(res) + analysis_body(res)
    warns = "".join(f"<li>{e(w)}</li>" for w in res.get("warns", []))
    extra = f'<div class="fq"><div class="fq-sec">คำเตือนจากการอ่านข้อมูล</div><ul class="fq-ev">{warns}</ul></div>' if warns else ""
    return ('<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(f["home"])} vs {e(f["away"])} · Football Quant</title><style>'
            "body{margin:0;padding:20px;background:#0b1220;color:#e6edf7;font-family:-apple-system,BlinkMacSystemFont,'Sukhumvit Set','Thonburi','Noto Sans Thai','Segoe UI',Tahoma,sans-serif}"
            ".wrap{max-width:1000px;margin:0 auto}h1{font-size:1.2rem;margin:0 0 4px}.sub{color:#8fa3c0;font-size:.8rem;margin-bottom:10px}"
            f"{CSS}</style></head><body><div class=\"wrap\"><h1>⚽ {e(f['home'])} vs {e(f['away'])}</h1>"
            f"<div class=\"sub\">Football Quant V5.9 · รายงานวิเคราะห์ · ไม่ใช่คำแนะนำทางการเงิน ผลลัพธ์ไม่รับประกัน</div>{body}{extra}</div></body></html>")


# ------------------------------------------------------------------ แดชบอร์ดสถิติ
def stats_dashboard(state, history):
    done = [r for r in history if r.get("status") == "settled"]
    pend = [r for r in history if r.get("status") == "pending"]
    if not done:
        return ('<div class="fq"><div class="fq-empty">ยังไม่มีผลที่บันทึก · ใส่ผลจริงที่แท็บ “บันทึกผล” เพื่อดูสถิติและให้ระบบเรียนรู้'
                f'<br><span class="fq-small">รอผล {len(pend)} นัด</span></div></div>')
    w = sum(1 for r in done if r["pick_r"] > 0)
    l = sum(1 for r in done if r["pick_r"] < 0)
    p = len(done) - w - l
    pr = sum(r["pick_profit"] for r in done)
    wr = w / (w + l) if (w + l) else 0
    roi = pr / len(done)
    kp = []
    kp.append(_card("อัตราชนะ (ไม่นับเจ๊า)", f'<div class="fq-donut" style="--p:{wr * 100:.0f};--c:{"#34d399" if wr >= .5 else "#f87171"}"><div>{wr:.0%}<small>{w}ช / {l}พ</small></div></div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("กำไรสุทธิ (หน่วย)", f'<div class="num {"fq-up" if pr >= 0 else "fq-down"}">{pr:+.2f}</div><div class="fq-small fq-mut">ROI {roi:+.1%} ต่อไม้</div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("บันทึกผลแล้ว", f'<div class="num">{len(done)}</div><div class="fq-small fq-mut">ชนะ {w} · เจ๊า {p} · แพ้ {l}</div>', "fq-c3 fq-m6 fq-kpi"))
    kp.append(_card("รอผล", f'<div class="num">{len(pend)}</div><div class="fq-small fq-mut">สัญญาณที่ยังไม่จบเกม</div>', "fq-c3 fq-m6 fq-kpi"))
    out = ['<div class="fq"><div class="fq-grid">' + "".join(kp) + "</div>"]

    # กำไร/ขาดทุนต่อไม้
    last = done[-40:]
    mx = max([1.0] + [abs(r["pick_profit"]) for r in last])
    cum, run = [], 0.0
    for r in done:
        run += r["pick_profit"]
        cum.append(run)
    bars = "".join(
        f'<div title="{e(r["features"]["home"])} vs {e(r["features"]["away"])}"><span class="mid"></span>'
        f'<i class="{"p" if r["pick_profit"] >= 0 else "n"}" style="height:{max(abs(r["pick_profit"]) / mx * 50, 2):.0f}%"></i></div>' for r in last)
    out.append('<div class="fq-sec">ผลงานต่อไม้ <small>แท่งเขียว = กำไร · แดง = ขาดทุน · ล่าสุด 40 ไม้</small></div>')
    out.append(_card("กำไร/ขาดทุนต่อไม้", f'<div class="fq-pl">{bars}</div>'
                     f'<div class="fq-small fq-mut" style="margin-top:8px">กำไรสะสม: <b class="{"fq-up" if cum[-1] >= 0 else "fq-down"}">{cum[-1]:+.2f}</b> '
                     f'· สูงสุด {max(cum):+.2f} · ต่ำสุด {min(cum):+.2f}</div>', "fq-c12"))

    # แยกตามตลาด
    by = {}
    for r in done:
        k = r["pick"]["market"].split("_")[0]
        b = by.setdefault(k, [0, 0, 0, 0.0])
        b[0] += 1
        b[1] += r["pick_r"] > 0
        b[2] += r["pick_r"] < 0
        b[3] += r["pick_profit"]
    names = {"HDP": "แฮนดิแคป", "OU": "สูง/ต่ำ", "X12": "1X2"}
    rows = ['<div class="fq-row head" style="grid-template-columns:1.4fr 1fr 1fr 1fr"><span>ตลาด</span><span>ไม้</span><span>ชนะ/แพ้</span><span>กำไร</span></div>']
    for k, (n, ww, ll, pf) in by.items():
        rows.append(f'<div class="fq-row" style="grid-template-columns:1.4fr 1fr 1fr 1fr"><b>{names.get(k, k)}</b><span>{n}</span><span>{ww}/{ll}</span>'
                    f'<b class="{"fq-up" if pf >= 0 else "fq-down"}">{pf:+.2f}</b></div>')
    out.append('<div class="fq-sec">แยกตามตลาด</div>')
    out.append(_card("ผลงานแยกตลาด", "".join(rows), "fq-c12"))

    # น้ำหนัก Rule
    wts = state.get("weights") or {}
    rs = state.get("rule_stats") or {}
    items = []
    for k, v in wts.items():
        d0 = q.DEFAULT_WEIGHTS.get(k, 1.0)
        items.append((abs(v - d0), rs.get(k, {}).get("n", 0), k, v, d0))
    items.sort(key=lambda x: (-x[1], -x[0]))
    wrows = []
    for _, n, k, v, d0 in items[:14]:
        col = "#34d399" if v > d0 + 0.005 else "#f87171" if v < d0 - 0.005 else "#64748b"
        wrows.append(f'<div class="fq-w"><span class="nm">{e(k)} <small>{e(q.RULE_NAMES.get(k, "Rule ที่เรียนรู้เอง"))}</small></span>'
                     f'<div class="tr"><i style="width:{min(v / 3 * 100, 100):.0f}%;background:{col}"></i><u style="left:{min(d0 / 3 * 100, 100):.0f}%"></u></div>'
                     f'<span class="fq-small" style="text-align:right">{v:.2f} <span class="fq-mut">({n})</span></span></div>')
    out.append('<div class="fq-sec">น้ำหนัก Rule ที่เรียนรู้ <small>แถบ = น้ำหนักปัจจุบัน · เส้นขาว = ค่าเริ่มต้น · วงเล็บ = จำนวนครั้งที่ใช้</small></div>')
    out.append(_card("น้ำหนัก Rule (เรียงตามจำนวนครั้งที่ใช้)", "".join(wrows), "fq-c12"))

    # ประวัติล่าสุด
    hist = []
    for r in list(reversed(history))[:10]:
        fe = r["features"]
        if r["status"] == "settled":
            kind = "ok" if r["pick_r"] > 0 else "bad" if r["pick_r"] < 0 else "warn"
            tail = _chip(f'{q.result_word(r["pick_r"])} {r["pick_profit"]:+.2f}', kind) + (" " + _chip("แก้ไขแล้ว", "warn") if r.get("edits") else "")
        else:
            tail = _chip("รอผล", "off")
        hist.append(f'<div class="fq-hist"><div>{e(fe["home"])} vs {e(fe["away"])}<small>{e(r["pick"]["label"])}</small></div><div>{tail}</div></div>')
    out.append('<div class="fq-sec">รายการล่าสุด</div>')
    out.append(_card("ประวัติ 10 รายการล่าสุด", "".join(hist), "fq-c12"))
    out.append("</div>")
    return "".join(out)
