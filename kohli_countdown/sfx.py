"""Synthesised sound effects + a light beat bed (no licensed samples needed).

Every function returns a mono float32 numpy array at SR, peak ~1.0.
"""
import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def _env(n, attack, release):
    a = max(1, int(SR * attack))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[a:] = np.exp(-np.linspace(0, 1, n - a) * release)
    return e


def _lowpass(x, cutoff):
    """One-pole lowpass; cutoff may be an array (time-varying sweep)."""
    cutoff = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def _norm(x, peak=1.0):
    m = np.abs(x).max()
    return (x / m * peak).astype(np.float32) if m > 0 else x.astype(np.float32)


def whoosh(dur=0.45):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    sweep = np.geomspace(300, 6000, n // 2)
    sweep = np.concatenate([sweep, sweep[::-1]])[:n]
    if len(sweep) < n:
        sweep = np.pad(sweep, (0, n - len(sweep)), mode="edge")
    hp = noise - _lowpass(noise, 200)
    x = _lowpass(hp, sweep)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    return _norm(x * env, 0.9)


def impact(dur=0.9):
    t = _t(dur)
    freq = 120 * np.exp(-t * 9) + 38
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 60)
    tail = _lowpass(rng.standard_normal(len(t)), 900) * np.exp(-t * 7) * 0.6
    return _norm(np.tanh(2.5 * body) + 0.5 * click + tail)


def tick(dur=0.04):
    t = _t(dur)
    return _norm(np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 180), 0.6)


def ding(dur=0.8, f=1320):
    t = _t(dur)
    x = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in ((1, 1), (2.01, 0.4), (3.02, 0.2)))
    return _norm(x * _env(len(t), 0.002, 6), 0.7)


def pop(dur=0.12):
    t = _t(dur)
    freq = 900 * np.exp(-t * 30) + 250
    x = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 35)
    return _norm(x, 0.8)


def riser(dur=2.0):
    n = int(SR * dur)
    t = _t(dur)
    noise = rng.standard_normal(n)
    x = _lowpass(noise, np.geomspace(200, 9000, n))
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(110, 880, n)) / SR) * 0.35
    env = np.linspace(0, 1, n) ** 2.2
    return _norm((x + tone) * env, 0.8)


def heartbeat(dur=0.9):
    t = _t(dur)
    def thump(t0):
        tt = np.clip(t - t0, 0, None)
        return np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 18) * (t >= t0)
    return _norm(np.tanh(3 * (thump(0) + 0.8 * thump(0.22))))


def crowd(dur=4.0):
    """Stadium roar: band-limited noise swelling in and out."""
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    band = _lowpass(noise, 2500) - _lowpass(noise, 300)
    wobble = 1 + 0.25 * np.sin(2 * np.pi * 3.1 * _t(dur)) * rng.uniform(0.6, 1, n)
    env = np.minimum(1, _t(dur) / 0.6) * np.minimum(1, (dur - _t(dur)) / 1.5)
    return _norm(band * wobble * env, 0.8)


def camera_shutter(dur=0.15):
    t = _t(dur)
    n = rng.standard_normal(len(t))
    x = n * (np.exp(-t * 90) + 0.7 * np.exp(-np.clip(t - 0.06, 0, None) * 90) * (t > 0.06))
    return _norm(x - _lowpass(x, 1500), 0.7)


def beat_bed(dur, bpm=96):
    """Minimal hip-hop-ish loop: kick, clap, hats and a sub note per bar."""
    n = int(SR * dur)
    out = np.zeros(n + 4 * SR)
    beat = 60 / bpm
    kt = _t(0.35)
    kick = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-kt * 20) + 45) / SR) * np.exp(-kt * 9)
    ct = _t(0.2)
    clap = (rng.standard_normal(len(ct)) - _lowpass(rng.standard_normal(len(ct)), 800)) * np.exp(-ct * 25)
    ht = _t(0.05)
    hat = rng.standard_normal(len(ht))
    hat = (hat - _lowpass(hat, 6000)) * np.exp(-ht * 90)
    roots = [55.0, 55.0, 43.65, 49.0]  # A1 A1 F1 G1
    i = 0
    pos = 0.0
    while pos < dur:
        s = int(pos * SR)
        step = i % 16
        if step in (0, 6, 10):
            out[s:s + len(kick)] += kick * 0.9
        if step in (4, 12):
            out[s:s + len(clap)] += clap * 0.35
        out[s:s + len(hat)] += hat * (0.18 if step % 2 else 0.1)
        if step == 0:
            bar = (i // 16) % 4
            bt = _t(beat * 4)
            sub = np.sin(2 * np.pi * roots[bar] * bt) * _env(len(bt), 0.01, 2)
            out[s:s + len(sub)] += sub * 0.35
        i += 1
        pos += beat / 4
    return _norm(np.tanh(out[:n] * 1.2), 0.8)
