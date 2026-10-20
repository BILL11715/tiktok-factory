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
   Même chose pour « Résultat ? » en ouverture de phrase : mal compris sur 2 vidéos (17/10 19:00 « pasuta »,
   18/10 08:00 « l azultat ») ; écrire « Au final ? » (bien entendu au 2e rendu du 18/10).
   Même chose pour « Exemple, » en ouverture : mal compris sur 2 vidéos (17/10 19:00 avalé, 18/10 17:00 « mes armes »),
   et « Prends un... » (18/10 17:00 « si tu es ») ; écrire « Imagine un plombier. » ou glisser l'exemple dans la phrase.
   Même chose pour « Puis » en ouverture : compté 3 fois dans les mots mal compris (20/10 08:00 « lui ») ; écrire « Ensuite, ».
6. Mettre « SEO Radius » en fin de phrase, jamais suivi d'un verbe court : les mots qui le suivent sont avalés
   sur 3 vidéos (14/10 « aura dus », « radius ed » ; 16/10 « SEO Radius. Tape un » entendu « au radus ca par »).
   Écrire « Pour ça, j'utilise SEO Radius. » puis une nouvelle phrase qui commence par un mot d'au moins
   2 syllabes (« Ensuite, tu choisis... ») : « SEO Radius. Tu tapes » a encore été avalé le 16/10 22:00 (« seo radus tap »).
   Le verbe « tapes » lui-même est mal compris sur 2 vidéos (16/10 « tap », 18/10 17:00 « t apples ») : écrire « tu choisis »
   (bien entendu au 2e rendu du 18/10 17:00).
7. Durée : à débit 25 car./s, 1 450 à 1 480 caractères ne donnent que 77 à 81 s (17/10 22:00, 18/10 12:00, 18/10 22:00).
   Viser 1 520 à 1 600 caractères pour tenir 82 à 90 s, sans dépasser 16 segments. Au-delà, ça déborde : 1 619 car. = 92,9 s (19/10 19:00),
   et la vidéo du 19/10 17:00 a atteint 97,9 s (hors cible 95 s). Rester sous 1 600.
   Depuis le 19/10, 1 550 à 1 560 car. donnent déjà 90 à 93 s (19/10 22:00 93,7 s ; 20/10 08:00 92,9 s) : viser 1 500 à 1 550.

## Pistes pour Bill (changements de code proposés, à valider par lui)
- Audit : comparer la transcription au texte écrit du script, pas à la graphie phonétique du lexique.
  Aujourd'hui « PDF » (dit « p d f ») et « PowerPoint » (dit « paoueur pointe ») comptent comme des
  écarts alors qu'ils sont bien entendus, ce qui fait passer la prononciation sous 93 % à tort.
