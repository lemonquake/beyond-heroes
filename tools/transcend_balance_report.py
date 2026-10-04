"""Class Transcendence balance report from output/class-transcendence/balance.csv (tests/tools/transcend_balance.gd).

    python tools/transcend_balance_report.py

Writes output/class-transcendence/balance_report.md: for every family and level, each build's single-target and area
damage, static and live effective HP and sustain, as a change against the starting class at the same level, gear and
point budget; then the master pairs side by side (role-adjusted gap) and the worst-case rows (every transcendence skill
and talent at its highest level).
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "output" / "class-transcendence" / "balance.csv"
OUT = ROOT / "output" / "class-transcendence" / "balance_report.md"
NAMES = {"knight": "Knight", "ranger": "Hunter", "mage": "Mage", "shadowblade": "Shadowblade"}


def pct(a, b):
    return (a / b - 1.0) * 100.0 if b else 0.0


def main():
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    for r in rows:
        for k in ("single_dps", "aoe_dps", "ehp", "live_ehp", "sustain_per_s"):
            r[k] = float(r[k])
    by = defaultdict(dict)
    for r in rows:
        by[(r["family"], int(r["level"]))][r["build"]] = r
    out = ["# Class Transcendence balance", "",
           "Source: `output/class-transcendence/balance.csv` from `tests/tools/transcend_balance.gd` (the bh-010 combat bot on "
           "Malasugue, 24 s fights, neutral dummies that never die). Every build of a family has the same gear (its starting "
           "bases made at the hero's level, Elite), the same attribute rule and the same skill/talent point budget. "
           "Changes are against the starting class at the same level. Damage, defense and sustain are listed separately; "
           "nothing is summed into one score. Kill-based traits (Dread, Soul Harvest, Collapse, Blood Price) do not fire on "
           "these dummies. Repeated runs vary by about 5-10 %.", ""]
    for fam in ("knight", "ranger", "mage", "shadowblade"):
        out += ["## %s family" % NAMES[fam], "",
                "| Level | Build | Single | Area | Effective HP | Live effective HP | Sustain / s |",
                "| --- | --- | --- | --- | --- | --- | --- |"]
        for lvl in sorted(l for f, l in by if f == fam):
            g = by[(fam, lvl)]
            base = g["base"]
            for name, r in g.items():
                if name == "base":
                    out.append("| %d | %s (start) | %.0f | %.0f | %.0f | %.0f | %.0f |" % (
                        lvl, NAMES[fam], r["single_dps"], r["aoe_dps"], r["ehp"], r["live_ehp"], r["sustain_per_s"]))
                    continue
                out.append("| %d | %s | %+.0f%% | %+.0f%% | %+.0f%% | %+.0f%% | %.0f |" % (
                    lvl, r["class"].replace("_", " ").title() + (" (max ranks)" if name.endswith("+max") else ""),
                    pct(r["single_dps"], base["single_dps"]), pct(r["aoe_dps"], base["aoe_dps"]),
                    pct(r["ehp"], base["ehp"]), pct(r["live_ehp"], base["live_ehp"]), r["sustain_per_s"]))
        out.append("")
    out += ["## Master pairs", "", "Gap = how far the stronger master is ahead on that measure.", "",
            "| Family | Level | Masters | Single gap | Area gap | Live EHP gap |", "| --- | --- | --- | --- | --- | --- |"]
    for (fam, lvl), g in sorted(by.items()):
        ms = [k for k in g if k not in ("base", "first") and not k.endswith("+max")]
        if len(ms) != 2:
            continue
        a, b = g[ms[0]], g[ms[1]]

        def gap(k):
            hi, lo = max(a[k], b[k]), min(a[k], b[k])
            who = a if a[k] >= b[k] else b
            return "%.0f%% (%s)" % (pct(hi, lo), who["class"].replace("_", " ").title())
        out.append("| %s | %d | %s / %s | %s | %s | %s |" % (NAMES[fam], lvl, ms[0].replace("_", " ").title(), ms[1].replace("_", " ").title(),
                                                       gap("single_dps"), gap("aoe_dps"), gap("live_ehp")))
    out.append("")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
