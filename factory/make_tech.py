"""Point d'entrée du compte IA / SEO Radius (iafortous) : script JSON -> MP4.

Usage :
    python -m factory.make_tech runs/ia/2026-10-10_0800/script.json
    python -m factory.make_tech --montage runs/ia/.../script.json   (interne, processus séparé)

Écrit dans le dossier du run : voice.json, timeline.json, video.mp4, result.json.
Copie la vidéo dans videos/ia/AAAA/MM/ pour publication (raw GitHub).
Pas d'appel à l'abonnement, pas de signature : la valeur fait le travail.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = {"title", "chat", "terminal", "code", "card", "list", "stat", "compare", "search", "shot"}
BANNED = ["—", "plongeons", "découvrons ensemble", "il est important de noter", "dans un monde où",
          "mais ce n'est pas tout", "incontournable", "véritable pépite", "révolutionnaire", "game changer",
          "game-changer", "captivant", "fascinant", "ce n'est pas seulement", "dans cette vidéo",
          "sans plus attendre", "n'hésitez pas", "en résumé", "boostez", "booster votre", "à l'ère de",
          "le futur est là", "libérez", "débloquez", "tirer parti"]
CTA = ["abonne", "abonnez", "follow", "like la vidéo", "lâche un like", "active la cloche"]


def lint(script: dict) -> list[str]:
    from . import voice
    problems = []
    segs = script.get("segments", [])
    full = " ".join(s.get("text", "") for s in segs).lower()
    for b in BANNED:
        if b in full or b in script.get("caption", "").lower():
            problems.append(f"tournure interdite : « {b} »")
    for c in CTA:
        if c in full:
            problems.append(f"appel à l'abonnement interdit sur ce compte : « {c} »")
    if not script.get("hook_text"):
        problems.append("hook_text manquant")
    elif len(script["hook_text"].split()) > 14:
        problems.append("hook_text > 14 mots")
    total = sum(len(voice._plain(s["text"])) for s in segs)
    if total < 1350:
        problems.append(f"texte trop court ({total} car.) : viser 1 450 à 1 750 car. pour dépasser 60 s")
    nvis = 0
    for i, s in enumerate(segs):
        if len(s["text"]) > 260:
            problems.append(f"segment {i + 1} trop long ({len(s['text'])} car.) : découper")
        v = s.get("visual")
        if v:
            nvis += 1
            if v.get("kind") not in KINDS:
                problems.append(f"segment {i + 1} : visual.kind inconnu « {v.get('kind')} »")
    if nvis < 5:
        problems.append(f"seulement {nvis} scènes : il en faut au moins 5 (une toutes les 8 à 12 s)")
    if script.get("theme") not in ("ia", "seo"):
        problems.append("theme doit valoir « ia » ou « seo »")
    return problems


def montage(script_path: str) -> None:
    from . import tech_motion
    sp = Path(script_path).resolve()
    work = sp.parent
    script = json.loads(sp.read_text())
    v = json.loads((work / "voice.json").read_text())
    seed = sum(map(ord, script.get("title", ""))) & 0xFFFF
    r = tech_motion.render(script, v, work, work / "video.mp4", seed=seed)
    (work / "montage.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))


def main(script_path: str) -> dict:
    from . import align, voice
    t0 = time.time()
    sp = Path(script_path).resolve()
    work = sp.parent
    script = json.loads(sp.read_text())
    problems = lint(script)
    if problems:
        print("LINT:", *problems, sep="\n - ")
        raise SystemExit("Script refusé, corriger les points ci-dessus puis relancer.")
    print(f"[1/3] voix ({voice.engine()})")
    v = voice.synthesize(script["segments"], work, script.get("tone", "pote"))
    print(f"      durée {v['duration']:.1f}s")
    if v["duration"] < 58:
        print(f"[!] vidéo courte ({v['duration']:.0f} s) : allonger le script la prochaine fois")
    v = align.align(v)
    (work / "voice.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    print("[2/3] montage Remotion TechShort")
    subprocess.run([sys.executable, "-m", "factory.make_tech", "--montage", str(sp)], cwd=str(ROOT), check=True)
    r = json.loads((work / "montage.json").read_text())
    print("[3/3] rangement")
    stamp = work.name
    dest_dir = ROOT / "videos" / "ia" / stamp[:4] / stamp[5:7]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stamp}.mp4"
    shutil.copy(work / "video.mp4", dest)
    rel = dest.relative_to(ROOT)
    result = {**r, "voice_engine": v["engine"], "repo_path": str(rel),
              "raw_url": f"https://raw.githubusercontent.com/BILL11715/tiktok-factory/main/{rel}",
              "render_seconds": round(time.time() - t0, 1)}
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return result


if __name__ == "__main__":
    if sys.argv[1] == "--montage":
        montage(sys.argv[2])
    elif sys.argv[1] == "--lint":
        p = lint(json.loads(Path(sys.argv[2]).read_text()))
        print("OK" if not p else "\n".join(p))
    else:
        main(sys.argv[1])
