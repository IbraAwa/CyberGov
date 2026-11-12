# Operation El Jefe — plateforme de labo (CTF)

Petit site Flask qui accompagne le CTF : comptes eleves, parcours en 5 missions,
economie d'indices, score en direct et classement. Pense pour etre **active sur Render
uniquement pendant le labo**.

## Comptes

- Un compte professeur est cree au premier demarrage : **prof / eljefe2026**
  (change le PIN : connecte-toi, cree un nouveau compte prof, supprime `prof`).
- Le prof cree les comptes eleves (prenom + PIN, aleatoire si laisse vide) dans la console.

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
# http://127.0.0.1:8000  (login prof : prof / eljefe2026)
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

## Reinitialiser une session

Dans la console prof : bouton **Reset** sur un eleve (efface sa progression et ses indices),
ou **Suppr** pour supprimer le compte.
