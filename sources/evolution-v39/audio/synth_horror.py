"""KONTUR horror sounds, synthesised from scratch (numpy only, no samples): 44.1 kHz mono 16-bit WAV in out/.
Run: python3 synth_horror.py   (system python with numpy). Loops are made seamless by cross-fading the tail into the head."""
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(20261115)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def norm(x, peak=0.9):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def fft_filter(x, lo=None, hi=None, order=4):
    """Zero-phase band filter in the frequency domain (smooth Butterworth-like edges)."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    X = np.fft.rfft(x)
    g = np.ones_like(f)
    if lo:
        g *= 1 / (1 + (lo / np.maximum(f, 1e-6)) ** (2 * order))
    if hi:
        g *= 1 / (1 + (f / hi) ** (2 * order))
    return np.fft.irfft(X * g, n)


def noise(sec):
    return rng.standard_normal(int(sec * SR))


def reverb(x, wet=0.35, decay=2.2):
    """Cheap diffuse reverb: sum of decaying noise-tail convolution via FFT."""
    n = int(decay * SR)
    tail = rng.standard_normal(n) * np.exp(-np.arange(n) / (decay * SR / 5))
    tail = fft_filter(tail, lo=150, hi=4500)
    size = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(tail, size), size)
    y = y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))
    out = np.zeros(size)
    out[: len(x)] += x * (1 - wet)
    out += y * wet
    return out


def loop(x, fade=0.5):
    """Make x seamless: cross-fade the last `fade` seconds into the first ones, drop the tail."""
    k = int(fade * SR)
    head, tail = x[:k].copy(), x[-k:].copy()
    w = np.linspace(0, 1, k)
    body = x[:-k].copy()
    body[:k] = head * w + tail * (1 - w)
    return body


def save(name, x):
    x = np.clip(x, -1, 1)
    data = (x * 32767).astype("<i2").tobytes()
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print(name, f"{len(x) / SR:.1f}s")


# 1. Low drone: detuned sub tones that beat, slow swells, dark filtered air. Loop ~14 s.
def drone():
    s = 16
    x = np.zeros(int(s * SR))
    tt = t(s)
    for f, a in ((34.0, 1.0), (34.9, 0.9), (51.3, 0.5), (68.7, 0.35), (103.1, 0.18)):
        x += a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6.28))
    x *= 0.65 + 0.35 * np.sin(2 * np.pi * tt / 7.0 + 1.0)
    air = fft_filter(noise(s), lo=60, hi=420) * 1.6
    air *= 0.5 + 0.5 * np.sin(2 * np.pi * tt / 5.3)
    x += air
    x += 0.12 * np.sin(2 * np.pi * (1480 + 14 * np.sin(2 * np.pi * tt / 3.1)) * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * tt / 9.0)) ** 3
    return loop(norm(reverb(x, 0.25, 2.5)), 1.0)


# 2. Raspy breathing: inhale/exhale envelopes of band-limited noise, slightly wet. Loop 4 breaths.
def breath():
    s = 16
    tt = t(s)
    cyc = 4.0
    ph = (tt % cyc) / cyc
    env = np.where(ph < 0.42, np.sin(np.pi * ph / 0.42) ** 1.5, 0) * 0.8 + np.where(ph >= 0.5, np.sin(np.pi * (ph - 0.5) / 0.5) ** 1.2, 0) * 1.0
    n = fft_filter(noise(s), lo=350, hi=2600)
    n2 = fft_filter(noise(s), lo=1800, hi=6500) * 0.35
    x = (n + n2) * env
    x += 0.18 * fft_filter(noise(s), lo=80, hi=220) * env
    x *= 1 + 0.15 * np.sin(2 * np.pi * 31 * tt)       # slight rattle in the chest
    return loop(norm(reverb(x, 0.3, 1.6)), 0.6)


# 3. Creak (v2, soft and low): a rope or beam under load. No sawtooth, nothing above ~900 Hz: three hollow wooden resonances that glide slowly,
#    amplitude-pulsed like slow strain, a faint sub-bass bed and rare dull ticks. Seamless loop of 10 s.
def creak():
    s = 10
    tt = t(s)
    x = np.zeros_like(tt)
    for base, drift, rate, amp in ((146, 20, 0.21, 1.0), (228, 30, 0.17, 0.75), (351, 42, 0.13, 0.5)):    # audible on laptop speakers too
        f = base + drift * np.sin(2 * np.pi * rate * tt + rng.uniform(0, 6.28)) - 10 * np.sin(2 * np.pi * tt / s)
        ph = np.cumsum(f) / SR
        tone = np.sin(2 * np.pi * ph) + 0.35 * np.sin(4 * np.pi * ph + 0.7)
        strain = 0.5 + 0.5 * np.sin(2 * np.pi * (0.35 + 0.1 * amp) * tt + rng.uniform(0, 6.28))
        x += amp * tone * strain ** 2
    grit = fft_filter(noise(s), lo=90, hi=520) * (0.25 + 0.25 * np.sin(2 * np.pi * 0.4 * tt) ** 2)
    x += 0.5 * grit
    x += 0.35 * np.sin(2 * np.pi * 43 * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 5.0))
    for _ in range(4):                                                              # rare dull ticks
        k = int(rng.uniform(0.5, s - 1.5) * SR)
        n = int(0.25 * SR)
        x[k:k + n] += 0.35 * fft_filter(noise(0.25), lo=150, hi=700)[:n] * np.exp(-np.arange(n) / (0.045 * SR))
    x = fft_filter(x, lo=60, hi=1000)
    return loop(norm(reverb(x, 0.35, 2.4), 0.8), 1.0)


# 4. Heavy knock: low thump with a dull click and a long body tail. 1.4 s.
def knock():
    s = 1.4
    tt = t(s)
    f = 48 + 90 * np.exp(-tt * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7.5)
    click = fft_filter(noise(s), lo=400, hi=2200) * np.exp(-tt * 70) * 0.7
    wood = np.sin(2 * np.pi * 182 * tt) * np.exp(-tt * 18) * 0.25 + np.sin(2 * np.pi * 311 * tt) * np.exp(-tt * 26) * 0.15
    return norm(reverb(body + click + wood, 0.35, 2.0))


# 5. Whisper: breathy noise shaped by moving vowel formants with syllable-like gating. 12 s loop.
def whisper():
    s = 14
    tt = t(s)
    x = np.zeros_like(tt)
    syll = np.zeros_like(tt)
    pos = 0.0
    while pos < s - 1.5:
        d = rng.uniform(0.22, 0.55)
        a, b = int(pos * SR), int((pos + d) * SR)
        e = np.sin(np.linspace(0, np.pi, b - a)) ** 1.3
        syll[a:b] = np.maximum(syll[a:b], e * rng.uniform(0.5, 1.0))
        pos += d + rng.uniform(0.05, 0.35) + (rng.uniform(0.5, 1.4) if rng.random() < 0.18 else 0)
    base = noise(s)
    for centre, width, g in ((520, 130, 1.0), (1400, 260, 0.8), (2500, 420, 0.5), (3600, 600, 0.3)):
        drift = 1 + 0.18 * np.sin(2 * np.pi * tt / rng.uniform(1.7, 3.1) + rng.uniform(0, 6))
        band = fft_filter(base, lo=centre * 0.82, hi=centre * 1.2)
        x += g * band * (0.6 + 0.4 * drift)
    x *= syll
    x += 0.08 * fft_filter(noise(s), lo=2500, hi=8000) * syll
    return loop(norm(reverb(x, 0.45, 2.4)), 0.8)


# 6. Heartbeat: slow double thump, 3.2 s loop.
def heartbeat():
    s = 3.2
    tt = t(s)
    x = np.zeros_like(tt)
    for start, amp in ((0.15, 1.0), (0.52, 0.7), (1.85, 1.0), (2.22, 0.7)):
        d = tt - start
        m = d >= 0
        f = 70 - 28 * np.minimum(d, 0.2) / 0.2
        x[m] += amp * np.sin(2 * np.pi * np.cumsum(f[m]) / SR) * np.exp(-d[m] * 16)
    return loop(norm(reverb(x, 0.2, 1.2)), 0.25)


# 7. Stinger (v2, soft): not a hit but a dark swell. Sub tone rising over 0.9 s with a slow attack, a muted minor cluster below 600 Hz,
#    long decay. Nothing sharp, no noise above 700 Hz. 5 s.
def stinger():
    s = 5.0
    tt = t(s)
    att = np.minimum(1, tt / 0.9) ** 2
    dec = np.exp(-np.maximum(tt - 0.9, 0) * 0.9)
    env = att * dec
    sub = np.sin(2 * np.pi * np.cumsum(46 + 14 * np.minimum(tt, 0.9) / 0.9) / SR)
    cluster = sum(np.sin(2 * np.pi * f * tt + rng.uniform(0, 6.28)) * a for f, a in ((116.5, 0.5), (138.6, 0.45), (174.6, 0.3), (207.7, 0.22), (277, 0.12)))
    cluster = cluster * (0.85 + 0.15 * np.sin(2 * np.pi * 2.3 * tt))
    air = fft_filter(noise(s), lo=60, hi=420) * 0.5
    x = (sub * 1.2 + cluster * 0.45 + air) * env
    x = fft_filter(x, lo=30, hi=650)
    return norm(reverb(x, 0.35, 3.0), 0.75)


# 8. Distant footstep tap on hard floor with room tail (single).
def footstep():
    s = 1.2
    tt = t(s)
    thud = np.sin(2 * np.pi * (85 + 40 * np.exp(-tt * 50)) * tt) * np.exp(-tt * 22)
    tap = fft_filter(noise(s), lo=600, hi=3400) * np.exp(-tt * 55)
    return norm(reverb(thud + tap * 0.7, 0.5, 1.8))


# 9. Ventilation: broadband air rumble with slow flutter and a faint 100 Hz motor hum. Loop 12 s.
def vent():
    s = 14
    tt = t(s)
    air = fft_filter(noise(s), lo=60, hi=900) * (0.7 + 0.3 * np.sin(2 * np.pi * tt / 5.0 + 0.7))
    hiss = fft_filter(noise(s), lo=1800, hi=6000) * 0.12 * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 3.3))
    motor = 0.1 * np.sin(2 * np.pi * 100 * tt) + 0.05 * np.sin(2 * np.pi * 200.5 * tt)
    return loop(norm(air + hiss + motor, 0.7), 1.0)


# 10. Distant office: muffled keyboard clicks, a far phone, voices as noise bursts, low room tone. Loop 20 s.
def office_far():
    s = 22
    tt = t(s)
    room = fft_filter(noise(s), lo=80, hi=500) * 0.5
    x = room.copy()
    for _ in range(rng.integers(55, 80)):                                    # key clicks
        at = rng.uniform(0.5, s - 1)
        a = int(at * SR)
        n = int(0.03 * SR)
        click = fft_filter(noise(0.03), lo=1500, hi=4500)[:n] * np.exp(-np.arange(n) / (0.006 * SR))
        x[a:a + n] += click * rng.uniform(0.15, 0.4)
    for _ in range(4):                                                         # murmur bursts
        at = rng.uniform(1, s - 4)
        d = rng.uniform(0.8, 2.0)
        a = int(at * SR)
        n = int(d * SR)
        murmur = fft_filter(noise(d), lo=200, hi=1200)[:n] * np.sin(np.linspace(0, np.pi, n)) ** 2
        x[a:a + n] += murmur * 0.35
    for at in (rng.uniform(2, 8), rng.uniform(12, 19)):                       # far phone ring
        for k in range(4):
            a = int((at + k * 0.18) * SR)
            n = int(0.1 * SR)
            ring = (np.sin(2 * np.pi * 1380 * np.arange(n) / SR) + np.sin(2 * np.pi * 1180 * np.arange(n) / SR)) * np.exp(-np.arange(n) / (0.04 * SR))
            x[a:a + n] += ring * 0.05
    x = fft_filter(x, lo=70, hi=3800)
    return loop(norm(reverb(x, 0.35, 1.8), 0.7), 1.0)


# 11. Level chime: soft rising minor-third pair, quickly decaying (short, not cheerful). 2.6 s.
def sting_level():
    s = 2.6
    tt = t(s)
    x = np.zeros_like(tt)
    for start, f, a in ((0.0, 392.0, 1.0), (0.22, 466.2, 0.9), (0.46, 587.3, 0.8)):
        d = np.clip(tt - start, 0, None)
        x += a * np.sin(2 * np.pi * f * tt) * np.exp(-d * 2.6) * (tt >= start) * np.minimum(1, d / 0.01 + 0.0)
        x += 0.35 * a * np.sin(2 * np.pi * f * 2.01 * tt) * np.exp(-d * 4.0) * (tt >= start)
    return norm(reverb(x, 0.35, 2.0), 0.8)


# 12. Wrong answer: low dissonant thud plus a descending buzz. 2.2 s.
def sting_wrong():
    s = 2.2
    tt = t(s)
    thud = np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-tt * 14)) / SR) * np.exp(-tt * 4.0)
    buzz = np.sign(np.sin(2 * np.pi * np.cumsum(180 - 80 * tt / s) / SR)) * np.exp(-tt * 3.0) * 0.25
    buzz = fft_filter(buzz, lo=100, hi=1400)
    return norm(reverb(thud + buzz, 0.3, 1.6), 0.85)


# 13. Death: huge sub boom, tritone swell collapsing downwards, noise tail. 5 s.
def sting_death():
    s = 5.0
    tt = t(s)
    boom = np.sin(2 * np.pi * np.cumsum(32 + 80 * np.exp(-tt * 5)) / SR) * np.exp(-tt * 0.9)
    pitch = 440 * np.exp(-tt * 0.55)
    swell = (np.sin(2 * np.pi * np.cumsum(pitch) / SR) + np.sin(2 * np.pi * np.cumsum(pitch * 1.414) / SR)) * np.exp(-tt * 1.1) * 0.25
    tail = fft_filter(noise(s), lo=200, hi=3500) * np.exp(-tt * 1.6) * 0.3
    return norm(reverb(boom * 1.2 + swell + tail, 0.4, 3.2), 0.9)


for name, fn in (("Drone", drone), ("Breath", breath), ("Creak", creak), ("Knock", knock), ("Whisper", whisper), ("Heartbeat", heartbeat), ("Stinger", stinger), ("Footstep", footstep), ("Vent", vent), ("OfficeFar", office_far), ("StingLevel", sting_level), ("StingWrong", sting_wrong), ("StingDeath", sting_death)):
    save("KONTUR_" + name, fn())
