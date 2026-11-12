# Operation El Jefe — plateforme de labo (CTF)

Petit site Flask qui accompagne le CTF : comptes eleves, parcours en 5 missions,
economie d'indices, score en direct et classement. Pense pour etre **active sur Render
uniquement pendant le labo**.

## Modele : sessions -> agences -> eleves

- **Session** = un cours dans une classe : intitule, code mnemonique, 1-2 stacks, date auto.
- Une session contient jusqu'a **4 agences**. **C'est l'agence qui a le compte** et qui joue.
- Chaque agence contient jusqu'a **5 eleves** : ce ne sont que des noms (pas de compte),
  pour savoir qui est dans quelle agence.
- **Connexion d'une agence** = `code de la session` + `nom de l'agence` + `mot de passe`
  (un mot + un PIN a 6 chiffres, genere et visible par le prof dans la console).

## Comptes professeur

- Un compte professeur est cree au premier demarrage : **bstorm / CycyBerFormation2026**
  (tu peux en ajouter d'autres dans la console -> section « Professeurs »).
- Tous les profs voient et gerent toutes les sessions.

## Parcours

- Une agence ne peut acceder qu'aux missions **deja debloquees** (jusqu'a sa mission en cours) ;
  elle peut revenir sur les missions deja faites, mais pas sauter en avant.

## Bareme (modifiable en haut de `app.py`)

- Base **1600 pts** (= 16 h), le temps coute **100 pts/h**.
- Indices : leger **50**, moyen **125**, fort **200**. **6 indices max** pour tout le parcours.
- Chaque flag valide rapporte **+75 pts**. Le score ne descend jamais sous 0.
- Classement : score decroissant ; a egalite, le premier a tout valider gagne.

## Contenu

- La **Mission 1** est deja remplie (briefing, 3 indices, corrige) d'apres tes PDF.
- Les briefings des missions 2 a 5 sont en place ; leurs **indices et corriges** sont a
  completer dans la console prof (onglet « Missions »). Les **flags** des 5 missions sont deja
  configures (et visibles pour le prof).
- Le corrige d'une mission se debloque cote eleve en entrant **le flag de cette mission**
  (le prof le voit toujours).

## Lancer en local

```bash
pip install -r requirements.txt
flask --app app run --port 8000
# http://127.0.0.1:8000  (login prof : bstorm / CycyBerFormation2026)
```

## Deployer sur Render

1. Cree un depot GitHub (ex. `operation-el-jefe-labo`) et pousse-y ce dossier :
   ```bash
   git init && git add . && git commit -m "labo el jefe"
   git branch -M main
   git remote add origin https://github.com/<toi>/operation-el-jefe-labo.git
   git push -u origin main
   ```
2. Sur Render : **New +  ->  Web Service**, connecte ce depot. Render lit `render.yaml`.
   - Build : `pip install -r requirements.txt`
   - Start : `gunicorn app:app`
3. **Persistance (important).** Le `render.yaml` est regle sur le plan **starter** avec un
   **disque** monte sur `/var/data` (SQLite y est stocke, les scores survivent aux
   redemarrages). Sur le plan **free**, il n'y a pas de disque : les donnees sont remises a
   zero a chaque redemarrage/veille — acceptable seulement pour un test.
4. Variable `SECRET_KEY` : generee automatiquement par Render.
5. Pour **activer/desactiver** entre les labos : sur Render tu peux **suspendre** le service
   (Settings  ->  Suspend) et le reprendre le jour du labo.

## Reinitialiser

Dans la console prof, sur une agence : **Reset progression** (efface score/indices/flags),
**Nouveau mdp** (regenere le mot de passe), **Supprimer l'agence**. On peut aussi supprimer
une session entiere.

> **Note base de donnees :** le modele a change (sessions/agences/eleves). Au premier
> lancement avec une base vide, tout se cree automatiquement. Une ancienne base `labo.db`
> (modele par eleve) est incompatible : supprime-la / repars d'un disque vide sur Render.
