"""Measure every generated WAV and render spectrogram PNGs (PIL only, no matplotlib).

Writes work/lemondev/bh-001/evidence/audio/report.txt and spectrogram PNGs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synth import SR, lufs, read_wav, seam_stats, todb  # noqa: E402

SPEC_SFX = ["swing_heavy_1", "hit_flesh_1", "crit_hit", "block_1", "parry", "fire_explode",
            "cast_ice", "lightning_zap_1", "thunder_strike", "footstep_stone_1", "boss_roar",
            "level_up", "loot_drop_legendary", "ui_click", "burn_loop"]

_CMAP = np.array([[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122],
                  [229, 80, 100], [251, 135, 97], [254, 194, 135], [252, 253, 191]], float)


def cmap(v):
    v = np.clip(v, 0, 1) * (len(_CMAP) - 1)
    i = np.minimum(np.floor(v).astype(int), len(_CMAP) - 2)
    f = (v - i)[..., None]
    return (_CMAP[i] * (1 - f) + _CMAP[i + 1] * f).astype(np.uint8)


def spectrogram_png(x, path, title, width=1200, height=420, fmin=30.0, fmax=20000.0, floor=-100.0):
    mono = x if x.ndim == 1 else x.mean(axis=1)
    nfft = 4096 if len(mono) > SR * 20 else 2048
    hop = max(64, int(np.ceil(max(len(mono) - nfft, 1) / width)))
    pad = np.concatenate([np.zeros(nfft // 2), mono, np.zeros(nfft)])
    frames = (len(pad) - nfft) // hop
    win = np.hanning(nfft)
    idx = np.arange(nfft)[None, :] + hop * np.arange(frames)[:, None]
    S = np.abs(np.fft.rfft(pad[idx] * win, axis=1)) / (np.sum(win) / 2)
    D = 20 * np.log10(S + 1e-10)
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    ylog = np.geomspace(fmax, fmin, height)
    # map each pixel row to the max over its frequency band (keeps thin partials visible)
    edges = np.sqrt(ylog[:-1] * ylog[1:])
    edges = np.concatenate([[fmax], edges, [fmin]])
    img = np.empty((height, frames))
    for r in range(height):
        hi, lo = edges[r], edges[r + 1]
        sel = (freqs >= lo) & (freqs < hi)
        if np.any(sel):
            img[r] = D[:, sel].max(axis=1)
        else:
            k = np.argmin(np.abs(freqs - ylog[r]))
            img[r] = D[:, k]
    img = (img - floor) / (-floor)
    rgb = cmap(img)
    spec = Image.fromarray(rgb).resize((width, height), Image.BILINEAR)

    L, T, W_H = 60, 30, 90
    canvas = Image.new("RGB", (width + L + 20, height + T + W_H + 40), (18, 18, 22))
    canvas.paste(spec, (L, T + W_H))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    d.text((L, 8), title, fill=(230, 230, 230), font=font)
    # waveform (peak envelope per column)
    cols = np.array_split(np.abs(mono), width)
    env = np.array([c.max() if len(c) else 0 for c in cols])
    mid = T + W_H // 2
    for i, e in enumerate(env):
        h = int(e * (W_H // 2 - 4))
        d.line([(L + i, mid - h), (L + i, mid + h)], fill=(120, 190, 255))
    d.line([(L, mid), (L + width, mid)], fill=(60, 60, 70))
    # axes
    for f in [50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]:
        if fmin <= f <= fmax:
            y = T + W_H + int(np.log(fmax / f) / np.log(fmax / fmin) * (height - 1))
            d.line([(L - 5, y), (L, y)], fill=(200, 200, 200))
            d.text((4, y - 6), f"{f/1000:g}k" if f >= 1000 else f"{f}", fill=(200, 200, 200), font=font)
    dur = len(mono) / SR
    step = next(s for s in [0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30] if dur / s <= 12)
    tt = 0.0
    while tt <= dur + 1e-9:
        xpx = L + int(tt / dur * (width - 1))
        y0 = T + W_H + height
        d.line([(xpx, y0), (xpx, y0 + 5)], fill=(200, 200, 200))
        d.text((xpx - 10, y0 + 8), f"{tt:g}s", fill=(200, 200, 200), font=font)
        tt += step
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def measure(path):
    x, sr, loop = read_wav(path)
    a = x if x.ndim == 2 else x[:, None]
    pk = float(np.max(np.abs(a)))
    rms = float(np.sqrt(np.mean(a ** 2)))
    clip = int(np.sum(np.abs(a) >= 32767 / 32768))
    st = dict(name=Path(path).stem, ch=a.shape[1], sr=sr, dur=len(a) / sr, peak_db=todb(pk),
              rms_db=todb(rms), lufs=lufs(x), clip=clip, loop=loop,
              first=float(np.max(np.abs(a[0]))), last=float(np.max(np.abs(a[-1]))))
    if loop:
        st.update(seam_stats(x))
    return st, x


def main(sfx_dir, mus_dir, out_dir):
    out_dir = Path(out_dir)
    spec_dir = out_dir / "spectrograms"
    rows = []
    files = sorted(Path(sfx_dir).glob("*.wav")) + sorted(Path(mus_dir).glob("*.wav"))
    for f in files:
        st, x = measure(f)
        rows.append(st)
        nm = st["name"]
        if nm in SPEC_SFX or nm.startswith("music_") or nm.startswith("amb_"):
            spectrogram_png(x, spec_dir / f"{nm}.png", f"{f.parent.name}/{f.name}  "
                            f"{st['dur']:.2f}s  peak {st['peak_db']:.2f} dBFS  {st['lufs']:.1f} LUFS")
    lines = ["Beyond Heroes audio report (generated by tools/audio/analyze.py)",
             "peak/rms in dBFS; LUFS = ITU-R BS.1770-4 integrated (gated); clip = samples at full scale;",
             "first/last = |sample| at file start/end (click check, one-shots);",
             "loops: seam = |x[last]-x[0]| (max over channels), vs p99/max of in-file sample-to-sample |diff|;",
             "PASS if seam <= p99 of in-file diffs.", ""]
    hdr = f"{'file':34s} {'ch':>2s} {'dur_s':>7s} {'peak':>7s} {'rms':>7s} {'LUFS':>6s} {'clip':>4s} {'first':>7s} {'last':>7s}  loop seam"
    for group, pred in [("SFX", lambda s: not (s["name"].startswith("music_") or s["name"].startswith("amb_"))),
                        ("AMBIENCE", lambda s: s["name"].startswith("amb_")),
                        ("MUSIC", lambda s: s["name"].startswith("music_"))]:
        sel = [s for s in rows if pred(s)]
        lines += [f"== {group} ({len(sel)} files) ==", hdr]
        for s in sel:
            line = (f"{s['name'] + '.wav':34s} {s['ch']:2d} {s['dur']:7.2f} {s['peak_db']:7.2f} {s['rms_db']:7.2f} "
                    f"{s['lufs']:6.1f} {s['clip']:4d} {s['first']:7.4f} {s['last']:7.4f}")
            if s["loop"]:
                ok = s["seam_jump"] <= s["diff_p99"]
                line += (f"  smpl[{s['loop'][0]}..{s['loop'][1]}] seam={s['seam_jump']:.5f} "
                         f"p99={s['diff_p99']:.5f} max={s['diff_max']:.5f} {'PASS' if ok else 'FAIL'}")
            lines.append(line)
        lines.append("")
    allpk = max(s["peak_db"] for s in rows)
    nclip = sum(s["clip"] for s in rows)
    loops = [s for s in rows if s["loop"]]
    npass = sum(1 for s in loops if s["seam_jump"] <= s["diff_p99"])
    lines += [f"TOTAL files: {len(rows)}   max peak: {allpk:.2f} dBFS   clipped samples: {nclip}   "
              f"loops seamless: {npass}/{len(loops)}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines[-1:]))
    return rows


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    main(root / "game/assets/audio/sfx", root / "game/assets/audio/music", root / "work/lemondev/bh-001/evidence/audio")
