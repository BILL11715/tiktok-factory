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
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = {"title", "chat", "terminal", "code", "card", "list", "stat", "compare", "search"}
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
    if total < 1250:
        problems.append(f"texte trop court ({total} car.) : viser 1 300 à 1 550 car. pour dépasser 60 s")
    if total > 1650:
        problems.append(f"texte trop long ({total} car.) : viser 1 300 à 1 550 car. (voix posée, 80 à 95 s)")
    nvis = 0
    for i, s in enumerate(segs):
        if len(s["text"]) > 260:
            problems.append(f"segment {i + 1} trop long ({len(s['text'])} car.) : découper")
        v = s.get("visual")
        if v:
            nvis += 1
            if v.get("kind") not in KINDS:
                problems.append(f"segment {i + 1} : visual.kind inconnu « {v.get('kind')} »")
    if nvis < 8:
        problems.append(f"seulement {nvis} scènes : il en faut au moins 8 (une toutes les 5 à 8 s)")
    cv = script.get("cover") or {}
    if not cv.get("text"):
        problems.append("cover.text manquant : affiche de couverture de 3 à 6 mots (miniature du profil)")
    elif len(cv["text"].split()) > 7:
        problems.append("cover.text > 7 mots : l'affiche doit se lire d'un coup d'oeil")
    if script.get("theme") not in ("ia", "seo"):
        problems.append("theme doit valoir « ia » ou « seo »")
    # style « stickers » : un emoji 3D par segment, étiquettes et titres-chocs courts
    from . import web_video
    check_emoji = web_video.EMOJI_DIR.exists()
    for i, s in enumerate(segs):
        st = s.get("sticker")
        if not st:
            problems.append(f"segment {i + 1} : sticker manquant (un emoji, ex. « 🔎 »)")
        elif check_emoji and not web_video.emoji_file(st):
            problems.append(f"segment {i + 1} : emoji « {st} » absent du pack Fluent 3D, en choisir un autre")
        if len(s.get("label", "")) > 24:
            problems.append(f"segment {i + 1} : label > 24 caractères")
        if s.get("punch"):
            if len(s["punch"].split()) > 3:
                problems.append(f"segment {i + 1} : punch > 3 mots")
            elif not any(w.lower().strip(".,!?") in s["text"].lower() for w in s["punch"].split()):
                problems.append(f"segment {i + 1} : punch doit reprendre un mot réellement dit dans ce segment")
    return problems


def montage(script_path: str) -> None:
    """Montage « stickers » HyperFrames (web/page.html), voir factory/web_video.py."""
    from . import web_video
    sp = Path(script_path).resolve()
    work = sp.parent
    script = json.loads(sp.read_text())
    v = json.loads((work / "voice.json").read_text())
    r = web_video.render(script, v, work, work / "video.mp4")
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
    # @iafortous : voix Gemini « Kore » UNIQUEMENT (décision de Bill, 26/10/2026) : aucune voix de
    # secours. Sans Gemini, le rendu s'arrête (l'agent note l'échec dans Notion, rien dans Buffer).
    if not voice.GEMINI_OK.exists() and os.environ.get("TF_VOICE") != "gemini":
        raise SystemExit("VOIX GEMINI INDISPONIBLE : voir la ligne [setup] Gemini de /tmp/tf-setup.out. Aucune vidéo produite.")
    os.environ["TF_VOICE"] = "gemini"
    os.environ["TF_VOICE_ONLY"] = "gemini"
    print(f"[1/3] voix ({voice.engine()})")
    # 0,6 s de silence au début : l'affiche de couverture s'affiche avant que la voix démarre
    v = voice.synthesize(script["segments"], work, script.get("tone", "pote"), lead=0.6)
    print(f"      durée {v['duration']:.1f}s")
    if v["duration"] < 58:
        print(f"[!] vidéo courte ({v['duration']:.0f} s) : allonger le script la prochaine fois")
    if v["engine"] != "gemini":
        raise SystemExit(f"VOIX GEMINI EN ÉCHEC ({v.get('fallback', '')}). Aucune vidéo produite.")
    v = align.align(v)
    if v["engine"] == "gemini":  # un seul fichier pour tout le texte : scènes recalées sur la voix réelle
        v = voice.reslot(v)
    (work / "voice.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    print("[2/3] montage HyperFrames (style stickers)")
    subprocess.run([sys.executable, "-m", "factory.make_tech", "--montage", str(sp)], cwd=str(ROOT), check=True)
    r = json.loads((work / "montage.json").read_text())
    print("[3/3] rangement")
    stamp = work.name
    dest_dir = ROOT / "videos" / "ia" / stamp[:4] / stamp[5:7]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stamp}.mp4"
    shutil.copy(work / "video.mp4", dest)
    rel = dest.relative_to(ROOT)
    result = {**r, "voice_engine": v["engine"], "voice_fallback": v.get("fallback", ""), "repo_path": str(rel),
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
