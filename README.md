# tiktok-factory

Production automatique de vidéos TikTok anime/manga (@the.asura8).

Chaîne : script écrit par l'agent (Claude, tâche planifiée) -> visuels officiels (Kitsu, Jikan) -> voix (clone de Bill via Chatterbox, secours Piper) -> montage 1080x1920 (FFmpeg, sous-titres mot par mot, musique Pixabay via OpenMontage) -> MP4 dans `videos/` -> brouillon Buffer -> historique Notion.

- `AGENT_RUN.md` : procédure suivie à chaque exécution.
- `EDITORIAL.md` : charte éditoriale.
- `python -m factory.make_video runs/<stamp>/script.json` : rendu local.
