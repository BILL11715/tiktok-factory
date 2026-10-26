# Runbook @iafortous (1 exécution = 1 vidéo)

Objectif : produire UNE vidéo TikTok pour @iafortous (IA pour tous + SEO Radius), la déposer en
**brouillon** dans Buffer et l'enregistrer dans Notion. Bill n'est pas là : ne pose aucune
question, décide et continue. Ne lis que ce qui est listé ici (pas d'exploration du code).

## Constantes
- Repo : BILL11715/tiktok-factory (branche main)
- Buffer : organisation "My organization" `6ab6760af0590c0d7de161a1`, canal TikTok iafortous `6ac97f406a5c39ccb66a156b`
- Notion data source "Historique des vidéos" : `collection://a67557a3-702e-448d-a4cd-3d3904d45deb`
- Fuseau : Europe/Paris. Créneaux : 08:00, 12:00, 17:00, 19:00, 22:00.

## Étapes
1. **Repo** : `add_repo` (owner BILL11715, repo tiktok-factory, access push) puis
   `git clone --depth 20 https://github.com/BILL11715/tiktok-factory /home/claude/tiktok-factory`
   (timeout long). git config user.name "Bill Hounmenou", user.email "yanndevfrance04@gmail.com".
2. **Voix** : la voix du compte est **Gemini TTS « Kore »** (voix féminine Google, choisie par Bill le
   26/10/2026), activée par `TF_GEMINI=1`. Secours automatique, dans l'ordre : Kyutai « estelle »
   (`TF_KYUTAI=1`, ancienne voix du compte), puis Fish Audio, puis Piper. Jamais de voix mélangées.
   Le message de la tâche planifiée contient la clé Gemini et la clé Fish Audio de Bill. Écris chacune
   seule dans son fichier AVANT le setup :
   `umask 077; printf '%s' '<clé Gemini>' > /tmp/tf-gemini-key; printf '%s' '<clé Fish>' > /tmp/tf-fish-key`.
   (Si le message ne contient pas de clé Gemini, n'écris que la clé Fish : la vidéo partira en estelle.)
   Ne recopie JAMAIS ces clés ailleurs : ni dans le repo (public), ni dans un commit, ni dans
   Notion, Buffer ou ton message de fin.
   **Installation en arrière-plan tout de suite** :
   `cd /home/claude/tiktok-factory && TF_GEMINI=1 TF_KYUTAI=1 nohup bash setup.sh > /tmp/tf-setup.out 2>&1 &`
   (environ 10 à 15 min : la voix de secours télécharge PyTorch). La ligne "[setup] voix Gemini Kore
   prête" doit apparaître. Sinon la vidéo part en estelle ("[setup] voix Kyutai estelle prête") : recopie
   la ligne "[setup] Gemini ..." dans les Notes Notion et dans ton message de fin (elle dit si le réseau
   bloque l'API ou si la clé est refusée). Si `result.json` contient un `voice_fallback` non vide, la
   voix a changé pendant le rendu : recopie aussi cette raison (elle ne contient jamais la clé).
3. **Créneau** : heure actuelle (outil current_time). Le créneau est le prochain à venir parmi
   08:00, 12:00, 17:00, 19:00, 22:00. Si `history_ia.jsonl` a déjà une vidéo pour ce jour et ce
   créneau (champ `slot` = "AAAA-MM-JJ HH:MM"), prends le créneau libre suivant (après 22:00 :
   le lendemain 08:00). Le pilier dépend du créneau (tableau de EDITORIAL_IA.md).
   La tâche planifiée tourne à 07:13, 09:13, 11:13, 13:13 et 15:13 : les 5 brouillons du jour
   doivent être prêts avant 18h, d'où ce saut au premier créneau libre.
4. **Contexte** : lis `EDITORIAL_IA.md`, `AMELIORATIONS_IA.md` (règles apprises, à appliquer) et les
   25 dernières lignes de `history_ia.jsonl`.
   Choisis l'angle et le sujet : pas le même angle 2 fois dans la journée, pas le même sujet sur
   7 jours, varie les formats.
   - Pilier IA : 2 à 4 recherches web pour un sujet frais et vrai (nouveauté Claude, skill ou
     repo GitHub utile, outil gratuit). Pour un repo ou un outil : ouvre la page (WebFetch) et
     vérifie le nom exact, ce qu'il fait, l'URL, et les étoiles si tu les cites. Rien d'inventé.
   - Pilier SEO Radius : appuie-toi sur les faits de EDITORIAL_IA.md (1 recherche max si besoin
     de vérifier un prix sur seoradius.fr).
5. **Script** : écris `runs/ia/<AAAA-MM-JJ_HHMM>/script.json` (HHMM = créneau, ex. 2026-10-11_0800)
   au format ci-dessous, puis `python3 -m factory.make_tech --lint runs/ia/<stamp>/script.json`
   et corrige jusqu'à "OK". Relis-le à voix haute mentalement : naturel, oral, zéro jargon.
6. **Rendu** : attends la fin du setup (`grep -q "\[setup\] OK" /tmp/tf-setup.out`, toutes les
   30 s, max 22 min), puis
   `cd /home/claude/tiktok-factory && nohup /tmp/tf-venv/bin/python -m factory.make_tech runs/ia/<stamp>/script.json > /tmp/ia-render.out 2>&1 &`
   (le rendu prend 15 à 20 min : lance-le en arrière-plan dès le départ, puis vérifie toutes les
   60 s que `runs/ia/<stamp>/result.json` existe ou qu'une erreur apparaît dans /tmp/ia-render.out,
   max 35 min).
7. **Vérification visuelle rapide** : extrais 3 images (`ffmpeg -ss 2`, milieu, fin) de
   `runs/ia/<stamp>/video.mp4` et regarde-les avec Read. Texte qui déborde ou scène vide :
   corrige le script et relance une fois.
   **Audit automatique** : `/tmp/tf-venv/bin/python -m factory.audit runs/ia/<stamp>` (débit, prononciation,
   silence d'ouverture, durée, mots mal prononcés). Si une ALERTE vient d'un prix, d'un nombre ou d'un
   mot précis mal prononcé : ajoute une écriture phonétique dans le lexique de la voix utilisée
   (`config/prononciation_gemini.json` si voice_engine = gemini, `config/prononciation.json` si kyutai) ou
   reformule la phrase, puis relance le rendu UNE fois (pas plus) et refais l'audit. Avec Gemini, chaque
   rendu consomme une requête du quota gratuit du jour : ne relance que pour une vraie faute. Recopie la ligne
   "AUDIT ..." et les alertes restantes dans les Notes Notion.
8. **Publication fichier** : `git add videos/ia runs/ia/<stamp>/script.json runs/ia/<stamp>/result.json runs/ia/<stamp>/audit.json audits_ia.jsonl config/prononciation.json config/prononciation_gemini.json`,
   commit "ia <stamp> <titre court>", `git pull --rebase -q origin main`, `git push origin main`.
   Vérifie que `raw_url` (result.json) répond 200 avec curl (3 essais, 10 s d'écart).
9. **Buffer** : `create_post` avec le channelId ci-dessus, `saveToDraft: true`,
   `mode: "customScheduled"`, `dueAt` = le créneau (offset Europe/Paris correct, ex.
   2026-10-11T08:00:00+02:00), `schedulingType: "automatic"`,
   text = caption + "\n\n" + hashtags séparés par des espaces,
   assets = [{video: {url: raw_url, metadata: {title: title, thumbnailOffset: 0}}}] (la 1re image = l'affiche de couverture),
   metadata = {tiktok: {title: <hook_text sans emoji, 90 car. max>}}.
   Si Buffer refuse à cause de la limite de posts du plan gratuit : ne supprime rien, mets
   Statut "Généré" dans Notion avec la note "Limite Buffer atteinte, vidéo prête à poster
   (Lien vidéo)", et continue.
10. **Notion** : page dans la data source avec Titre, Compte "@iafortous", Pilier ("SEO Radius" |
    "IA vulgarisée"), Format (Tuto / méthode | Outil / repo | Actu IA | Mythe vs réalité |
    Top / classement), Statut "Brouillon Buffer", Date de création (datetime Paris), Hook,
    Script (texte intégral), Hashtags, Lien vidéo (raw_url), Lien Buffer
    (https://publish.buffer.com/post/<id>), Sources visuels (liens consultés pour le sujet),
    Voix ("Gemini" si voice_engine = gemini, "Kyutai" si kyutai, "Fish Audio" si fish, "Clone Bill" si clone, sinon "Piper"),
    Durée (s), Notes (créneau + angle). Laisse "Anime" vide.
11. **Historique** : ajoute une ligne JSON à `history_ia.jsonl`
    `{"stamp","slot","pillar","angle","format","topic","title","hook","buffer_id","notion_url","raw_url","voice","duration"}`,
    commit + push (pull --rebase avant).
12. **Nettoyage** : pour chaque ligne de `history_ia.jsonl` de plus de 3 jours dont le fichier
    `videos/ia/...` existe encore, regarde le post Buffer (`get_post`). Supprime la vidéo
    (`git rm`) UNIQUEMENT si le statut est `sent` ou si le post n'existe plus ; mets alors le
    Statut Notion à "Publié" si sent. Jamais pour un brouillon ou un post programmé. Pas de force push.
13. **Amélioration continue** (une vidéo sur deux : quand le nombre de lignes de `history_ia.jsonl`
    est pair) : relis les 10 dernières lignes de `audits_ia.jsonl`, la ligne "MOTS MAL COMPRIS SUR
    PLUSIEURS VIDÉOS" de l'audit et les 3 images de l'étape 7. Puis mets à jour `AMELIORATIONS_IA.md` :
    - « Règles apprises » : ajoute ou précise une règle seulement si un problème revient sur 2 vidéos
      ou plus (débit, prononciation, longueur, lisibilité d'une scène, hook) ; 15 règles maximum,
      fusionne plutôt qu'empiler, supprime une règle devenue inutile ;
    - lexique de la voix utilisée (`config/prononciation_gemini.json` pour Gemini, `config/prononciation.json`
      pour Kyutai) : écriture phonétique pour chaque mot mal compris 2 fois ou plus avec cette voix ;
    - « Pistes pour Bill » : ce qui demanderait de changer le code ou les réglages (tu ne touches ni au
      code, ni aux seuils, ni à ce runbook) ;
    - « Journal » : une ligne datée (constat + action), 20 lignes maximum.
    Commit "ia amélioration <date>" + push (pull --rebase avant).
14. **Fin** : message court (créneau, pilier, titre, durée, voix, débit et prononciation de l'audit,
    lien Buffer). En cas d'échec : ligne Notion avec Statut "Échec" et l'erreur dans Notes.

## Format de script.json
```json
{
  "title": "Trouver ses premiers clients en SEO local",
  "theme": "seo",
  "pillar": "seo-radius",
  "format": "methode",
  "music": "pote",
  "cover": {"text": "Tes clients sont en page 2", "highlight": ["page"], "emoji": "🔎", "sub": "la méthode"},
  "hook_text": "Freelance SEO ? Tes clients sont déjà sur Google, page 2.",
  "segments": [
    {"text": "Freelance SEO ? Tes clients sont déjà sur Google, page 2.", "emphasis": ["page"]},
    {"text": "Le plombier qui n'apparaît pas dans les résultats perd des appels tous les jours.",
     "visual": {"kind": "search", "query": "plombier Lyon 7", "results": [{"name": "SOS Eau Lyon", "note": "site lent", "rating": "3,9"}], "pick": 0}},
    {"text": "...", "visual": {"kind": "list", "title": "La méthode", "items": ["Un métier + une ville", "Repérer les retards"], "at": ["métier", "repérer"]}},
    {"text": "...", "stamp": "3 heures"}
  ],
  "caption": "Tes futurs clients SEO sont en page 2 de Google 👀 (outil en bio)",
  "hashtags": ["#seo", "#seolocal", "#freelance", "#prospection"]
}
```
Règles (le pipeline refuse sinon) :
- `theme` : "seo" (pilier SEO Radius) ou "ia" (pilier IA). `music` : pote | hype | mystere.
- `cover` (affiche de couverture, visible sur le profil TikTok) : `text` 3 à 6 mots qui donnent envie de
  cliquer (bénéfice ou tension, pas le titre plat), `highlight` = 1 mot clé de `text`, `emoji` = 1 emoji
  qui illustre le sujet, `sub` = 2 à 5 mots facultatifs (ex. "la méthode en 3 étapes", "gratuit").
- `hook_text` = 1er segment, 14 mots max, écrit en gros à l'écran pendant qu'il est dit.
  Pas de `visual` sur le 1er segment.
- 1 250 à 1 650 caractères, viser 1 300 à 1 550 (environ 80 à 95 s). 12 à 16 segments de 1 à 2 phrases,
  260 caractères max chacun.
- Au moins 8 segments avec `visual` (une scène toutes les 5 à 8 s, jamais 2 fois le même type d'affilée). Un segment sans `visual`
  garde la scène précédente. Types : voir EDITORIAL_IA.md.
- `list.at` : un mot réellement prononcé pour chaque élément, dans l'ordre de la voix.
- Textes courts dans les scènes (une ligne de liste = 5 mots max ; réponse de chat = 300 car. max).
- Zéro appel à l'abonnement, zéro signature. Pas de tiret cadratin.
- `sfx: true` sur 1 ou 2 révélations (transition flash + impact).
- Aucune balise dans le texte (ni `[excited]`, ni `<laugh>` ou `<short pause>`) : elles s'afficheraient
  dans les sous-titres. L'intonation vient de la ponctuation : phrases courtes, points d'exclamation et
  questions réels (la voix Gemini les joue bien). Chaque segment est lu sur sa propre ligne : la voix
  marque une petite respiration entre deux segments.
- `caption` : 1 phrase + emoji, mentionne "lien en bio" si SEO Radius ; liens GitHub en clair pour
  le pilier IA. 4 à 6 hashtags dont #ia ou #seo.
