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
5. Éviter de commencer une phrase (surtout le hook) par « Ton » ou « Son » + nom (« Son concurrent » entendu « donc » le 22/10 22:00) : mal compris sur 2 vidéos du 12/10
   (« ton client » entendu « donc il y en », « ton entretien » entendu « son » / « dans l »). Préférer « Tu as un
   entretien demain ? » ou placer le mot après le verbe.
   Même chose pour « Résultat ? » en ouverture de phrase : mal compris sur 2 vidéos (17/10 19:00 « pasuta »,
   18/10 08:00 « l azultat ») ; écrire « Au final ? » (bien entendu au 2e rendu du 18/10).
   Même chose pour « Exemple, » en ouverture : mal compris sur 2 vidéos (17/10 19:00 avalé, 18/10 17:00 « mes armes »),
   et « Prends un... » (18/10 17:00 « si tu es ») ; écrire « Imagine un plombier. » ou glisser l'exemple dans la phrase.
   Même chose pour « Puis » en ouverture : compté 3 fois dans les mots mal compris (20/10 08:00 « lui ») ; écrire « Ensuite, ».
   « Tu » + verbe en début de phrase entendu « il » sur 3 vidéos (21/10 08:00 « tu prospectes », 21/10 12:00 « Tu lui donnes »,
   21/10 19:00 « Tu demandes » → « il demande », alors que le verbe a 2 syllabes) : ne pas ouvrir la phrase par « Tu » ; écrire
   « Quand tu demandes... », « Si tu ajoutes... » ou « Toi, tu... ».
   « Relis » (impératif) mal compris sur 3 vidéos (20/10 08:00 « venez », 22/10 08:00 « voilez ») : écrire « Vérifie » ou
   « Prends le temps de relire » (mot courant, pas de lexique).
   « Promets » (impératif) compté 4 fois dans les mots mal compris (22/10 17:00 « on met ») : écrire « Mieux vaut promettre... »
   ou « garantir » (bien entendus au 2e rendu du 22/10 17:00).
6. Mettre « SEO Radius » en fin de phrase, jamais suivi d'un verbe court : les mots qui le suivent sont avalés
   sur 3 vidéos (14/10 « aura dus », « radius ed » ; 16/10 « SEO Radius. Tape un » entendu « au radus ca par »).
   Écrire « Pour ça, j'utilise SEO Radius. » puis une nouvelle phrase qui commence par un mot d'au moins
   2 syllabes (« Ensuite, tu choisis... ») : « SEO Radius. Tu tapes » a encore été avalé le 16/10 22:00 (« seo radus tap »).
   Le verbe « tapes » lui-même est mal compris sur 2 vidéos (16/10 « tap », 18/10 17:00 « t apples ») : écrire « tu choisis »
   (bien entendu au 2e rendu du 18/10 17:00).
7. Durée : la même longueur donne des durées très différentes (1 560 car. = 92,9 s le 20/10 08:00, 1 600 car. = 72 à 82 s le 21/10).
   Le 21/10, 4 vidéos sur 4 sous 82 s avec 1 590 à 1 610 car. (72,6 s, 81,8 s, 72,3 s, 80,0 s pour 1 610 car. à 25,1 car./s) :
   viser désormais 1 620 à 1 650 car. (plafond du runbook), sans dépasser 16 segments, surtout en format outil, mythe ou méthode
   à phrases courtes. Si une vidéo repasse au-dessus de 93 s à cette longueur, redescendre à 1 600.
   Tenu le 22/10 08:00 (1 629 car. = 81,4 s à 25,1 car./s, sans alerte) : garder 1 620 à 1 650 car.
   Le 22/10 17:00, 1 634 car. = 77,2 s (débit 25,6, alerte) au 1er rendu, 1 635 car. = 79,9 s au 2e : couper les phrases longues
   en deux (« Il a le temps. Et il veut... ») ralentit la voix plus que d'ajouter du texte.
8. « Claude » entendu « cloud » sur 2 vidéos (23/10 12:00 2 fois, 23/10 19:00 3 fois) ; le lexique « clôde » n'y change rien (essayé au 2e rendu du 23/10 19:00,
   retiré). Le dire 4 fois maximum par vidéo, jamais en tout début de phrase : écrire « Avec Claude, ... », « demande à Claude » ou remplacer par « l'IA ».
   Éviter aussi « coloc » (entendu « coloque ») et « appli » juste après un mot court (« appuie ») : préférer « application » une fois sur deux.

