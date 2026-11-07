# -*- coding: utf-8 -*-
"""Backtest แบบ walk-forward: เทียบการ "ไม่เรียนรู้" กับ "เรียนรู้ต่อเนื่อง" บนประวัติผลที่บันทึกไว้

หลักการ (ไม่มองอนาคต): เดินตามลำดับที่ใส่ผลจริงทีละนัด
  1) ให้ทุกแบบฟันธงนัดนั้นด้วยสถานะ "ณ ตอนนั้น" (ใช้ features ที่เก็บไว้ในประวัติ)
  2) ตัดสินผลด้วยสกอร์จริง
  3) แบบที่เรียนรู้จึงค่อยอัปเดตน้ำหนัก/สร้าง Rule ใหม่ จากนัดนั้น แล้วไปนัดถัดไป
ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากัน (cold start) ไม่ใช้สถานะที่เรียนรู้สะสมไว้ในระบบจริง
"""
import copy
import html as _html
import random

import football_quant_v58 as q

ARMS = ("static", "weights", "full")
ARM_LABEL = {"static": "ไม่เรียนรู้ (Rule เดิม)", "weights": "เรียนรู้เฉพาะน้ำหนัก Rule",
             "full": "เรียนรู้เต็มรูปแบบ (+สร้าง Rule ใหม่)"}
ARM_COLOR = {"static": "#94a3b8", "weights": "#fbbf24", "full": "#2dd4bf"}
MIN_RELIABLE = 30          # ต่ำกว่านี้ถือว่าข้อมูลน้อยเกินสรุป


class MemStore:
    """ที่เก็บสถานะในหน่วยความจำสำหรับ backtest (ไม่แตะดิสก์/คลาวด์)"""

    def __init__(self, params=None):
        self.state = {"weights": dict(q.DEFAULT_WEIGHTS), "rule_stats": {}, "learned_rules": [],
                      "params": dict(params or {}), "meta": {"next_learned": 1, "schema": "5.9"}}
        self.history = []
        self.inc_stats = {}

    @property
    def params(self):
        p = dict(q.DEFAULT_PARAMS)
        p.update(self.state["params"])
        return p

    def save(self, *a, **k):
        pass


def _ordered(history):
    items = [(r.get("settle_seq", -1), i, r) for i, r in enumerate(history)
             if r.get("status") == "settled" and r.get("score") and r.get("features")]
    items.sort(key=lambda x: (x[0], x[1]))
    return [r for _, _, r in items]


# ------------------------------------------------------------------ เมตริก
def _metrics(bets):
    n = len(bets)
    if n == 0:
        return {"n": 0}
    pr = [b["profit"] for b in bets]
    w = sum(1 for b in bets if b["r"] > 0)
    l = sum(1 for b in bets if b["r"] < 0)
    mean = sum(pr) / n
    var = sum((x - mean) ** 2 for x in pr) / (n - 1) if n > 1 else 0.0
    std = var ** 0.5
    cum, run, peak, dd = [], 0.0, 0.0, 0.0
    for x in pr:
        run += x
        cum.append(run)
        peak = max(peak, run)
        dd = max(dd, peak - run)
    streak = best = 0
    for b in bets:
        streak = streak + 1 if b["r"] < 0 else 0
        best = max(best, streak)
    W = 10
    wins_ = [sum(pr[i:i + W]) for i in range(n - W + 1)] if n >= W else []
    h = n // 2
    first, second = pr[:h], pr[h:]
    return {"n": n, "wins": w, "pushes": n - w - l, "losses": l,
            "win_rate": w / (w + l) if (w + l) else None, "profit": sum(pr), "roi": mean, "std": std,
            "sharpe": mean / std if std > 1e-9 else None, "max_dd": dd, "loss_streak": best,
            "roll_pos": (sum(1 for x in wins_ if x > 0) / len(wins_)) if wins_ else None,
            "roi_first": (sum(first) / len(first)) if first else None,
            "roi_second": (sum(second) / len(second)) if second else None, "cum": cum}


