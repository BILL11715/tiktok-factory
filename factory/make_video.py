"""Point d'entrée : script JSON -> MP4 prêt à publier.

Usage :
    python -m factory.make_video runs/2026-09-27_1830/script.json

Écrit dans le même dossier : video.mp4, result.json (durée, voix, sources).
Le nom de fichier final est aussi copié dans videos/AAAA/MM/ pour publication.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

from . import align, assets, clips, motion, render, voice

ROOT = Path(__file__).resolve().parent.parent
SIGNATURE = "C'était Asura. On se capte au prochain épisode."
BANNED = ["—", "plongeons", "découvrons ensemble", "il est important de noter",
          "dans un monde où", "mais ce n'est pas tout", "incontournable", "véritable pépite",
          "chef-d'œuvre intemporel", "aventure épique", "captivant", "fascinant",
          "ce n'est pas seulement", "plus qu'un anime"]


def lint(script: dict) -> list[str]:
    """Contrôle anti-IA et structure. Retourne la liste des problèmes."""
    problems = []
    full = " ".join(s["text"] for s in script["segments"]).lower()
    for b in BANNED:
        if b in full:
            problems.append(f"tournure interdite : « {b} »")
    if len(script.get("hook_text", "").split()) > 15:
        problems.append("hook_text > 15 mots")
    total = sum(len(voice._plain(s["text"])) for s in script["segments"])  # sans balises d'émotion
    if script.get("format") != "citation" and total < 1400:
        problems.append(f"texte trop court ({total} car.) : viser 1 500 à 1 650 car. pour dépasser 60 s")
    if not any(s.get("cta") for s in script["segments"]) or \
            not any("abonne" in s["text"].lower() for s in script["segments"] if s.get("cta")):
        problems.append("appel à l'abonnement manquant : un segment avec \"cta\": true qui dit « abonne-toi »")
    if not script.get("hook_text"):
        problems.append("hook_text manquant")
    for s in script["segments"]:
        if len(s["text"]) > 260:
            problems.append(f"segment trop long ({len(s['text'])} car.) : découper")
    return problems


def main(script_path: str) -> dict:
    t0 = time.time()
    sp = Path(script_path).resolve()
    work = sp.parent
    script = json.loads(sp.read_text())
    problems = lint(script)
    if problems:
        print("LINT:", *problems, sep="\n - ")
        if any(k in p for p in problems for k in ("interdite", "trop court", "abonnement", "hook_text manquant")):
            raise SystemExit("Script refusé (anti-IA ou trop court), corriger puis relancer.")
    # signature toujours présente, ton posé
    if not script["segments"][-1]["text"].startswith("C'était Asura"):
        script["segments"].append({"text": SIGNATURE, "tone": "pose",
                                   "shots": [{"anime": script["animes"][0], "kind": "poster"}]})
        if script.get("reveal_text"):
            script["reveal_segments"] = int(script.get("reveal_segments", 1)) + 1
    print(f"[1/4] visuels pour {script['animes']}")
    index = assets.collect(script["animes"], work)
    try:  # extraits vidéo (openings officiels, sakuga) ; sans eux, images fixes
        clips.collect(script["animes"], work, index)
    except Exception as exc:
        print(f"[clips] échec ({exc}), montage en images fixes")
    print(f"[2/4] voix ({voice.engine()})")
    v = voice.synthesize(script["segments"], work, script.get("tone", "pote"))
    print(f"      durée {v['duration']:.1f}s")
    v = align.align(v)  # vrais temps de chaque mot (synchro image/son)
    (work / "voice.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    print("[3/4] montage")
    # le montage tourne dans un processus neuf : la mémoire du modèle de voix est rendue au système
    import subprocess as _sp
    rc = _sp.run([sys.executable, "-m", "factory.montage_cli", str(sp)], cwd=str(ROOT)).returncode
    if rc == 0 and (work / "montage.json").exists():
        r = json.loads((work / "montage.json").read_text())
    else:
        r = None
    out = work / "video.mp4"
    seed = sum(map(ord, script.get("title", ""))) & 0xFFFF
    if r is None:  # secours : montage FFmpeg v2
        print("[montage] Remotion a échoué, montage de secours FFmpeg")
        r = render.render(script, v, index, work, out, seed=seed)
        r["engine"] = "ffmpeg (secours)"
    print("[4/4] rangement")
    stamp = work.name
    dest_dir = ROOT / "videos" / stamp[:4] / stamp[5:7]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{stamp}.mp4"
    shutil.copy(out, dest)
    result = {**r, "voice_engine": v["engine"], "repo_path": str(dest.relative_to(ROOT)),
              "raw_url": f"https://raw.githubusercontent.com/BILL11715/tiktok-factory/main/"
                         f"{dest.relative_to(ROOT)}",
              "lint": problems, "render_seconds": round(time.time() - t0, 1)}
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return result


if __name__ == "__main__":
    main(sys.argv[1])
