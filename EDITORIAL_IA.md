# Charte éditoriale @iafortous (IA pour tous + SEO Radius)

## Mission
Rendre l'IA, la data et le code accessibles à des gens qui ne sont pas développeurs : la caissière,
l'artisan, l'étudiant, le freelance. Chaque vidéo doit laisser une chose concrète à faire ou à
retenir. Et faire grandir une communauté autour de SEO Radius (seoradius.fr), l'outil de
prospection SEO de Bill.

## Règle d'or : la valeur, pas la demande
- **Jamais** d'appel à l'abonnement, de "like", de "follow", ni de signature de fin. Le pipeline
  refuse le script s'il en contient. On donne tellement de valeur que la personne s'abonne d'elle-même.
- Une fin forte à la place : la dernière astuce, une question ouverte qui appelle un commentaire
  ("dis-moi ce que tu trouves"), ou une promesse de la suite ("la partie avancée, c'est demain").

## Les deux piliers (5 vidéos par jour)
Créneaux et piliers fixes (au moins 3 SEO Radius par jour) :

| Créneau | Pilier |
|---|---|
| 08:00 | SEO Radius |
| 12:00 | IA vulgarisée |
| 17:00 | SEO Radius |
| 19:00 | IA vulgarisée |
| 22:00 | SEO Radius |

### Pilier SEO Radius (theme "seo", accent cyan)
Cible : freelances SEO, consultants, petites agences, et ceux qui veulent vivre du SEO.
Angles à faire tourner (pas 2 fois le même dans la journée) :
1. **Trouver des clients** : méthodes de prospection locale, comment repérer une entreprise mal
   référencée, quoi dire au premier contact, comment fixer ses prix, relances.
2. **Démo de l'outil** : une seule fonctionnalité par vidéo, sur un cas concret
   (analyse SERP, score d'opportunité /100, réservation exclusive, benchmark IA, email IA, CRM).
3. **Astuce SEO local** : une action concrète (fiche Google, avis, vitesse du site, pages par ville),
   et SEO Radius cité comme le moyen de trouver les entreprises qui en ont besoin.
4. **Coulisses / build in public** : comment Bill a construit SEO Radius avec l'IA sans équipe.

Faits sur SEO Radius (ne rien inventer au-delà) :
- Outil de prospection SEO pour freelances, consultants et petites agences.
- On tape un secteur et une ville (ou un rayon). L'outil analyse jusqu'à 50 résultats Google,
  écarte annuaires et grandes plateformes, et classe les entreprises restantes.
- Score d'opportunité /100 (écart entre la position actuelle et le potentiel : autorité, trafic,
  backlinks, position). Les métriques sont des **estimations** (le dire quand on cite un chiffre).
- Réservation exclusive : le prospect disparaît des listes des autres utilisateurs 7 à 30 jours selon le plan.
- Benchmark concurrentiel généré par IA (à relire avant envoi). Email de prospection IA avec mini
  audit (à partir de Starter). CRM : réservé, contacté, en attente, gagné.
- Plans : Découverte gratuit (10 recherches, 5 réservations, sans carte), Starter 19 €/mois,
  Pro 49 €/mois, Agency 99 €/mois. Vérifier sur https://seoradius.fr avant de citer un prix.
- Inscription : seoradius.fr (dire "lien en bio" dans la légende, pas dans la voix).

### Pilier IA vulgarisée (theme "ia", accent vert citron)
Cible : grand public curieux, zéro jargon. Angles :
1. **Astuce Claude / LLM** : une façon d'utiliser Claude ou un LLM qui change la vie au quotidien
   (rédiger, résumer un PDF, préparer un entretien, créer un petit outil sans coder).
2. **Outil ou repo GitHub utile** : un projet open source, une skill Claude, un outil gratuit.
   Toujours avec le lien exact (vérifié) dans la scène "card" et dans la légende.
3. **Actu IA expliquée** : une nouveauté récente (Claude, modèles, fonctionnalités), ce que ça
   change concrètement pour quelqu'un de normal. Vérifier par recherche web, dater l'info.
4. **Mythe vs réalité / concept expliqué** : c'est quoi un LLM, un prompt, une hallucination,
   un agent, une API, la data. Une image simple tirée du quotidien.
5. **Coder sans être dev** : construire un mini outil avec l'IA, étape par étape.

## Ton et écriture
- Tutoiement, phrases courtes, langage oral, comme un pote qui s'y connaît.
- Exemples du quotidien (courses, boulot, factures, CV). Un seul mot technique par vidéo,
  expliqué tout de suite.
- Honnête : si un outil a une limite, le dire. Pas de promesse magique, pas de "révolutionnaire".
- Pas de tiret cadratin. Tournures interdites : voir `factory/make_tech.py` (BANNED).
- Hook (1re phrase, 14 mots max) : une tension ou un bénéfice concret.
  Exemples : "Tu paies ChatGPT mais tu l'utilises comme Google.",
  "Ce repo GitHub gratuit remplace un abonnement à 20 euros.",
  "Freelance SEO ? Tes clients sont déjà sur Google, page 2."
- Durée : 1 450 à 1 750 caractères de texte parlé (environ 65 à 80 s). Jamais moins d'une minute.

## Scènes disponibles (motion design TechShort)
Une scène toutes les 8 à 12 s (5 minimum). Choisir celle qui MONTRE ce qui est dit :
- `title` : phrase clé en gros (`kicker`, `text`, `highlight`, `sub`).
- `chat` : échange avec une IA (`name`, `user`, `assistant`). Idéal pour montrer un prompt.
- `terminal` : commandes et résultats (`title`, `lines`: [{"cmd"}, {"out"}]).
- `code` : extrait de code qui s'écrit (`file`, `code`, `highlight` = n° de lignes).
- `card` : outil ou repo (`emoji`, `owner`, `name`, `desc`, `tags`, `stars`, `price`, `url`).
- `list` : étapes ou top (`title`, `items`, `at` = un mot dit au moment de chaque élément, dans l'ordre).
- `stat` : chiffre animé (`value`, `prefix`, `suffix`, `label`, `source`).
- `compare` : avant/après (`left`/`right` : `title`, `items`).
- `search` : recherche locale avec carte et résultats (`query`, `results`: [{name, note, rating}], `pick`).
- `shot` : capture d'écran fournie dans le dossier du run (`src`, `title`, `scroll`).
`stamp` (segment) : un mot tamponné en gros, 1 ou 2 par vidéo. `emphasis` : 1 ou 2 mots en couleur.
