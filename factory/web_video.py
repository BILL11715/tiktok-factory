"""Montage @iafortous (depuis le 26/10/2026) : page HTML animée, plan fixe façon « stickers »
(fond crème quadrillé, légendes courtes, emoji 3D, encadrés à ombre franche, transitions en
motif), rendue en MP4 par HyperFrames (Chrome headless + GSAP). Remplace TechShort / Remotion.

Étapes : web/page.html + données (script, voix, emoji) -> repères son lus dans la page ->
mixage voix + musique + bruitages (motion.mix) -> rendu HyperFrames.
Champs du script propres à ce style : segments[].sticker (emoji, obligatoire), .label
(étiquette sous le sticker), .punch (titre-choc en majuscules au moment où il est dit).
"""
from __future__ import annotations

import asyncio
import glob
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
NM = WEB / "node_modules"
EMOJI_DIR = NM / "@lobehub/fluent-emoji-3d/assets"
FONTS = ["@fontsource/montserrat/files/montserrat-latin-900-normal.woff2",
         "@fontsource/montserrat/files/montserrat-latin-800-normal.woff2",
         "@fontsource/inter/files/inter-latin-600-normal.woff2",
         "@fontsource/inter/files/inter-latin-700-normal.woff2",
         "@fontsource/inter/files/inter-latin-800-normal.woff2",
         "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2",
         "@fontsource/jetbrains-mono/files/jetbrains-mono-latin-700-normal.woff2"]


def emoji_file(ch: str) -> Path | None:
    """Fichier Fluent 3D d'un emoji (avec ou sans sélecteur de variante FE0F)."""
    cps = [f"{ord(c):x}" for c in str(ch or "")]
    if not cps:
        return None
    for cand in ("-".join(cps), "-".join(c for c in cps if c != "fe0f"), "-".join(cps + ["fe0f"])):
        f = EMOJI_DIR / f"{cand}.webp"
        if f.exists():
            return f
    return None


def chrome() -> str:
    env = os.environ.get("HYPERFRAMES_BROWSER_PATH")
    if env and Path(env).exists():
        return env
    found = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell"))
    if not found:
        raise RuntimeError("Chrome headless introuvable (lancer : npx hyperframes browser ensure)")
    return found[-1]


def build_page(script: dict, voice: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "fonts").mkdir(exist_ok=True)
    (out / "emo").mkdir(exist_ok=True)
    for f in FONTS:
        shutil.copy(NM / f, out / "fonts" / Path(f).name)
    shutil.copy(NM / "gsap/dist/gsap.min.js", out / "gsap.min.js")
    emo = {}
    for seg in script["segments"]:
        ch = seg.get("sticker")
        if ch and ch not in emo:
            f = emoji_file(ch)
            if f:
                shutil.copy(f, out / "emo" / f.name)
                emo[ch] = f"emo/{f.name}"
    data = json.dumps({"script": script, "voice": voice, "emoji": emo}, ensure_ascii=False).replace("</", "<\\/")
    html = (WEB / "page.html").read_text().replace("__DATA__", data).replace("__DURATION__", f"{voice['duration']:.3f}")
    (out / "index.html").write_text(html)


async def _cues(out: Path) -> list:
    from playwright.async_api import async_playwright  # type: ignore
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=chrome())
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto((out.resolve() / "index.html").as_uri())
        try:
            await pg.wait_for_function("!!window.__cues", timeout=30000, polling=100)
        except Exception:
            raise RuntimeError("page vidéo en erreur : " + " | ".join(errs[:3]))
        c = await pg.evaluate("window.__cues")
        await b.close()
    return c


def snapshot(out: Path, times: list[float], dest: Path) -> list[Path]:
    """Captures de contrôle (vérification visuelle sans attendre le rendu)."""
    async def run() -> list[Path]:
        from playwright.async_api import async_playwright  # type: ignore
        files = []
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path=chrome())
            pg = await b.new_page(viewport={"width": 1080, "height": 1920})
            await pg.goto((out.resolve() / "index.html").as_uri())
            await pg.wait_for_function("!!window.__cues", timeout=30000, polling=100)
            for t in times:
                await pg.evaluate(f"void window.__timelines.root.seek({t}, false)")
                f = dest / f"snap_{t:06.2f}.png"
                await pg.screenshot(path=str(f))
                files.append(f)
            await b.close()
        return files
    dest.mkdir(parents=True, exist_ok=True)
    return asyncio.run(run())


def render(script: dict, voice: dict, work: Path, out_path: Path) -> dict:
    from . import motion
    work, out_path = Path(work).resolve(), Path(out_path).resolve()
    web = work / "web"
    if web.exists():
        shutil.rmtree(web)
    build_page(script, voice, web)
    cues = sorted((round(t, 3), k) for t, k in asyncio.run(_cues(web)) if t >= 0)
    kept, last = [], -1.0
    for t, k in cues:  # un bruitage toutes les 0,12 s au plus
        if t - last >= 0.12:
            kept.append((t, k))
            last = t
    lib = {m["file"]: m for m in json.loads((ROOT / "music" / "library.json").read_text())}
    music = dict(lib.get(f"{script.get('music', 'pote')}.mp3") or lib["pote.mp3"])
    music["offset"] = music.get("start", 0)
    mix = motion.mix(Path(voice["path"]), music, voice["duration"], kept, web, voice["timeline"][0]["slot_end"])
    shutil.move(str(mix), web / "mix.m4a")
    env = {**os.environ, "HYPERFRAMES_BROWSER_PATH": chrome(), "DO_NOT_TRACK": "1"}
    workers = os.environ.get("TF_HF_WORKERS", str(max(1, min(4, os.cpu_count() or 2))))
    r = subprocess.run(["node", str(NM / "hyperframes/bin/hyperframes.mjs"), "render", "-o", str(out_path), "-w", workers, "-q", "looks"],
                       cwd=str(web), env=env, capture_output=True, text=True)
    if r.returncode != 0 or not out_path.exists():
        raise RuntimeError("rendu HyperFrames en échec : " + (r.stderr or r.stdout)[-800:])
    return {"path": str(out_path), "duration": voice["duration"], "sfx": len(kept),
            "music": {k: music[k] for k in ("file", "offset") if k in music}, "engine": "hyperframes (stickers)"}
