"""Montage Remotion dans un processus séparé (appelé par make_video).

Relit script.json (signature ajoutée comme dans make_video), voice.json et images.json
du dossier du run, écrit video.mp4 et montage.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import motion
from .make_video import SIGNATURE


def main(script_path: str) -> None:
    sp = Path(script_path).resolve()
    work = sp.parent
    script = json.loads(sp.read_text())
    if not script["segments"][-1]["text"].startswith("C'était Asura"):
        script["segments"].append({"text": SIGNATURE, "tone": "pose",
                                   "shots": [{"anime": script["animes"][0], "kind": "poster"}]})
        if script.get("reveal_text"):
            script["reveal_segments"] = int(script.get("reveal_segments", 1)) + 1
    voice = json.loads((work / "voice.json").read_text())
    index = json.loads((work / "images.json").read_text())
    seed = sum(map(ord, script.get("title", ""))) & 0xFFFF
    r = motion.render(script, voice, index, work, work / "video.mp4", seed=seed)
    (work / "montage.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