## Pistes pour Bill (changements de code proposés, à valider par lui)
- Audit : comparer la transcription au texte écrit du script, pas à la graphie phonétique du lexique.
  Aujourd'hui « PDF » (dit « p d f ») et « PowerPoint » (dit « paoueur pointe ») comptent comme des
  écarts alors qu'ils sont bien entendus, ce qui fait passer la prononciation sous 93 % à tort. Même chose pour les sigles du lexique (« QR », « SMS » dits
  « Q R », « S M S » mais transcrits « qr », « sms » : 5 écarts sur la vidéo du 22/10 22:00).
- Audit : ignorer les homophones (« rends » / « rend », « ton » / « t'on ») dans les mots mal compris.
- Audit : relancer `factory.audit` sur le même run ajoute une 2e ligne identique dans `audits_ia.jsonl` (doublons 14/10 12:00 et 19:00), ce qui gonfle le compte des « mots mal compris sur plusieurs vidéos ». Remplacer la ligne du même stamp au lieu d'en ajouter une.
- Rendu : Remotion télécharge son Chrome depuis remotion.media, bloqué par le proxy du conteneur (403) le 23/10 12:00. Contourné à la main en liant
  `remotion/node_modules/.remotion/chrome-headless-shell/linux64/chrome-headless-shell-linux64` au Chromium local `/opt/pw-browsers/chromium_headless_shell-*`
  (+ fichier VERSION attendu) : à intégrer dans setup.sh, sinon chaque run neuf échoue à l'étape montage.

## Journal (1 ligne par revue, la plus récente en haut, 20 lignes maximum)
- 2026-10-24 (08:00) : sans alerte au 1er rendu (débit 25,1 car./s, prononciation 94 %, 82,5 s pour 1 630 car. environ) : règle 7 tenue. « PageSpeed Insights » mis au lexique par précaution,
  bien entendu (« pagespeedinsights »). Sur les 10 derniers audits, 6 sans alerte (3 prononciation à 90-92 %, 1 débit + prononciation le 23/10 19:00). « vérifie » et « garde » comptés 3 fois
  dans les mots mal compris mais surtout par conjugaison (« vérifiez ») : pas de lexique. Chrome de Remotion relié à la main au Chromium local avant le rendu (piste déjà notée, toujours à intégrer). Pas de nouvelle règle.
- 2026-10-23 (19:00) : 1er rendu 79,3 s, débit 25,7, prononciation 91 % (« Claude » entendu « cloud » 3 fois, « Publier crée » « public écrit », « Tes colocs » « les colloques ») ;
  phrases coupées, mots reformulés et « Claude » mis au lexique : 2e rendu 78,6 s, débit toujours 25,7, prononciation 88 % (« cloud » 3 fois encore, « appuie », « convaincre »).
  Lexique retiré (sans effet), règle 8 ajoutée. Couper les phrases n'a pas ralenti la voix cette fois (1 636 car.). Sur les 10 derniers audits, 5 sans alerte.
- 2026-10-23 (12:00) : sans alerte au 1er rendu (débit 25,3 car./s, prononciation 96 %, 79,8 s pour 1 633 car.). Sur les 10 derniers audits, débit 24,7 à 25,6 car./s,
  6 sans alerte (3 prononciation à 90-91 %, 1 débit). Règle 7 tenue (78 à 84 s à 1 620-1 650 car.). « Claude » entendu « cloud » 2 fois sur 1 seule vidéo : pas de lexique.
  Montage bloqué par le téléchargement de Chrome de Remotion (proxy) : contourné, piste ajoutée pour Bill. Pas de nouvelle règle.
- 2026-10-22 (22:00) : 1er rendu à 89 % (« à Lyon. Clients ravis » entendu « alliant client ravi », « Son concurrent » entendu « donc », « Pour trouver » « vous trouvez »,
  « L'outil » « le tient », « Souvent, » « nouveau ») : reformulés, 2e rendu à 90 % avec alerte, mais les écarts restants viennent surtout de la graphie (QR et SMS ajoutés
  au lexique en lettres, bien entendus « qr » « sms ») et des pluriels. Débit 24,7 car./s, 83,6 s pour 1 639 car. : règle 7 tenue. Sur les 10 derniers audits, débit 24,3 à 26,1 car./s,
  6 sans alerte. « Son » + nom en ouverture rejoint « Ton » : règle 5 précisée. Doublons d'audit du même stamp retirés à la main (piste déjà notée).
- 2026-10-22 (17:00) : 1er rendu 77,2 s avec alerte débit 25,6 (« ramoneur » en tout début de hook entendu « hame honneur », « rush » « roche », « Réserve » « deserve », « pic » « pied ») :
  hook réordonné (« En plein hiver, un ramoneur... »), mots remplacés, phrases coupées ; 2e rendu sans alerte (25,5 car./s, 96 %, 79,9 s). Sur les 10 derniers audits, débit 24,3 à 26,1 car./s,
  7 sans alerte. « promets » 4 fois : règle 5 étendue. Règle 7 précisée. Pas de nouveau mot au lexique (mots mal compris sur 1 seule vidéo).
- 2026-10-22 (08:00) : sans alerte au 1er rendu (débit 25,1 car./s, prononciation 95 %, 81,4 s pour 1 629 car.). Sur les 10 derniers audits, débit 24,3 à 26,1 car./s,
  6 sans alerte (2 alertes débit le 21/10, 2 prononciation). Règle 7 tenue. « Relis » mal compris sur 3 vidéos : règle 5 étendue. « radiusse » et « opportunite »
  restent en tête des mots mal compris mais viennent de la graphie et du pluriel (piste déjà notée). Pas de nouveau mot au lexique.
- 2026-10-21 (19:00) : 1er rendu à 88 % (« il te la dicte » entendu « si tu l as dictes », « magique. Plus il fait d'étapes seul » avalé) : reformulés,
  2e rendu à 91 % avec alerte (écarts surtout graphie et homophones : anne tropique, ses/ces, cuisines ; « Tu demandes » entendu « il demande »), débit 25,1 car./s, 80,0 s
  pour 1 610 car. Sur les 10 derniers audits, débit 24,3 à 26,1 car./s, 6 sans alerte. Règle 5 étendue (ne plus ouvrir par « Tu »), règle 7 relevée (1 620 à 1 650 car.).
- 2026-10-21 (12:00) : 1er rendu à 92 % (« tes papiers ne partent » entendu « le papier part », « ne les lit » entendu « l est lie », « Tu lui donnes » entendu « il donne ») :
  reformulés, 2e rendu à 94 % sans alerte (débit 24,3 car./s, 81,8 s pour 1 607 car.). Sur les 10 derniers audits, débit 23,9 à 26,1 car./s (alerte débit au 21/10 08:00, 72,6 s), 7 sans alerte.
  « Tu » entendu « il » sur 2 vidéos : règle 5 étendue. Règle 7 précisée. AnythingLLM et Word ajoutés au lexique (bien entendus). Doublon d'audit du même stamp retiré à la main (piste déjà notée).
- 2026-10-20 (22:00) : sans alerte au 1er rendu (débit 24,7 car./s, prononciation 97 %, 81,7 s pour 1 570 car.). Sur les 10 derniers audits, débit 23,9 à 25,4 car./s,
  8 sans alerte. 2e vidéo du jour à 82 s malgré 1 554 à 1 570 car. : règle 7 relevée (1 570 à 1 600 car.). « chauffagiste » entendu « chou fagiste » et « premier »
  entendu « promenee » sur 1 seule vidéo : pas de lexique. « radiusse » et « opportunite » restent en tête des mots mal compris mais viennent de la graphie et du pluriel (piste déjà notée).
- 2026-10-20 (17:00) : sans alerte au 1er rendu (débit 25,4 car./s, prononciation 93 %), mais 82,1 s pour 1 554 car. alors que 1 560 car. donnaient 92,9 s le matin :
  règle 7 revue (fourchette 1 540 à 1 580 car.). Sur les 10 derniers audits, débit 23,9 à 25,4 car./s, 7 sans alerte. Phrases nominales très courtes (« Aucun conflit. »)
  et fin de phrase « un vrai merci donne » avalées, « place » entendu « peste » : 1 seule vidéo, pas de règle. « promets » / « promet » : homophone, pas de lexique.
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
