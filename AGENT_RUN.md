# Runbook de l'agent planifié (1 exécution = 1 vidéo)

Objectif : produire UNE vidéo TikTok pour @the.asura8, la déposer en **brouillon** dans Buffer
et l'enregistrer dans Notion. Économiser les crédits : ne lire que ce qui est listé ici, pas
d'exploration du code, pas de recherche web sauf pour une théorie/actu (2 recherches max).
Bill n'est pas là pendant le run : ne pose aucune question, décide et continue.

## Constantes
- Repo : BILL11715/tiktok-factory (branche main)
- Buffer : organisation "My organization" 6ab6760af0590c0d7de161a1, canal TikTok the.asura8 `6ab84079ea19ca0bdefacbee`
- Notion data source Historique : `collection://a67557a3-702e-448d-a4cd-3d3904d45deb`
- Fuseau : Europe/Paris

## Étapes
1. **Repo** : appelle `add_repo` (owner BILL11715, repo tiktok-factory, access push) puis
   `git clone --depth 20 https://github.com/BILL11715/tiktok-factory /home/claude/tiktok-factory`
   (timeout long). Config git : user.name "Bill Hounmenou", user.email "yanndevfrance04@gmail.com".
2. **Installation en arrière-plan tout de suite** :
   `cd /home/claude/tiktok-factory && nohup bash setup.sh > /tmp/tf-setup.out 2>&1 &`
   (ça tourne pendant que tu écris le script).
3. **Contexte** : lis `EDITORIAL.md` et les 30 dernières lignes de `history.jsonl`.
   Donne-toi l'heure actuelle (outil current_time) pour savoir le créneau (12h30, 18h30 ou 21h30,
   le plus proche). Choisis le format autorisé pour ce créneau en respectant la rotation
   (pas 2 fois le même format dans la journée, pas le même anime sur 48 h, équilibre de la semaine).
   Si `config/weights.json` existe, il ajuste la répartition des formats.
4. **Script** : écris `runs/<AAAA-MM-DD_HHMM>/script.json` (heure de Paris) au format ci-dessous.
   Relis-le à voix haute mentalement avec les règles anti-IA de EDITORIAL.md et corrige.
5. **Rendu** : attends la fin du setup (`grep -q "\[setup\] OK" /tmp/tf-setup.out`, vérifier
   toutes les 30 s, max 15 min), puis
   `cd /home/claude/tiktok-factory && /tmp/tf-venv/bin/python -m factory.make_video runs/<stamp>/script.json`
   (timeout 10 min, relancer une fois en arrière-plan + attente si trop long).
   Si le script est refusé par le contrôle anti-IA, corrige les tournures signalées et relance.
6. **Publication fichier** : `git add videos runs/<stamp>/script.json runs/<stamp>/result.json`,
   commit "video <stamp> <anime>", `git pull --rebase -q origin main`, `git push origin main`.
   Vérifie que `raw_url` (dans result.json) répond 200 avec curl (réessaie 3 fois, 10 s d'écart).
7. **Buffer** : `create_post` avec channelId ci-dessus, `saveToDraft: true`,
   `mode: "customScheduled"`, `dueAt` = l'heure du créneau aujourd'hui (12:30, 18:30 ou 21:30,
   offset Europe/Paris correct, ex. 2026-09-28T18:30:00+02:00 ; si l'heure est déjà passée,
   prends le créneau libre suivant), `schedulingType: "automatic"`, text = caption + "\n\n" + hashtags séparés par des espaces,
   assets = [{video: {url: raw_url, metadata: {title: title}}}],
   metadata = {tiktok: {title: <hook_text sans emoji, 90 car. max>}}.
   Note l'id du post.
8. **Notion** : crée une page dans la data source Historique avec : Titre, Compte "@the.asura8",
   Anime, Format (Anecdote | Top / classement | Théorie | Recommandation | Texte animé ;
   citation -> Anecdote), Statut "Brouillon Buffer", Date de création (datetime Paris),
   Hook, Script (texte intégral des segments), Hashtags, Lien vidéo (raw_url),
   Lien Buffer (https://publish.buffer.com/post/<id>), Sources visuels (result.sources),
   Voix ("Clone Bill" si voice_engine = clone sinon "Piper"), Durée (s), Notes (créneau).
9. **Historique local** : ajoute une ligne JSON à `history.jsonl`
   `{"stamp","slot","format","anime","title","hook","buffer_id","notion_url","raw_url","voice"}`,
   commit + push (pull --rebase avant).
10. **Nettoyage du repo public** : pour chaque ligne de `history.jsonl` de plus de 3 jours
    dont le fichier `videos/...` existe encore, regarde le post Buffer (`get_post`). Supprime la
    vidéo (`git rm`) UNIQUEMENT si le statut est `sent` ou si le post n'existe plus. Jamais pour un
    brouillon, un post programmé ou en erreur. Pas de force push. Mets à jour le Statut Notion
    ("Publié" si sent).
11. **Fin** : un message court (titre, format, lien Buffer). En cas d'échec à n'importe quelle
    étape : crée quand même la ligne Notion avec Statut "Échec" et l'erreur dans Notes.

## Format de script.json
```json
{
  "title": "Reco Solo Leveling - le chasseur le plus nul",
  "format": "reco | theorie | top | anecdote | citation",
  "tone": "pote | conteur | hype | pose",
  "music": "pote | mystere | hype | hype2 | triste",
  "animes": ["Solo Leveling"],
  "hook_text": "Le chasseur le plus nul du monde... jusqu'au jour où",
  "spoiler": false,
  "spoiler_label": "chapitre 1160",
  "segments": [
    {
      "text": "Phrase(s) dite(s) par Bill, 1 à 3 phrases, 260 caractères max.",
      "shots": [{"anime": "Solo Leveling", "kind": "character", "character": "Jinwoo"}],
      "emphasis": ["mots", "à", "surligner"],
      "overlay": "#3",
      "sfx": true
    }
  ],
  "reveal_text": "Solo Leveling",
  "reveal_segments": 1,
  "caption": "Il était le plus faible de tous 😭 tu connaissais ?",
  "hashtags": ["#anime", "#manga", "#animefr", "#sololeveling", "#recommandationanime"]
}
```
- `animes` : noms tels que cherchés sur Kitsu (titre anglais ou romaji courant). Pour un top
  multi-animes, liste-les tous et mets le bon `anime` dans chaque shot.
- `shots` optionnel : `kind` = character (avec `character`), wide (captures/bannières), poster, any.
  Sans shots, le pipeline choisit des images variées (un plan toutes les 2-4 s).
- `emphasis` : 1 ou 2 mots clés par segment (en jaune).
- `overlay` : uniquement pour les tops ("#5"..."#1").
- `sfx` : true seulement sur 2-4 révélations par vidéo.
- `reveal_text` : pour une reco (nom de l'anime en fin), sinon omettre.
- La signature est ajoutée automatiquement, ne l'écris pas.
- Découpe en 8 à 14 segments.