- Audit : ignorer les homophones (« rends » / « rend », « ton » / « t'on ») dans les mots mal compris.
- Audit : relancer `factory.audit` sur le même run ajoute une 2e ligne identique dans `audits_ia.jsonl` (doublons 14/10 12:00 et 19:00), ce qui gonfle le compte des « mots mal compris sur plusieurs vidéos ». Remplacer la ligne du même stamp au lieu d'en ajouter une.

## Journal (1 ligne par revue, la plus récente en haut, 20 lignes maximum)
- 2026-10-20 (08:00) : 1er rendu à 93 % avec alerte (« relis » entendu « venez », « montre » entendu « entre », « puis » entendu « lui ») : reformulés
  (« vérifie », « fais-lui voir », « ensuite »), 2e rendu à 91 % (écarts surtout homophones et graphie : freelance, IA, ses/ces, peut/peu), débit 24,5 car./s, 92,9 s
  pour 1 560 car. Sur les 10 derniers audits, débit 23,9 à 25,2 car./s, 7 sans alerte. Règle 5 étendue à « Puis », règle 7 resserrée (1 500 à 1 550 car.).
- 2026-10-19 (19:00) : sans alerte au 1er rendu (débit 24,5 car./s, prononciation 94 %, 92,9 s, 1 619 car.). Sur les 10 derniers audits, débit 23,9 à 25,2 car./s,
  8 sans alerte. 2 vidéos du jour au-dessus de 90 s (97,9 et 92,9 s) : règle 7 précisée (rester sous 1 600 car.). « jour J » entendu « jorgi » et « onde » entendu « tombe »
  sur 1 seule vidéo : pas de règle. Pas de nouveau mot au lexique.
- 2026-10-19 (12:00) : sans alerte au 1er rendu (débit 24,3 car./s, prononciation 97 %, 89,9 s, 1 549 car.). Règle 7 tenue sur les 2 vidéos du jour (89,8 et 89,9 s).
  Sur les 10 derniers audits, débit 24,2 à 25,2 car./s, 8 sans alerte (les 2 alertes : prononciation 91 et 92 %, déjà traitées). « Handy » et « Whisper »
  ajoutés au lexique par précaution ; « Handy » reste entendu « andy » (proche, 1 seule vidéo, pas de règle). Le lint refuse « pas d'abonnement » (mot « abonne ») :
  écrire « rien à payer chaque mois ». Pas de nouvelle règle.
- 2026-10-18 (22:00) : 1er rendu à 89 % : noms de villes peu connus mal compris (« Bron » entendu « branc » 3 fois, « Vaulx-en-Velin », « Caluire »),
  remplacés par Lille, Roubaix, Tourcoing, Lens ; 2e rendu à 92 % avec alerte (« Lille » entendu « l'île », « ce gérant laisse filer » avalé). Débit 25,2 car./s, 77 s.
  Sur les 10 derniers audits, débit 24,2 à 25,2 car./s, 8 sans alerte ; 3 vidéos à 81 s ou moins : règle 7 ajoutée (longueur). Villes : 1 seule vidéo, pas de règle,
  préférer une grande ville connue et la répéter peu. Doublons d'audit du même stamp retirés à la main (piste déjà notée).
- 2026-10-18 (17:00) : 1er rendu à 93 % avec alerte (« prends » entendu « si tu es », « tapes » entendu « t apples », « vaut » entendu « voir ») :
  reformulés, 2e rendu à 94 % sans alerte (débit 24,7 car./s, 84,7 s). Sur les 10 derniers audits, débit 24,2 à 25,4 car./s, 8 sans alerte.
  « Exemple, » en ouverture et « tu tapes » mal compris sur 2 vidéos : règles 5 et 6 précisées. Doublon d'audit du même stamp retiré à la main (piste déjà notée).
- 2026-10-18 (08:00) : 1er rendu à 91 % (« mercredi » entendu « marc redit », « le suivi range » entendu « je suggère en »,
  « un clic », « Résultat ») : reformulés (« jeudi », « chaque prospect reçoit un statut », « en un seul clic », « Au final »),
  2e rendu à 93 % sans alerte (débit 24,2 car./s, 91,2 s). Sur les 10 derniers audits, débit 23,8 à 25,4 car./s, 7 sans alerte.
  « Résultat » en ouverture mal compris sur 2 vidéos : règle 5 étendue. Doublon d'audit du même stamp retiré à la main (piste déjà notée).
- 2026-10-17 (19:00) : 5 audits de suite sans alerte (16/10 19:00 à 17/10 19:00), débit 24,8 car./s, prononciation 94 %, 90,2 s.
  Règles 5 et 6 tenues. Prénom « Inès » mal compris 2 fois (« linaise ») sur 1 seule vidéo : pas de lexique, préférer des
  prénoms d'une syllabe ou très courants dans les exemples. « radiusse », « tchatte », « anne tropique » restent en tête des
  « mots mal compris » mais viennent de la graphie phonétique (piste déjà notée). Pas de nouvelle règle.
- 2026-10-16 (22:00) : 1er rendu à 92 % (« court » mal compris 2 fois : « co repolis », « courant ») : remplacé par « simple »
  et « petit message », 2e rendu à 93 % sans alerte (débit 24,2 car./s, 83,6 s). « SEO Radius. Tu tapes » encore avalé malgré la règle 6 :
  règle précisée (phrase suivante ouverte par un mot plus long). Doublon d'audit du même stamp retiré à la main (piste déjà notée).
- 2026-10-16 (17:00) : hook « te fait peur » entendu « feper » et « offre » entendu « oeuf » au 1er rendu : reformulés
  (« Tu as peur d'appeler... », « proposition commerciale »), hook bien entendu au 2e rendu. Prononciation 90 % (débit 25,0 car./s, 90 s).
  Mots avalés après « SEO Radius » sur 3 vidéos : règle 6 ajoutée. Doublon d'audit du même stamp retiré à la main (piste déjà notée).
- 2026-10-14 (19:00) : 1er rendu à 1 590 car. = 100,4 s (hors cible) et « chatbot » entendu « chapeau » 2 fois : chatbot ajouté au
  lexique (« tchatte botte », bien entendu au 2e rendu), texte ramené à 1 523 car. = 89,4 s. Prononciation 91 % : écarts surtout dus à la
  graphie phonétique (piste déjà notée). Sur les 10 derniers audits, débit 23,8 à 25,2 car./s, cible tenue. Pas de nouvelle règle (1 seule vidéo trop longue).
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
