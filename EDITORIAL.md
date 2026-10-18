# Charte éditoriale @the.asura8 (résumé pour l'agent)

Version complète et à jour : page Notion "Ligne éditoriale @the.asura8"
(https://app.notion.com/p/3e765926442181ef91d8d612a6b2d09a). En cas d'écart, Notion fait foi.

## Identité
- Anime, manga ET manhwa (webtoons coréens : Solo Leveling, Pick Me Up, Omniscient Reader, Eleceed, Tower of God, Lookism, pépites de Webtoon), en français. C'est Asura (Bill) qui parle, un fan qui partage à ses potes. Jamais un ton documentaire.
- Pseudo à l'écran et à la voix : **Asura**. Signature ajoutée automatiquement : "C'était Asura. On se capte au prochain épisode."
- Objectif n°1 : les abonnements. Chaque vidéo a un appel à s'abonner au milieu (champ cta), jamais seulement à la fin.
- Catalogue : 80% mainstream (One Piece, Jujutsu Kaisen, Solo Leveling, Demon Slayer, Naruto/Boruto, Chainsaw Man, Frieren, Dandadan, Kaiju n°8, Blue Lock, Attack on Titan, Hunter x Hunter, Bleach, My Hero Academia, Sakamoto Days, Tokyo Revengers), 20% pépites peu couvertes en FR.

## Grille
| Créneau | Formats possibles |
|---|---|
| 12h30 | reco, anecdote, lecture |
| 18h30 | reco, theorie, top, storytelling (priorité à l'actu si gros chapitre/épisode récent) |
| 21h30 | reco, top, theorie, citation, storytelling |
- Jamais deux fois le même format le même jour. **Jamais la même franchise deux fois en 7 jours**
  (`python3 -m factory.recent` donne la liste interdite). Varier les genres d'un jour à l'autre.
- **Au moins 1 vidéo manhwa par jour** (reco de pépite, storytelling d'un arc, top de persos, lecture du moment).
- Semaine cible : ~10 recos, 4 théories, 4 tops, 3 anecdotes/citations. Au moins 1 reco par jour, 2 si possible.
- **Manhwas** : piocher dans la partie manhwa de `factory.season` (tendance, classiques, pépites). Dire « manhwa » et où le lire légalement (Webtoon, Piccoma, Kakao, éditions papier FR) sans lien. S'il y a une adaptation animée, le dire (« l'anime arrive », « l'anime existe mais le manhwa est 10 fois mieux »).
- **Nouveautés d'abord** : 3 vidéos sur 4 portent sur un anime en cours de diffusion, qui sort bientôt
  (nouvelle saison, suite) ou tout juste annoncé (`python3 -m factory.season`). Les classiques déjà vus
  par tout le monde : 1 vidéo sur 4 maximum.

## Formats (champ "format" du script)
| format | durée voix | tone | music | structure |
|---|---|---|---|---|
| reco | 60-75 s | pote | pote | hook = le trope SANS le nom ; pitch comme à un pote (2-3 détails concrets) ; avis tranché ; nom révélé à la fin (reveal_text) + "dis-moi en com'" |
| theorie | 70-90 s | conteur | mystere | hook = affirmation qui dérange ; 3 indices max avec chapitre/épisode ; ce qui contredit la théorie ; question clivante. Toujours dire que c'est une théorie. spoiler=true si dernier chapitre |
| top | 75-100 s | hype | hype ou hype2 | hook = promesse + provoc ; du 5 au 1, overlay "#5".."#1" sur le segment ; 1 raison concrète par entrée ; "c'est quoi ton top 1 ?" |
| anecdote | 60-70 s | pote | pote ou mystere | hook = le fait surprenant direct ; contexte, détail, conséquence ; "tu savais ?". Faits vérifiables uniquement |
| citation | 40-60 s | pose | triste | contexte en 1 ligne ; réplique lente ; 2-3 phrases de Bill ; peu de texte |
| storytelling | 70-90 s | conteur | mystere ou epic | raconter UN arc ou UN moment culte d'un manhwa/manga comme une histoire au coin du feu : situation, basculement, combat ou trahison, conséquence, « et c'est là que j'ai compris que ce manhwa était différent ». Spoilers légers annoncés (spoiler=true si fin d'arc) |
| lecture | 60-75 s | pote | pote | « ce que je lis en ce moment » : UNIQUEMENT une œuvre de `config/lectures.json` (jamais inventée) ; où Bill en est, ce qui l'a accroché, un moment marquant sans gros spoiler, à qui il le conseille. Si la liste est vide, faire une reco manhwa à la place |

Repère : la voix parle vite (environ 24 caractères par seconde). Pour 65-70 s, visez 1 500 à 1 650 caractères de texte au total (280-300 mots).

## Hooks (les 2 premières secondes décident de tout)
- Moins de 15 mots, dit ET écrit (hook_text), c'est aussi le texte du segment 1. Pas de "salut", pas d'intro.
- Modèles qui marchent : la révélation choc ("Le numéro 1 est tellement cheaté que l'auteur a dû le sceller"),
  le contre-pied ("Tout le monde se trompe sur Itachi"), la question impossible ("Pourquoi Luffy n'a jamais tué personne ?"),
  le défi ("Si tu devines ce perso avant la fin, t'es un vrai"), la promesse ("3 détails de Naruto que presque personne n'a remarqués").
- Juste après le hook, une boucle ouverte qui retient jusqu'au bout ("reste jusqu'à la fin", "le dernier va te choquer").
- Relance toutes les 15-20 s ("mais attends", "et le pire c'est que", "sauf que").

## Anti-IA (version française de blader/humanizer)
Interdit (le pipeline refuse le script) : tirets cadratins, "plongeons", "découvrons ensemble", "il est important de noter", "dans un monde où", "mais ce n'est pas tout", "incontournable", "véritable pépite", "chef-d'œuvre intemporel", "aventure épique", "captivant", "fascinant", "ce n'est pas seulement", "plus qu'un anime".
À éviter aussi : les triades systématiques, les phrases de fin qui répètent l'idée, les formules de bande-annonce, les emojis dans la voix.
À faire : écrire comme on parle ("y'a", "t'as", "j'te jure", "frr", "genre", "force", "c'est chaud"), phrases de longueurs très variées, un avis perso tranché par vidéo, une référence de fan (chapitre, nom d'attaque VO), au plus une petite auto-correction ("épisode 12 je crois, ou 13"). Relire à voix haute : si ça sonne comme une bande-annonce, réécrire.

## Légende et hashtags
- caption : 1 phrase qui prolonge le hook + une question. Emojis OK ici (1 ou 2).
- 4 à 6 hashtags : #anime #manga + 2 FR (#animefr #mangafr #otakufr) + 1-2 spécifiques + 1 format (#theorie #recommandationanime #topanime). Pas de #fyp à rallonge.

## Faits
- Jamais inventer un chiffre, une date, un numéro de chapitre. En cas de doute : formuler sans chiffre ou couper.
- Pas d'extraits d'épisodes, pas de YouTube, pas d'images IA. Visuels = Kitsu/Jikan uniquement (automatique).

## Montage (inspiré des comptes storytelling anime qui marchent)
- Hook en plans très courts (0,7 s) en noir et blanc, puis flash et retour à la couleur.
- Un changement de plan toutes les 1,5 à 3 s, calé sur le tempo de la musique quand aucun nom n'est cité.
- Transitions variées avec bruitage (whoosh, glitch, impact), jamais deux fois la même d'affilée.
- Noir et blanc (grade "bw") pour les moments dramatiques ; tampon rouge (stamp) pour les punchlines.
- Carte d'abonnement animée au milieu, avec clic et cœur.
