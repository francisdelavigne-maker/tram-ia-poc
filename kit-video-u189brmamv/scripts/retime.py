"""Assemble la voix (mp3 par scène), recale scènes/sous-titres sur les durées réelles.
Usage: python3 -I retime.py <script.json> <dossier_mp3> <dossier_projet_hyperframes> [vitesse=1.19]
"""
import json, re, subprocess, sys

S = json.load(open(sys.argv[1]))
SRC = sys.argv[2].rstrip("/") + "/"
P = sys.argv[3].rstrip("/") + "/"
OLD = {"s1": 8.26, "s2": 16.96, "s3": 18.56, "s4": 12.61, "s5": 22.74, "s6": 9.87, "s7": 22.35}
LEAD, GAP, TAIL = 1.0, 0.45, 3.0
SPEED = float(sys.argv[4]) if len(sys.argv) > 4 else 1.19

starts, durs, t = {}, {}, LEAD
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
flt = []
for i, k in enumerate(S):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC + k + ".mp3", "-filter:a", f"atempo={SPEED}", "-ar", "44100", "-ac", "1", SRC + k + ".wav"], check=True)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC + k + ".wav"]))
    starts[k], durs[k] = round(t, 2), round(d, 2)
    cmd += ["-i", SRC + k + ".wav"]
    ms = int(t * 1000)
    flt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    t += d + GAP
total = round(t - GAP + TAIL)
n = len(S)
flt.append("".join(f"[a{j}]" for j in range(n)) + f"amix=inputs={n}:normalize=0,apad=whole_dur={total}[o]")
subprocess.run(cmd + ["-filter_complex", ";".join(flt), "-map", "[o]", "-t", str(total), P + "assets/vo.wav"], check=True)

keys = list(S)
caps = []
for k, txt in S.items():
    sents = [x.strip() for x in re.split(r"(?<=[.?!:])\s+", txt) if x.strip()]
    merged, i = [], 0
    while i < len(sents):
        if len(sents[i]) < 14 and i + 1 < len(sents):
            merged.append(sents[i] + " " + sents[i + 1]); i += 2
        else:
            merged.append(sents[i]); i += 1
    tot = sum(len(x) for x in merged)
    c = starts[k]
    for x in merged:
        dd = durs[k] * len(x) / tot
        caps.append([round(c, 2), round(dd, 2), x]); c += dd
B = [0] + [round(starts[k] - 0.25, 2) for k in keys[1:]] + [total]
K = [round(durs[k] / OLD[k], 3) for k in keys]

s = open(P + "index.html").read()
s = re.sub(r"const B = \[.*?\];", "const B = " + json.dumps(B) + ";", s)
s = re.sub(r"const CAPS = \[.*?\];\n", "const CAPS = " + json.dumps(caps, ensure_ascii=False) + ";\n", s, flags=re.S)
s = re.sub(r"const K = \[.*?\];", "const K = " + json.dumps(K) + ";", s)
s = re.sub(r'data-duration="\d+"', f'data-duration="{total}"', s)  # racine + clips pleine durée
s = re.sub(r"duration:\d+, ease:\"none\"", f'duration:{total}, ease:"none"', s)
# scènes: restaurer leurs durées propres
for i, k in enumerate(keys):
    s = re.sub(rf'(<section id="{k}" class="clip scene" data-start=")[\d.]+(" data-duration=")[\d.]+', rf"\g<1>{B[i]}\g<2>{round(B[i+1]-B[i],2)}", s)
open(P + "index.html", "w").write(s)
print("starts", starts); print("durs", durs); print("B", B); print("K", K); print("total", total)
