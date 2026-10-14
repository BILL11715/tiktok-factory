# Amélioration continue @iafortous

Fichier tenu par l'agent (étape 13 du runbook AGENT_RUN_IA.md), lu avant chaque script (étape 4).
L'agent peut modifier ce fichier et `config/prononciation.json`, jamais le code ni les seuils.

## Règles apprises (15 maximum, les plus utiles en premier ; fusionner plutôt qu'empiler)
1. Voix posée et claire avant tout (retour de Bill, 12/10) : phrases courtes, une idée par phrase,
   pas d'enchaînement de chiffres. Débit cible 23 à 25,5 caractères prononcés par seconde (audit).
2. Prix et nombres : écrire `19 €/mois`, `49 €`, `30 %`, `81/100` ; le pipeline les dit en toutes
   lettres. Jamais plus de 2 chiffres dans la même phrase, sinon l'oreille décroche.
3. La voix démarre 0,6 s après l'affiche de couverture : ne pas raccourcir le hook pour compenser.
4. Pas de balises d'émotion : l'intonation vient de la ponctuation (questions, exclamations réelles).
5. Éviter de commencer une phrase (surtout le hook) par « Ton » + nom : mal compris sur 2 vidéos du 12/10
   (« ton client » entendu « donc il y en », « ton entretien » entendu « son » / « dans l »). Préférer « Tu as un
   entretien demain ? » ou placer le mot après le verbe.

## Pistes pour Bill (changements de code proposés, à valider par lui)
- Audit : comparer la transcription au texte écrit du script, pas à la graphie phonétique du lexique.
  Aujourd'hui « PDF » (dit « p d f ») et « PowerPoint » (dit « paoueur pointe ») comptent comme des
  écarts alors qu'ils sont bien entendus, ce qui fait passer la prononciation sous 93 % à tort.
- Audit : ignorer les homophones (« rends » / « rend », « ton » / « t'on ») dans les mots mal compris.

## Journal (1 ligne par revue, la plus récente en haut, 20 lignes maximum)
- 2026-10-14 (12:00) : « IA » mal compris sur 2 vidéos (13/10 « aya par », 14/10 « il y a », « haies ») : ajouté au
  lexique (« I A »), avec Jan (« djanne ») et Linux (« linuxe »). Au 2e rendu, les trois sont bien entendus, mais la
  prononciation tombe de 91 % à 89 % car l'audit compare à la graphie phonétique (piste déjà notée). Débit 24,3 car./s.
- 2026-10-13 (22:00) : sans alerte au 1er rendu (débit 24,0 car./s, prononciation 94 %, 88 s), règle 5 tenue.
  Sur les 10 derniers audits, 7 alertes concernent la prononciation juste sous 93 % (88 à 93 %), aucune le débit.
  « rangée(s) » mal transcrit 3 fois ici (« ranger », « arranger ») : homophone, 1 seule vidéo, pas de règle.
- 2026-10-13 (08:00) : 1re vidéo sans alerte depuis le 12/10 17:00 (débit 24,5 car./s, prononciation 94 %),
  règle 5 appliquée (aucune phrase ouverte par « Ton »). « seo » et « radius » restent candidats au lexique
  mais sont bien entendus (« seo radius ») : écart dû à la graphie phonétique, déjà en piste audit. « IA »
  en milieu de phrase mal compris 1 fois (« l'IA compare ») : à surveiller, pas de règle tant que ça ne revient pas.
- 2026-10-12 (19:00) : débit 24,3 à 25,3 car./s sur les 4 dernières vidéos (cible tenue). « ton » en début de
  phrase mal compris 7 fois sur 2 vidéos : règle 5 ajoutée (reformuler, pas de lexique possible pour un mot courant).
  « l'appli » entendu « la plie » : remplacé par « l'application » au 2e rendu, corrigé.
- 2026-10-12 (12:00) : 2 vidéos Kyutai auditées, débit 24,6 à 24,8 car./s (dans la cible). PowerPoint et
  Anthropic ajoutés au lexique (mal dits au 1er rendu, corrects au 2e). « rends » et « ton » reviennent
  mais sont des homophones : pas d'entrée au lexique, piste audit ajoutée pour Bill.
- 2026-10-12 : mise en place. Voix Kyutai estelle ralentie à 0,94, pauses 0,22 / 0,36 s, 0,6 s de
  silence d'ouverture, prix et nombres convertis en lettres, audit automatique après chaque vidéo.