def _boot(diffs, B, seed):
    n = len(diffs)
    rnd = random.Random(seed)
    means = sorted(sum(diffs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return {"mean": sum(diffs) / n, "lo": means[int(0.025 * B)], "hi": means[min(B - 1, int(0.975 * B))],
            "p_pos": sum(1 for m_ in means if m_ > 0) / B}


# ------------------------------------------------------------------ ตัวรัน
def _walk(recs, scores, params):
    """เดินตามลำดับทีละนัด (ไม่มองอนาคต) คืน (bets ต่อแบบ, stores, จำนวนที่ข้าม)"""
    stores = {k: MemStore(params) for k in ARMS}
    bets = {k: [] for k in ARMS}
    skipped = 0
    for rec, (hg, ag) in zip(recs, scores):
        f = rec["features"]
        try:
            analyses = {k: q.analyze_features(None, copy.deepcopy(f), st) for k, st in stores.items()}
            outcomes = q.settle_all({"features": f}, hg, ag)
            roles = q.role_outcomes({"features": f}, outcomes)
        except Exception:  # noqa  (รายการเก่าที่ features ไม่ครบ)
            skipped += 1
            continue
        for k, st in stores.items():
            _, contribs, pick = analyses[k]
            r, halves = outcomes[pick["market"]]
            bets[k].append({"i": len(bets[k]), "id": rec["id"], "home": f.get("home", ""), "away": f.get("away", ""),
                            "market": pick["market"], "label": pick["label"], "r": r,
                            "profit": q.profit(halves, pick["price_win"]), "strength": pick["strength"],
                            "n_rules": len(st.state["learned_rules"])})
            tmp = {"contribs": contribs, "features": f, "status": "settled", "role_r": roles}
            if k in ("weights", "full"):
                q.update_weights(st, tmp, outcomes)
            if k == "full":
                q.accumulate_stats(st.inc_stats, f["tags"], roles, st.params)
                q.discover_rules(st, verbose=False)
    return bets, stores, skipped


def _gain(bets):
    n = len(bets["static"])
    return sum(bets["full"][i]["profit"] - bets["static"][i]["profit"] for i in range(n)) / n if n else 0.0


def run_backtest(history, params=None, boot=4000, seed=11, permute=0):
    """permute = จำนวนรอบสุ่มสลับสกอร์ระหว่างนัด เพื่อสร้างการแจกแจงของ "กำไรที่ได้จากการเรียนรู้" เมื่อ features ไม่เกี่ยวกับผล
    (ปรับตามโครงสร้างข้อมูลจริง เช่น ความต่างของค่าน้ำ/สัดส่วนสูง-ต่ำ) ใช้คำนวณ p-value"""
    recs = _ordered(history)
    scores = [r["score"] for r in recs]
    bets, stores, skipped = _walk(recs, scores, params)
    n = len(bets["static"])
    out = {"n": n, "skipped": skipped, "bets": bets, "metrics": {k: _metrics(v) for k, v in bets.items()},
           "min_disc": stores["full"].params["disc_min_n"], "learned": stores["full"].state["learned_rules"],
           "weights": {k: dict(st.state["weights"]) for k, st in stores.items()}, "perm": None}
    out["compare"] = {}
    if n >= 2:
        for k in ("weights", "full"):
            d = [bets[k][i]["profit"] - bets["static"][i]["profit"] for i in range(n)]
            changed = sum(1 for i in range(n) if bets[k][i]["market"] != bets["static"][i]["market"])
            better = sum(1 for x in d if x > 1e-9)
            worse = sum(1 for x in d if x < -1e-9)
            out["compare"][k] = {**_boot(d, boot, seed), "changed": changed, "better": better, "worse": worse, "diffs": d}
    if permute and n >= 10:
        # สลับสกอร์ระหว่างนัด (features ยังเดิม) -> การแจกแจงของกำไรต่อไม้ที่ต่างกันเมื่อไม่มีความสัมพันธ์ features↔ผล
        obs = _gain(bets)
        rnd = random.Random(seed + 101)
        gains = []
        for _ in range(permute):
            sh = scores[:]
            rnd.shuffle(sh)
            gains.append(_gain(_walk(recs, sh, params)[0]))
        mean_ = sum(gains) / len(gains)
        sd_ = (sum((g - mean_) ** 2 for g in gains) / max(len(gains) - 1, 1)) ** 0.5
        out["perm"] = {"B": permute, "obs": obs, "null_mean": mean_, "null_sd": sd_,
                       "p": (1 + sum(1 for g in gains if g >= obs)) / (1 + permute)}
    out["verdict"] = verdict(out)
    return out


def verdict(res):
    n = res["n"]
    if n < 2:
        return {"tag": "none", "title": "ยังไม่มีข้อมูลพอทดสอบ", "lines": ["ต้องมีรายการที่บันทึกผลแล้วอย่างน้อย 2 นัด"]}
    cf, ms, perm = res["compare"]["full"], res["metrics"], res.get("perm")
    lines = []
    perm_ok = perm is None or perm["p"] < 0.05
    if n < MIN_RELIABLE:
        tag, title = "small", f"ข้อมูลยังน้อยเกินสรุป (n = {n}, ควรมีอย่างน้อย {MIN_RELIABLE} นัด)"
        lines.append("ผลต่างที่เห็นส่วนใหญ่เกิดจากความบังเอิญ จึงยังไม่ควรใช้ตัดสินว่าแบบไหนดีกว่า")
    elif cf["lo"] > 0 and perm_ok:
        tag, title = "full", "แบบเรียนรู้เต็มรูปแบบดีกว่า และผ่านทั้งการทดสอบ bootstrap และการสุ่มสลับสกอร์"
        if perm is None:
            title = "แบบเรียนรู้เต็มรูปแบบดีกว่า (bootstrap 95%) · ยังไม่ได้รันการทดสอบสุ่มสลับสกอร์ จึงควรระวัง"
    elif cf["hi"] < 0:
        tag, title = "static", "แบบไม่เรียนรู้ดีกว่าอย่างมีนัยสำคัญ (ช่วงเชื่อมั่น 95%)"
    else:
        tag, title = "nodiff", "ยังไม่พบหลักฐานว่าการเรียนรู้ดีกว่าการไม่เรียนรู้"
        if cf["lo"] > 0 and not perm_ok:
            lines.append(f"แม้ bootstrap ชี้ว่าดีกว่า แต่ไม่ผ่านการทดสอบสุ่มสลับสกอร์ (p = {perm['p']:.2f}) "
                         "ส่วนต่างอาจมาจากโครงสร้างข้อมูล (เช่น สัดส่วนสูง/ต่ำ หรือความต่างของค่าน้ำ) ไม่ใช่การเรียนรู้ที่ได้ผลจริง")
        else:
            lines.append("ช่วงเชื่อมั่น 95% ของกำไรต่อไม้ที่ต่างกันคร่อมศูนย์ ผลต่างอยู่ในขอบเขตของการสุ่ม")
    mf, mst = ms["full"], ms["static"]
    if mf.get("max_dd") is not None and mst.get("max_dd") is not None:
        a, b = mf["max_dd"], mst["max_dd"]
        if abs(a - b) > 0.5:
            lines.append(("ความมั่นคง: แบบเรียนรู้เต็มรูปแบบมี drawdown ต่ำกว่า" if a < b else "ความมั่นคง: แบบไม่เรียนรู้มี drawdown ต่ำกว่า")
                         + f" ({a:.2f} เทียบ {b:.2f} หน่วย) · เป็นค่าจากตัวอย่างนี้ ไม่ใช่การยืนยันในระยะยาว")
    if cf["changed"] == 0:
        lines.append("ทั้งสองแบบฟันธงเหมือนกันทุกนัด (ระบบยังเรียนรู้ไม่พอที่จะเปลี่ยนการตัดสินใจ) จึงไม่มีความต่าง")
    return {"tag": tag, "title": title, "lines": lines}


# ------------------------------------------------------------------ HTML
CSS = """
.fq-cmp { display:grid; grid-template-columns:minmax(0,1.5fr) repeat(3,minmax(0,1fr)); gap:8px; align-items:center;
          padding:8px 0; border-bottom:1px solid var(--line); font-size:.84rem; }
.fq-cmp:last-child { border-bottom:none; }
.fq-cmp.head { color:var(--mut); font-size:.7rem; letter-spacing:.05em; text-transform:uppercase; padding-top:0; }
.fq-cmp .k { color:var(--mut); } .fq-cmp b { font-weight:600; } .fq-cmp .best { color:var(--up); font-weight:700; }
.fq-cmp .a { text-align:right; }
.fq-legend { display:flex; flex-wrap:wrap; gap:12px; margin-bottom:8px; font-size:.78rem; color:var(--mut); }
.fq-legend i { display:inline-block; width:18px; height:3px; border-radius:3px; margin-right:6px; vertical-align:middle; }
.fq-verdict { border-radius:16px; padding:16px 18px; border:1px solid var(--line); background:var(--panel); }
.fq-verdict.full { background:rgba(52,211,153,.1); border-color:rgba(110,231,183,.35); }
.fq-verdict.static { background:rgba(251,191,36,.08); border-color:rgba(253,224,71,.3); }
.fq-verdict.small, .fq-verdict.nodiff, .fq-verdict.none { background:rgba(148,163,184,.1); border-color:rgba(148,163,184,.3); }
.fq-verdict .t { font-size:1.12rem; font-weight:700; margin-bottom:6px; } .fq-verdict ul { margin:6px 0 0; padding-left:18px; color:#b8c7df; font-size:.86rem; line-height:1.6; }
@media (max-width: 820px) { .fq-cmp { grid-template-columns:minmax(0,1.3fr) repeat(3,minmax(0,1fr)); font-size:.76rem; gap:4px; } }
"""


def e(x):
    return _html.escape(str(x))


def _fmt(v, kind):
    if v is None:
        return "–"
    if kind == "n":
        return str(int(v))
    if kind == "pct":
        return f"{v:.0%}"
    if kind == "sgn":
        return f"{v:+.2f}"
    return f"{v:.2f}"


def _svg_curves(series, n):
    W, H, L, B, T = 760, 230, 44, 24, 10
    allv = [0.0] + [x for s in series.values() for x in s]
    lo, hi = min(allv), max(allv)
    if hi - lo < 1e-9:
        hi, lo = hi + 1, lo - 1
    pad = (hi - lo) * 0.08
    lo, hi = lo - pad, hi + pad
    X = lambda i: L + (W - L - 8) * (i / max(n - 1, 1))
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" style="display:block;max-width:100%">']
    for v, lab in ((lo + pad, f"{lo + pad:+.1f}"), (0.0, "0"), (hi - pad, f"{hi - pad:+.1f}")):
        y = Y(v)
        op = 0.35 if v == 0 else 0.08
        dash = ' stroke-dasharray="4 4"' if v == 0 else ""
        parts.append(f'<line x1="{L}" x2="{W - 8}" y1="{y:.1f}" y2="{y:.1f}" stroke="rgba(255,255,255,{op})" stroke-width="1"{dash}/>'
                     f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#8fa3c0">{lab}</text>')
    parts.append(f'<text x="{L}" y="{H - 6}" font-size="11" fill="#8fa3c0">นัดที่ 1</text>'
                 f'<text x="{W - 8}" y="{H - 6}" text-anchor="end" font-size="11" fill="#8fa3c0">นัดที่ {n - 1}</text>')
    for k in ("static", "weights", "full"):
        s = series[k]
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
        parts.append(f'<polyline fill="none" stroke="{ARM_COLOR[k]}" stroke-width="{2.6 if k == "full" else 2}" '
                     f'stroke-linejoin="round" stroke-linecap="round" points="{pts}"/>')
    parts.append("</svg>")
    return "".join(parts)


def report_html(res):
    n = res["n"]
    if n < 2:
        return '<div class="fq"><div class="fq-empty">ต้องมีรายการที่บันทึกผลแล้วอย่างน้อย 2 นัดจึงจะทดสอบย้อนหลังได้</div></div>'
    ms, cp, vd = res["metrics"], res["compare"], res["verdict"]
    out = ['<div class="fq">']
    lines = "".join(f"<li>{e(x)}</li>" for x in vd["lines"])
    out.append(f'<div class="fq-verdict {vd["tag"]}"><div class="fq-h"><span>ข้อสรุปของการทดสอบ</span>'
               f'<span class="fq-chip off">{n} นัด{(" · ข้าม " + str(res["skipped"]) + " นัดที่ข้อมูลไม่ครบ") if res["skipped"] else ""}</span></div>'
               f'<div class="t">{e(vd["title"])}</div><ul>{lines}</ul></div>')

    # ตารางเทียบ
    rows = [("จำนวนไม้", "n", "n", None), ("ชนะ / เจ๊า / แพ้", None, None, None), ("อัตราชนะ (ไม่นับเจ๊า)", "win_rate", "pct", 1),
            ("กำไรสุทธิ (หน่วย)", "profit", "sgn", 1), ("ROI ต่อไม้", "roi", "sgn", 1), ("Drawdown สูงสุด (ต่ำ = มั่นคง)", "max_dd", "num", -1),
            ("แพ้ติดต่อกันสูงสุด (ไม้)", "loss_streak", "n", -1), ("ความผันผวนต่อไม้ (std)", "std", "num", -1),
            ("กำไร/ความผันผวน (Sharpe-like)", "sharpe", "num", 1), ("ช่วง 10 ไม้ที่กำไร (%)", "roll_pos", "pct", 1),
            ("ROI ครึ่งแรก", "roi_first", "sgn", None), ("ROI ครึ่งหลัง", "roi_second", "sgn", None)]
    head = '<div class="fq-cmp head"><span></span>' + "".join(f'<span class="a">{e(ARM_LABEL[k])}</span>' for k in ARMS) + "</div>"
    body = []
    for lab, key, kind, direction in rows:
        if key is None:
            cells = "".join(f'<span class="a">{ms[k]["wins"]} / {ms[k]["pushes"]} / {ms[k]["losses"]}</span>' for k in ARMS)
        else:
            vals = {k: ms[k].get(key) for k in ARMS}
            best = None
            if direction and any(v is not None for v in vals.values()):
                cand = [v for v in vals.values() if v is not None]
                best = max(cand) if direction > 0 else min(cand)
                if len({round(v, 6) for v in cand}) == 1:
                    best = None
            cells = "".join(f'<span class="a {"best" if best is not None and vals[k] is not None and abs(vals[k] - best) < 1e-9 else ""}">{_fmt(vals[k], kind)}</span>' for k in ARMS)
        body.append(f'<div class="fq-cmp"><span class="k">{e(lab)}</span>{cells}</div>')
    out.append('<div class="fq-sec">เทียบผลงาน <small>ตัวหนาสีเขียว = ดีที่สุดในแถว (เฉพาะแถวที่ค่าต่างกัน)</small></div>')
    out.append(f'<div class="fq-card">{head}{"".join(body)}</div>')

    # กราฟกำไรสะสม
    series = {k: [0.0] + ms[k]["cum"] for k in ARMS}
    legend = "".join(f'<span><i style="background:{ARM_COLOR[k]}"></i>{e(ARM_LABEL[k])}</span>' for k in ARMS)
    out.append('<div class="fq-sec">กำไรสะสมตามลำดับนัด <small>walk-forward · ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากัน</small></div>')
    out.append(f'<div class="fq-card"><div class="fq-legend">{legend}</div>{_svg_curves(series, n + 1)}</div>')

    # ความต่างต่อนัด + สถิติ
    cf = cp["full"]
    mx = max([1e-9] + [abs(x) for x in cf["diffs"]])
    bars = "".join(f'<div title="{e(res["bets"]["full"][i]["home"])} vs {e(res["bets"]["full"][i]["away"])}"><span class="mid"></span>'
                   f'<i class="{"p" if x >= 0 else "n"}" style="height:{max(abs(x) / mx * 50, 0 if abs(x) < 1e-9 else 3):.0f}%"></i></div>'
                   for i, x in enumerate(cf["diffs"][-60:]))
    sign = "fq-up" if cf["lo"] > 0 else "fq-down" if cf["hi"] < 0 else "fq-mut"
    stat = (f'<div class="fq-small fq-mut" style="margin-top:8px">กำไรต่อไม้ที่ต่างกัน (เรียนรู้เต็ม − ไม่เรียนรู้): '
            f'<b class="{sign}">{cf["mean"]:+.3f}</b> หน่วย · ช่วงเชื่อมั่น 95% (bootstrap) [{cf["lo"]:+.3f}, {cf["hi"]:+.3f}] · '
            f'ความน่าจะเป็นที่ต่าง > 0 ≈ {cf["p_pos"]:.0%}</div>'
            f'<div class="fq-small fq-mut">ฟันธงต่างกัน {cf["changed"]}/{n} นัด · แบบเรียนรู้ดีกว่า {cf["better"]} นัด · แย่กว่า {cf["worse"]} นัด</div>')
    out.append('<div class="fq-sec">ความต่างรายนัดของแบบเรียนรู้เต็มรูปแบบ <small>แท่งเขียว = ดีกว่า · แดง = แย่กว่าแบบไม่เรียนรู้ · ล่าสุด 60 นัด</small></div>')
    out.append(f'<div class="fq-card"><div class="fq-pl">{bars}</div>{stat}</div>')

    pm = res.get("perm")
    if pm:
        z = (pm["obs"] - pm["null_mean"]) / pm["null_sd"] if pm["null_sd"] > 1e-9 else 0.0
        out.append('<div class="fq-sec">การทดสอบสุ่มสลับสกอร์ (permutation) <small>วัดว่ากำไรจากการเรียนรู้สูงกว่าที่จะได้จากความบังเอิญหรือไม่</small></div>')
        out.append(f'<div class="fq-card"><div class="fq-small fq-mut">สลับสกอร์ระหว่างนัด {pm["B"]} รอบ (features เดิม) แล้วรันซ้ำ: '
                   f'ถ้าไม่มีความสัมพันธ์ระหว่าง features กับผล แบบเรียนรู้จะได้กำไรต่อไม้มากกว่าแบบไม่เรียนรู้เฉลี่ย '
                   f'<b>{pm["null_mean"]:+.3f}</b> (± {pm["null_sd"]:.3f})</div>'
                   f'<div style="margin-top:8px">ของจริง <b class="{"fq-up" if pm["p"] < 0.05 else "fq-mut"}">{pm["obs"]:+.3f}</b> · z ≈ {z:+.1f} · '
                   f'<b>p = {pm["p"]:.3f}</b> {_chip_ok("ผ่าน (p < 0.05)") if pm["p"] < 0.05 else ""}</div></div>')

    # สถานะการเรียนรู้ตอนท้าย
    lr = res["learned"]
    lrows = ""
    for r in sorted(lr, key=lambda r: -(r["wr"] * r["n"]))[:6]:
        tags_txt = " + ".join(r["tags"])
        chip = _chip_ok("ชนะ {:.0%} / {:.0f} นัด".format(r["wr"], r["n"]))
        lrows += (f'<div class="fq-hist"><div>{e(tags_txt)}<small>→ {e(q.ROLE_TH[r["role"]])}</small></div><div>{chip}</div></div>')
    out.append('<div class="fq-sec">สิ่งที่แบบเรียนรู้เต็มรูปแบบสร้างขึ้น <small>ณ นัดสุดท้ายของการทดสอบ</small></div>')
    out.append(f'<div class="fq-card"><div class="fq-small fq-mut" style="margin-bottom:6px">เกณฑ์สร้าง Rule ใหม่: ต้องมีอย่างน้อย {res["min_disc"]} นัดที่รูปแบบซ้ำ · '
               f'สร้างได้ {len(lr)} Rule</div>{lrows or "<div class=fq-mut>ยังไม่มี Rule ที่ผ่านเกณฑ์</div>"}</div>')

    notes = ["ผลทั้งหมดคำนวณจากประวัติที่บันทึกในระบบ ฟันธงซ้ำด้วย features ที่เก็บไว้ ไม่ใช่ไม้ที่คุณเดิมพันจริง",
             "ทุกแบบเริ่มจากน้ำหนักเริ่มต้นเท่ากัน ไม่ใช้สถานะที่ระบบจริงเรียนรู้สะสมไว้ จึงทดสอบตั้งแต่ “เริ่มเรียนรู้จากศูนย์”",
             f"ข้อมูลน้อยกว่า {MIN_RELIABLE} นัด ผลต่างเกือบทั้งหมดเป็นการสุ่ม · แม้ข้อมูลมาก ผลย้อนหลังก็ไม่รับประกันผลในอนาคต",
             "การสร้าง Rule ใหม่จากข้อมูลน้อยเสี่ยง overfit (จับรูปแบบบังเอิญ) ซึ่งการทดสอบแบบ walk-forward นี้ช่วยเปิดเผยได้"]
    out.append('<div class="fq-sec">ข้อจำกัดที่ควรรู้</div>')
    out.append('<div class="fq-card"><ul class="fq-ev">' + "".join(f"<li>{e(x)}</li>" for x in notes) + "</ul></div>")
    out.append("</div>")
    return "".join(out)


def _chip_ok(t):
    return f'<span class="fq-chip ok">{e(t)}</span>'


def report_document(res):
    import dashboard as d
    return ('<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>Backtest · Football Quant</title><style>body{margin:0;padding:20px;background:#0b1220;color:#e6edf7;"
            "font-family:-apple-system,BlinkMacSystemFont,'Sukhumvit Set','Thonburi','Noto Sans Thai','Segoe UI',Tahoma,sans-serif}"
            ".wrap{max-width:1000px;margin:0 auto}h1{font-size:1.2rem;margin:0 0 10px}"
            f"{d.CSS}{CSS}</style></head><body><div class=\"wrap\"><h1>🧪 Backtest: ไม่เรียนรู้ vs เรียนรู้ต่อเนื่อง</h1>{report_html(res)}</div></body></html>")


def text_summary(res):
    """สรุปแบบข้อความสำหรับบรรทัดคำสั่ง"""
    if res["n"] < 2:
        return "ต้องมีรายการที่บันทึกผลแล้วอย่างน้อย 2 นัด"
    ms = res["metrics"]
    L = [f"Backtest {res['n']} นัด (ข้าม {res['skipped']})", ""]
    L.append(f"{'':34}" + "".join(f"{ARM_LABEL[k][:22]:>24}" for k in ARMS))
    for lab, key, kind in (("อัตราชนะ", "win_rate", "pct"), ("กำไรสุทธิ", "profit", "sgn"), ("ROI/ไม้", "roi", "sgn"),
                           ("Drawdown สูงสุด", "max_dd", "num"), ("แพ้ติดสูงสุด", "loss_streak", "n"), ("std/ไม้", "std", "num")):
        L.append(f"{lab:34}" + "".join(f"{_fmt(ms[k].get(key), kind):>24}" for k in ARMS))
    cf = res["compare"]["full"]
    L += ["", f"ส่วนต่างกำไร/ไม้ (เต็ม−ไม่เรียนรู้): {cf['mean']:+.3f} CI95 [{cf['lo']:+.3f},{cf['hi']:+.3f}] P(>0)≈{cf['p_pos']:.0%}",
          f"ฟันธงต่างกัน {cf['changed']}/{res['n']} นัด", "", res["verdict"]["title"], *["- " + x for x in res["verdict"]["lines"]]]
    return "\n".join(L)
