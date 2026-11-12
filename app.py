import os, sqlite3, random, string, time
from functools import wraps
from flask import (Flask, g, redirect, render_template, request, session, url_for, flash, abort, jsonify)

APP_TITLE = "Operation El Jefe"
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "labo.db"))

# ---- Bareme (modifiable) ----
BASE_POINTS = 1600          # 16 h
POINTS_PER_HOUR = 100       # le temps coute 100 pts/h
HINT_COST = {"leger": 50, "moyen": 125, "fort": 200}
HINT_LABELS = {"leger": "Indice leger", "moyen": "Indice moyen", "fort": "Indice fort"}
MAX_HINTS = 6               # nombre total d'indices autorises
FLAG_BONUS = 75             # chaque flag valide rapporte des points

MAX_AGENCES = 4             # agences par session
MAX_ELEVES = 5             # eleves par agence

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-change-me")

# ============================================================
#   CONTENU DES MISSIONS (seed initial, ensuite editable en admin)
# ============================================================
MISSIONS_SEED = [
 {
  "num": 1, "title": "Le coffre", "flag": "FLAG{pin_brute_force_ok}",
  "briefing": """
<h3>Le contexte</h3>
<p>Votre cellule vous a contacte personnellement. Vous etes les meilleurs, et c'est pour ca qu'on fait appel a vous.</p>
<p>La mission El Jefe vise le cartel de Sinaloa et son chef. Une sous-mission concerne un coffre numerique, <span class="code">coffre.zip</span>, saisi lors d'une perquisition. Il est verrouille par un code PIN a 4 chiffres, et personne n'a reussi a l'ouvrir a la main.</p>
<h3>Votre mission</h3>
<ol>
<li>Ecrivez un programme qui teste tous les codes possibles, de <span class="code">0000</span> a <span class="code">9999</span>.</li>
<li>Pour chaque code, essayez d'ouvrir le coffre. Une mauvaise combinaison ne doit pas faire planter le programme.</li>
<li>Des que le bon code est trouve, arretez la recherche et recuperez le contenu du coffre.</li>
</ol>
<h3>Consignes techniques</h3>
<ul>
<li>Un fichier de depart vous est fourni dans votre langage. Completez la fonction de recherche du code.</li>
<li>La fonction qui teste un code est deja ecrite : elle renvoie le contenu si le code est bon, sinon rien. Appelez-la, ne la modifiez pas.</li>
<li>Lancez votre programme depuis le dossier qui contient <span class="code">coffre.zip</span>.</li>
</ul>
<h3>Ce que vous obtiendrez</h3>
<ul>
<li>L'adresse de l'intranet du cartel : la porte d'entree vers l'etape 2.</li>
<li>Le flag de l'etape 1, a soumettre ci-dessous pour valider la mission.</li>
</ul>
""",
  "hint_leger": """<p><strong>Ce que vous savez.</strong> Le PIN fait 4 chiffres : de 0000 a 9999, le nombre de codes est limite.</p>
<p><strong>Par ou commencer :</strong></p>
<ul>
<li>Combien de codes faut-il tester au maximum ? Un ordinateur les teste en quelques secondes.</li>
<li>Quand le mot de passe est faux, <span class="code">zipfile</span> ne renvoie pas "faux" : il leve une exception. Laquelle ?</li>
<li>Un PIN peut commencer par un zero. Comment ecrire 7 sur 4 chiffres ?</li>
</ul>
<p class="hint-note">Indice leger : l'orientation seulement. Pas de code a copier.</p>""",
  "hint_moyen": """<p><strong>La structure.</strong> Il faut quatre boucles imbriquees : une par chiffre du PIN, chacune de 0 a 9. Dans la boucle la plus profonde, on forme le code a 4 chiffres et on le teste.</p>
<p><strong>Tester un code :</strong></p>
<ul>
<li>Ouvrir le fichier avec <span class="code">zipfile.ZipFile</span>, puis lire <span class="code">mission.txt</span> avec <span class="code">pwd=</span>.</li>
<li>Le mot de passe attend des octets : pensez a <span class="code">.encode()</span>.</li>
<li>Une mauvaise combinaison ne doit pas arreter le programme : capturez l'exception avec <span class="code">try / except</span>.</li>
</ul>
<p class="hint-note">Indice moyen : la structure, sans le code complet.</p>""",
  "hint_fort": """<p><strong>Le programme pas a pas.</strong> Recopiez ce code, lancez-le depuis le dossier qui contient <span class="code">coffre.zip</span>, et lisez ce qu'il affiche.</p>
<pre class="snippet">import zipfile, zlib
with zipfile.ZipFile("coffre.zip") as z:
    for a in range(10):
      for b in range(10):
        for c in range(10):
          for d in range(10):
            pin = f"{a}{b}{c}{d}".encode()
            try:
                contenu = z.read("mission.txt", pwd=pin)
                print("PIN trouve :", pin.decode())
                print(contenu.decode())
                raise SystemExit
            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                pass</pre>
<p>Les quatre boucles couvrent les 10 000 combinaisons. Le <span class="code">try</span> ignore les mauvais codes, et <span class="code">raise SystemExit</span> arrete des que le bon est trouve. Le flag est dans le contenu affiche.</p>
<p class="hint-note">Indice fort : la demarche complete. Il ne donne ni le PIN, ni le flag : il faut les obtenir en lancant le programme.</p>""",
  "correction": """<h3>Demarche de A a Z</h3>
<ol>
<li><span class="code">coffre.zip</span> est protege par mot de passe. Le PIN a 4 chiffres : 10 000 codes possibles.</li>
<li>Une ouverture avec le mauvais mot de passe leve une exception : c'est le signal pour passer au code suivant.</li>
<li>On genere les codes avec 4 boucles imbriquees, formates avec <span class="code">f"{a}{b}{c}{d}"</span> (zeros devant).</li>
<li>Dans la boucle la plus profonde : <span class="code">try</span> pour lire <span class="code">mission.txt</span> avec <span class="code">pwd=</span>, <span class="code">except</span> pour ignorer le mauvais code.</li>
<li>Des que la lecture reussit : afficher le PIN et le contenu, puis <span class="code">raise SystemExit</span>.</li>
</ol>
<pre class="snippet">import zipfile, zlib
with zipfile.ZipFile("coffre.zip") as z:
    for a in range(10):
      for b in range(10):
        for c in range(10):
          for d in range(10):
            pin = f"{a}{b}{c}{d}".encode()
            try:
                contenu = z.read("mission.txt", pwd=pin)
                print("PIN trouve :", pin.decode()); print(contenu.decode()); raise SystemExit
            except (RuntimeError, zipfile.BadZipFile, zlib.error):
                pass</pre>
<p>Resultat : le PIN est <span class="code">0731</span>. Le fichier contient l'adresse de l'intranet et le flag <span class="code">FLAG{pin_brute_force_ok}</span>.</p>
<h3>Comment se defendre</h3>
<ul>
<li>Un PIN a 4 chiffres se teste en une seconde : allonger le code ou limiter les essais.</li>
<li>ZipCrypto est faible ; le chiffrement AES (ex. librairie pyzipper) est bien plus solide.</li>
</ul>""",
 },
 {
  "num": 2, "title": "L'intranet", "flag": "FLAG{sqli_union_ok}",
  "briefing": """
<h3>Le contexte</h3>
<p>Le coffre a livre son secret : vous avez l'adresse de l'intranet du cartel. Le site a une page de connexion et une barre de recherche de membres. Personne ne controle ce que les utilisateurs y tapent.</p>
<h3>Ce que vous devez faire</h3>
<ol>
<li>Ouvrez l'intranet dans votre navigateur. Vous n'avez pas d'identifiants.</li>
<li>Essayez de vous connecter sans connaitre le mot de passe. Observez ce que l'application fait de votre saisie.</li>
<li>Utilisez la barre de recherche : elle presente le meme defaut.</li>
<li>Trouvez le hash du mot de passe du compte du chef (<span class="code">el_jefe</span>).</li>
</ol>
<h3>Ce que vous obtiendrez</h3>
<ul><li>Le hash MD5 du mot de passe du chef (pour l'etape 3) et un flag a soumettre ci-dessous.</li></ul>
""",
  "hint_leger": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_moyen": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_fort": "<p><em>Indice a completer par le professeur.</em></p>",
  "correction": "<p><em>Corrige a completer par le professeur.</em></p>",
 },
 {
  "num": 3, "title": "Le mot de passe du chef", "flag": "FLAG{hash_cracked_ok}",
  "briefing": """
<h3>Le contexte</h3>
<p>Vous avez le hash du mot de passe d'El Jefe, ainsi que des informations sur ses preferences. Le mot de passe est hashe : impossible de le lire directement. Tester tous les caracteres prendrait des annees : reduisez les possibilites (animal + couleur + annee) et cherchez-les une par une.</p>
<h3>Ce que vous devez faire</h3>
<ol>
<li>Reperez l'animal et l'annee du chef, et sa couleur preferee.</li>
<li>Ecrivez un programme qui teste les mots de passe possibles et compare leur empreinte au hash.</li>
<li>Connectez-vous avec <span class="code">el_jefe</span> et le mot de passe trouve.</li>
</ol>
<h3>Ce que vous obtiendrez</h3>
<ul><li>Le mot de passe en clair, l'acces au compte du chef, et un flag a soumettre ci-dessous.</li></ul>
""",
  "hint_leger": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_moyen": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_fort": "<p><em>Indice a completer par le professeur.</em></p>",
  "correction": "<p><em>Corrige a completer par le professeur.</em></p>",
 },
 {
  "num": 4, "title": "La zone sensible", "flag": "FLAG{hidden_routes_ok}",
  "briefing": """
<h3>Le contexte</h3>
<p>Depuis le compte du chef, une zone sensible du reseau est verrouillee par un code que personne n'a trouve. A vous de reperer cette zone, puis son code d'acces.</p>
<h3>Ce que vous devez faire</h3>
<ol>
<li>Connectez-vous avec le compte <span class="code">el_jefe</span>.</li>
<li>Trouvez la zone sensible : le reseau en dit parfois plus qu'il n'en a l'air (code source, robots.txt, onglet Reseau).</li>
<li>Trouvez le code d'acces : il n'est pas affiche a l'ecran.</li>
</ol>
<h3>Ce que vous obtiendrez</h3>
<ul><li>L'acces a la zone sensible et un flag a soumettre ci-dessous.</li></ul>
""",
  "hint_leger": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_moyen": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_fort": "<p><em>Indice a completer par le professeur.</em></p>",
  "correction": "<p><em>Corrige a completer par le professeur.</em></p>",
 },
 {
  "num": 5, "title": "Le dossier final", "flag": "FLAG{api_chain_ok}",
  "briefing": """
<h3>Le contexte</h3>
<p>Un dossier classifie, "Operation finale", n'apparait nulle part dans l'interface. Il faut lire ce que l'intranet echange avec le navigateur pour le recuperer.</p>
<h3>Ce que vous devez faire</h3>
<ol>
<li>Connecte en chef, observez les echanges page / serveur (onglet Reseau).</li>
<li>Trouvez le dossier classifie et lisez tout ce que le serveur renvoie, pas seulement le visible.</li>
<li>Une valeur encodee n'est pas un secret : decodez-la (base64).</li>
</ol>
<h3>Ce que vous obtiendrez</h3>
<ul><li>Le dossier final et le flag final de la mission, a soumettre ci-dessous.</li></ul>
""",
  "hint_leger": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_moyen": "<p><em>Indice a completer par le professeur.</em></p>",
  "hint_fort": "<p><em>Indice a completer par le professeur.</em></p>",
  "correction": "<p><em>Corrige a completer par le professeur.</em></p>",
 },
]

PH_HINT = "<p><em>Indice a completer par le professeur.</em></p>"
PH_CORR = "<p><em>Corrige a completer par le professeur.</em></p>"

# Indices + corriges reels pour les missions 2 a 5 (remplacent les placeholders).
FILLED_CONTENT = {
 2: {
  "hint_leger": """<p><strong>Ce que vous savez deja.</strong> Le serveur ne verifie pas ce que vous tapez : votre saisie est collee directement dans une requete SQL, et le serveur ne fait pas la difference entre vos mots et ses ordres.</p>
<p><strong>Par ou commencer :</strong></p>
<ul>
<li>Tapez une seule apostrophe dans le champ identifiant de la connexion. Que se passe-t-il ?</li>
<li>Une erreur SQL affichee est une information : votre texte atteint la base.</li>
<li>Une fois connecte, la barre de recherche presente la meme faille : elle affiche le resultat d'une requete.</li>
<li>Pour lire une autre table, votre requete doit renvoyer le meme nombre de colonnes que l'originale. Combien en renvoie-t-elle ?</li>
<li>Vous ne connaissez pas le nom des tables : SQLite garde la liste dans une table systeme. Comment la lire ?</li>
</ul>
<p>Ce que vous cherchez : le hash du mot de passe du chef, <span class="code">el_jefe</span>, dans la table <span class="code">members</span>.</p>
<p class="hint-note">Indice leger : la structure seulement. Pas de texte a copier.</p>""",
  "hint_moyen": """<p><strong>Connexion : contourner le mot de passe.</strong> La requete ressemble a <span class="code">WHERE username = '[ID]' AND password = '...'</span> avec votre identifiant a la place de [ID].</p>
<ul>
<li>Votre identifiant doit fermer l'apostrophe avant la fin prevue.</li>
<li>Ajoutez une condition toujours vraie (par exemple <span class="code">OR 1=1</span>).</li>
<li>Ajoutez un commentaire SQL (<span class="code">--</span>) pour ignorer la verification du mot de passe.</li>
</ul>
<p><strong>Recherche : compter puis lire.</strong></p>
<ul>
<li>Testez <span class="code">ORDER BY 1</span>, puis 2, puis 3. Le premier numero qui provoque une erreur est trop grand : vous avez le nombre de colonnes.</li>
<li>Pour lire une autre table, <span class="code">UNION SELECT</span> avec le meme nombre de colonnes, dans l'ordre.</li>
<li>Listez les tables via la table systeme <span class="code">sqlite_master</span> (colonne <span class="code">name</span>).</li>
</ul>
<p>Attention : un espace apres les deux tirets (<span class="code">-- </span>) evite beaucoup d'erreurs. Utilisez des apostrophes droites (<span class="code">'</span>), pas typographiques.</p>
<p class="hint-note">Indice moyen : les formes a utiliser, sans les valeurs completes.</p>""",
  "hint_fort": """<p><strong>Pas a pas.</strong></p>
<p>1. Connexion sans mot de passe &mdash; dans le champ identifiant :</p>
<pre class="snippet">' OR 1=1 --</pre>
<p>Mot de passe : n'importe quoi. Vous etes connecte, la faille fonctionne.</p>
<p>2. Nombre de colonnes (barre de recherche) :</p>
<pre class="snippet">' ORDER BY 2 --</pre>
<p>Puis <span class="code">ORDER BY 3</span> provoque une erreur : la requete a 2 colonnes.</p>
<p>3. Nom des tables :</p>
<pre class="snippet">' UNION SELECT name, sql FROM sqlite_master WHERE type='table' --</pre>
<p>La table des comptes apparait : <span class="code">members</span>.</p>
<p>4. Lire les comptes :</p>
<pre class="snippet">' UNION SELECT username, password FROM members --</pre>
<p>Notez le hash d'<span class="code">el_jefe</span> (32 caracteres hex).</p>
<p>5. Cibler le chef :</p>
<pre class="snippet">' UNION SELECT animal, birth_year FROM members WHERE username='el_jefe' --</pre>
<p>Notez l'animal et l'annee : ils serviront a l'etape 3. Le flag apparait dans la meme liste, sur la ligne du compte <span class="code">sys_audit</span>.</p>
<p class="hint-note">Indice fort : la demarche complete. Il ne donne ni le hash, ni le mot de passe, ni le flag : il faut les lire vous-meme.</p>""",
  "correction": """<h3>Demarche de A a Z</h3>
<ol>
<li>Les champs ne sont pas filtres : la saisie est concatenee dans la requete SQL (injection SQL).</li>
<li>Connexion sans mot de passe avec <span class="code">' OR 1=1 --</span> : la condition est toujours vraie et le <span class="code">--</span> annule la verification du mot de passe.</li>
<li>Dans la recherche, <span class="code">ORDER BY</span> donne le nombre de colonnes (ici 2).</li>
<li><span class="code">' UNION SELECT name, sql FROM sqlite_master WHERE type='table' --</span> revele la table <span class="code">members</span>.</li>
<li><span class="code">' UNION SELECT username, password FROM members --</span> affiche les hashs ; celui d'<span class="code">el_jefe</span> est <span class="code">164d50a562afd0cbbc3298aa3eb35d30</span>.</li>
<li><span class="code">' UNION SELECT animal, birth_year FROM members WHERE username='el_jefe' --</span> donne l'animal (<span class="code">cobra</span>) et l'annee, pour l'etape 3.</li>
</ol>
<p>Le flag est sur la ligne du compte <span class="code">sys_audit</span> : <span class="code">FLAG{sqli_union_ok}</span>.</p>
<h3>Comment se defendre</h3>
<ul>
<li>Requetes parametrees (placeholders), jamais de concatenation de chaines.</li>
<li>Comptes a privileges minimaux et messages d'erreur generiques (ne pas exposer le SQL).</li>
<li>Stocker les mots de passe avec un hash lent et sale (bcrypt, argon2), pas MD5.</li>
</ul>""",
 },
 3: {
  "hint_leger": """<p><strong>Ce que vous savez.</strong> Vous avez le hash du compte du chef, l'animal et l'annee de naissance. Le mot de passe suit une forme precise, decrite dans le briefing.</p>
<ul>
<li>Quel type de hash est-ce ? Combien de caracteres, quel alphabet ?</li>
<li>Si vous connaissez la forme du mot de passe, combien de candidats faut-il tester ?</li>
<li>Quelle librairie standard Python calcule une empreinte ?</li>
</ul>
<p class="hint-note">Indice leger : l'orientation seulement. Pas de code a copier.</p>""",
  "hint_moyen": """<p><strong>Construire les candidats.</strong></p>
<ul>
<li>L'animal est fixe : vous le connaissez deja.</li>
<li>La couleur change : faites une liste de couleurs courantes.</li>
<li>L'annee change aussi : une plage d'annees suffit, puisque vous connaissez l'annee de naissance.</li>
<li>Chaque couleur combinee avec chaque annee : une boucle dans une autre.</li>
</ul>
<p><strong>Tester chaque candidat.</strong></p>
<ul>
<li>Calculez l'empreinte MD5 avec <span class="code">hashlib</span>, en pensant a <span class="code">.encode()</span>.</li>
<li>Comparez avec <span class="code">hexdigest()</span> au hash du chef.</li>
<li>Des que ca correspond, affichez le mot de passe et arretez.</li>
</ul>
<p>Attention : un espace, une majuscule oubliee ou un mauvais chiffre change toute l'empreinte.</p>
<p class="hint-note">Indice moyen : la methode, sans les valeurs.</p>""",
  "hint_fort": """<p><strong>Le programme pas a pas.</strong> Recopiez ce code dans <span class="code">crack.py</span> et lancez <span class="code">python crack.py</span>. Verifiez que le hash est bien celui de l'etape 2.</p>
<pre class="snippet">import hashlib
cible = "164d50a562afd0cbbc3298aa3eb35d30"   # hash recupere a l'etape 2
animal = "cobra"                              # recupere a l'etape 2
couleurs = ["Noir", "Rouge", "Blanc", "Bleu", "Vert", "Or"]
trouve = None
for couleur in couleurs:
    for annee in range(1950, 2011):
        mot_de_passe = f"{animal}{couleur}{annee}"
        empreinte = hashlib.md5(mot_de_passe.encode()).hexdigest()
        if empreinte == cible:
            trouve = mot_de_passe
            print("Mot de passe trouve :", mot_de_passe)
            break
    if trouve:
        break
if trouve is None:
    print("Rien trouve : elargissez la liste de couleurs ou la plage d'annees.")</pre>
<p>Les deux boucles couvrent toutes les combinaisons couleur + annee ; <span class="code">hexdigest()</span> calcule l'empreinte ; <span class="code">break</span> arrete des que ca correspond.</p>
<p class="hint-note">Indice fort : la demarche complete. Il ne donne pas le mot de passe : trouvez-le en lancant le programme.</p>""",
  "correction": """<h3>Demarche de A a Z</h3>
<ol>
<li>Le hash fait 32 caracteres hexadecimaux : c'est du MD5, non sale et rapide a tester.</li>
<li>Le mot de passe a une forme connue : animal + couleur + annee. L'animal (<span class="code">cobra</span>) et l'annee viennent de l'etape 2.</li>
<li>On genere les candidats (couleurs x annees) et on compare l'empreinte MD5 de chacun au hash cible.</li>
<li>Correspondance trouvee : <span class="code">cobraNoir1978</span>.</li>
</ol>
<p>On se connecte ensuite avec <span class="code">el_jefe</span> / <span class="code">cobraNoir1978</span>. Flag : <span class="code">FLAG{hash_cracked_ok}</span>.</p>
<h3>Comment se defendre</h3>
<ul>
<li>MD5 est casse : utiliser un hash lent et sale (bcrypt, scrypt, argon2).</li>
<li>Imposer des mots de passe non devinables (pas de schema animal + couleur + annee).</li>
</ul>""",
 },
 4: {
  "hint_leger": """<p><strong>Ce que vous savez.</strong> Le compte du chef signale une activite suspecte. Une zone sensible existe, mais aucun lien ne mene a elle.</p>
<ul>
<li>Un site peut indiquer aux moteurs les pages a ne pas visiter. Ou se trouve ce fichier ?</li>
<li>Le code d'acces n'apparait pas a l'ecran. Un navigateur peut-il voir ce que le serveur envoie en coulisses ?</li>
<li>Le code source d'une page contient parfois des commentaires. Lesquels, sur "Mon compte" ?</li>
</ul>
<p class="hint-note">Indice leger : l'orientation seulement. Pas d'adresse ni de code a copier.</p>""",
  "hint_moyen": """<p><strong>Trois endroits a regarder.</strong></p>
<ul>
<li>Le fichier des chemins exclus : il nomme la zone sensible.</li>
<li>Le code source de "Mon compte" : un commentaire JavaScript mentionne la meme zone.</li>
<li>Les en-tetes de reponse d'une requete faite par la page : le code y est transmis.</li>
</ul>
<p><strong>Les outils.</strong></p>
<ul>
<li>Code source : clic droit &rarr; "Afficher le code source", ou Ctrl+U.</li>
<li>Requetes : F12, onglet <span class="code">Network</span>, puis recharger.</li>
<li>En-tetes : cliquer une requete &rarr; onglet <span class="code">Headers</span>, section Response Headers.</li>
</ul>
<p>Attention : le code n'apparait que connecte en chef. Connectez-vous d'abord avec <span class="code">el_jefe</span>.</p>
<p class="hint-note">Indice moyen : les trois pistes et les outils, sans l'adresse exacte ni le code.</p>""",
  "hint_fort": """<p><strong>Pas a pas.</strong></p>
<ol>
<li>Ouvrez <span class="code">/robots.txt</span> sur l'adresse de l'intranet : la ligne <span class="code">Disallow</span> donne le chemin de la zone sensible.</li>
<li>Connectez-vous avec <span class="code">el_jefe</span> et le mot de passe de l'etape 3.</li>
<li>Code source de "Mon compte" (Ctrl+U) : un commentaire mentionne la zone, et un appel a <span class="code">/api/v1/statut</span>.</li>
<li>F12 &rarr; Network &rarr; recharger &rarr; requete <span class="code">statut</span> &rarr; Headers : l'en-tete <span class="code">X-Code-Acces</span> contient le code.</li>
<li>Ouvrez la zone sensible, saisissez le code : le flag s'affiche.</li>
</ol>
<p class="hint-note">Indice fort : la demarche complete. Il ne donne pas le code : lisez-le dans l'en-tete.</p>""",
  "correction": """<h3>Demarche de A a Z</h3>
<ol>
<li><span class="code">/robots.txt</span> revele, via <span class="code">Disallow</span>, le chemin de la zone sensible (ex. <span class="code">/chef/salle-secrete</span>).</li>
<li>Connecte en <span class="code">el_jefe</span>, le code source de "Mon compte" confirme la zone et un appel a <span class="code">/api/v1/statut</span>.</li>
<li>Dans l'onglet Network, la reponse de <span class="code">/api/v1/statut</span> porte un en-tete <span class="code">X-Code-Acces</span> : c'est le code d'acces.</li>
<li>On ouvre la zone sensible et on saisit ce code.</li>
</ol>
<p>Flag : <span class="code">FLAG{hidden_routes_ok}</span>.</p>
<h3>Comment se defendre</h3>
<ul>
<li>La securite par l'obscurite ne protege pas : <span class="code">robots.txt</span> et les commentaires sont publics.</li>
<li>Proteger les zones sensibles par une vraie autorisation cote serveur, pas par un chemin cache.</li>
<li>Ne jamais transmettre un secret dans un en-tete ou le code source.</li>
</ul>""",
 },
 5: {
  "hint_leger": """<p><strong>Par ou commencer.</strong></p>
<ul>
<li>Dans les outils de dev, quelle partie de l'onglet Network ne montre que les appels au serveur ?</li>
<li>La page "Mon compte" fait des appels en arriere-plan. Lesquels ?</li>
<li>Un identifiant dans une adresse peut-il etre change pour voir un autre element ?</li>
<li>Une reponse contient plus que son corps : que trouve-t-on dans ses en-tetes ?</li>
</ul>
<p class="hint-note">Indice leger : l'orientation seulement. Pas d'adresse ni de valeur a copier.</p>""",
  "hint_moyen": """<p><strong>Trois gestes.</strong></p>
<ul>
<li>Observer : filtrez le Network sur <span class="code">api</span>, puis rechargez la page du compte.</li>
<li>Tester : changez l'identifiant de dossier dans l'adresse. Certains identifiants existent, d'autres non.</li>
<li>Lire les en-tetes : pas seulement le corps JSON. Une valeur y est encodee en base64.</li>
</ul>
<p><strong>Decoder.</strong></p>
<ul>
<li>Dans la console du navigateur, <span class="code">atob()</span> decode une valeur base64.</li>
<li>Un terminal decode aussi avec <span class="code">base64 -d</span>.</li>
</ul>
<p>Attention : ce n'est pas la reponse qui est encodee, c'est un en-tete. Cherchez le bon.</p>
<p class="hint-note">Indice moyen : les gestes et les outils, sans l'identifiant ni le flag.</p>""",
  "hint_fort": """<p><strong>Pas a pas.</strong></p>
<ol>
<li>Sur "Mon compte", la page appelle un dossier. Notez son identifiant dans l'onglet Network.</li>
<li>Ouvrez <span class="code">/api/v1/dossiers/</span> suivie d'un autre numero (essayez les numeros proches) : le dossier classifie apparait.</li>
<li>Sur cette reponse, ouvrez les en-tetes : <span class="code">X-Mission-Trace</span> contient une valeur encodee.</li>
<li>Decodez-la :</li>
</ol>
<pre class="snippet">atob("&lt;la valeur de l'en-tete&gt;")</pre>
<p>Le resultat est le flag final.</p>
<p class="hint-note">Indice fort : la demarche complete. Il ne donne pas le numero du dossier ni le flag : trouvez-les vous-meme.</p>""",
  "correction": """<h3>Demarche de A a Z</h3>
<ol>
<li>Onglet Network filtre sur <span class="code">api</span> : "Mon compte" appelle <span class="code">/api/v1/dossiers/&lt;id&gt;</span>.</li>
<li>En changeant l'identifiant (IDOR), on atteint un dossier classifie non lie dans l'interface.</li>
<li>La reponse de ce dossier porte un en-tete <span class="code">X-Mission-Trace</span> : une chaine base64.</li>
<li>On la decode avec <span class="code">atob(...)</span> (ou <span class="code">base64 -d</span>).</li>
</ol>
<p>Le flag final : <span class="code">FLAG{api_chain_ok}</span>.</p>
<h3>Comment se defendre</h3>
<ul>
<li>Verifier les droits cote serveur sur chaque objet (eviter l'IDOR) : un identifiant devinable ne suffit pas.</li>
<li>Ne pas mettre de donnees sensibles dans des en-tetes ; base64 n'est pas du chiffrement.</li>
<li>Journaliser et limiter les acces aux ressources de l'API.</li>
</ul>""",
 },
}

# Blocs "pour demarrer" (liens GitHub) ajoutes aux briefings des missions 1 et 2.
START_BLOCK_M1 = """
<h3>Pour demarrer</h3>
<p>Un depot de depart est fourni dans votre langage : recuperez celui qui correspond, il contient le fichier a completer et le <span class="code">coffre.zip</span>.</p>
<ul>
<li>Python : <span class="code">https://github.com/IbraAwa/PinFinderExoPython</span></li>
<li>Java : <span class="code">https://github.com/IbraAwa/PinFinderExoJava</span></li>
</ul>
<p>Telechargez le ZIP (bouton vert "Code" &rarr; "Download ZIP") ou clonez avec <span class="code">git clone</span>, puis lancez votre programme depuis le dossier qui contient <span class="code">coffre.zip</span>.</p>"""

START_BLOCK_M2 = """
<h3>Pour demarrer : lancer l'intranet en local</h3>
<p>L'intranet du cartel tourne sur votre propre machine. Le code est ici : <span class="code">https://github.com/IbraAwa/app</span></p>
<ol>
<li>Installez Python (python.org/downloads ; sur Windows, cochez "Add python.exe to PATH").</li>
<li>Recuperez le code : bouton vert "Code" &rarr; "Download ZIP", ou <span class="code">git clone https://github.com/IbraAwa/app.git</span></li>
<li>Dans un terminal, placez-vous dans le dossier : <span class="code">cd app</span></li>
<li>Installez les dependances : <span class="code">pip install -r requirements.txt</span></li>
<li>Lancez le site : <span class="code">flask --app app run --port 8000</span></li>
<li>Ouvrez <span class="code">http://127.0.0.1:8000</span> dans votre navigateur.</li>
</ol>
<p>Le <strong>kit de demarrage</strong> (PDF) detaille chaque etape, meme sans connaissance technique. Laissez le terminal ouvert tant que vous jouez : il fait tourner le site.</p>"""

START_BLOCKS = {1: ("PinFinderExo", START_BLOCK_M1), 2: ("github.com/IbraAwa/app", START_BLOCK_M2)}

# fusionne le contenu reel dans le seed (pour les bases neuves)
for _m in MISSIONS_SEED:
    if _m["num"] in FILLED_CONTENT:
        _m.update(FILLED_CONTENT[_m["num"]])
    if _m["num"] in START_BLOCKS:
        marker, block = START_BLOCKS[_m["num"]]
        if marker not in _m["briefing"]:
            _m["briefing"] = _m["briefing"] + block

ENONCE_GLOBAL = """
<p>Quatre services (FBI, CIA, NCIS, DEA) se disputent un dossier : faire tomber <strong>El Jefe</strong>, chef du cartel de Sinaloa. Le premier a reconstituer toute l'operation gagne.</p>
<p>La mission se joue en <strong>5 etapes</strong>. A chaque etape, un briefing, un objectif, et un <strong>flag</strong> a trouver pour passer a la suivante.</p>
<p>Vous disposez de <strong>6 indices maximum</strong> pour toute la mission (leger, moyen, fort). Chaque indice et chaque heure ecoulee grignotent votre score : reflechissez avant de demander de l'aide.</p>
<p>On n'attaque que les systemes prevus pour l'exercice. Bonne chasse, agent.</p>
"""

# 150 mots (mix francais / anglais) pour generer les mots de passe d'agence (mot + PIN 6 chiffres)
MDP_WORDS = [
    # animaux FR
    "jaguar", "cobra", "aigle", "faucon", "loup", "tigre", "puma", "renard", "ours",
    "lion", "requin", "panthere", "corbeau", "dauphin", "bison", "coyote", "lynx",
    "hibou", "aigle", "serpent", "guepard", "scorpion", "vautour", "belier", "taureau",
    # animals EN
    "wolf", "hawk", "eagle", "shark", "falcon", "raven", "viper", "panther", "cobra",
    "jackal", "mamba", "lynx", "bear", "fox", "owl", "stallion", "rhino", "bull",
    "cougar", "osprey", "mantis", "python", "kraken", "phoenix", "dragon",
    # couleurs FR
    "rouge", "noir", "argent", "cuivre", "ivoire", "ambre", "pourpre", "indigo",
    "emeraude", "corail", "cobalt", "bronze", "carmin", "saphir", "onyx",
    # colors EN
    "crimson", "scarlet", "silver", "amber", "violet", "cobalt", "ebony", "ivory",
    "copper", "jade", "onyx", "ruby", "slate", "teal", "gold",
    # nature FR
    "sierra", "orage", "tonnerre", "eclair", "brume", "canyon", "desert", "volcan",
    "mistral", "nord", "sud", "ocean", "dune", "ravin", "falaise", "cascade",
    # nature EN
    "storm", "thunder", "canyon", "desert", "summit", "ridge", "frost", "ember",
    "tide", "dune", "cliff", "blizzard", "mirage", "comet", "nova",
    # espionnage / noir FR
    "ombre", "masque", "cipher", "cle", "coffre", "dossier", "alias", "taupe",
    "complot", "secret", "piste", "indice", "traque", "filature", "planque",
    # spy / noir EN
    "shadow", "cipher", "vault", "ghost", "agent", "echo", "delta", "sigma",
    "vector", "cobweb", "decoy", "relay", "beacon", "nexus", "rogue",
    # objets / divers FR
    "lance", "fleche", "dague", "bouclier", "ancre", "marteau", "rouage", "ressort",
    "balise", "fusee", "sablier", "boussole", "prisme", "miroir", "lanterne",
    # objects / misc EN
    "anchor", "arrow", "dagger", "shield", "hammer", "gear", "spring", "rocket",
    "compass", "prism", "mirror", "lantern", "forge", "circuit", "matrix",
    # extras pour atteindre 150
    "sinaloa", "cartel", "jefe", "aguila", "sierra", "halcon", "lobo", "zorro",
    "diablo", "trueno", "sombra", "fuego", "noche", "plata", "oro",
]

# ============================================================
#   BASE DE DONNEES
# ============================================================
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d is not None:
        d.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- migration : ancien modele "par eleve" -> modele "par agence" ---
    def cols(table):
        return [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    for t in ("hints", "completions"):
        existing = cols(t)
        if existing and "user_id" in existing and "agence_id" not in existing:
            c.execute(f"DROP TABLE {t}")   # donnees de progression obsoletes : on repart propre

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE, pin TEXT, role TEXT);
    CREATE TABLE IF NOT EXISTS sessions(
      id INTEGER PRIMARY KEY, code TEXT UNIQUE, title TEXT, stacks TEXT,
      created_at REAL, created_by INTEGER);
    CREATE TABLE IF NOT EXISTS agences(
      id INTEGER PRIMARY KEY, session_id INTEGER, name TEXT, password TEXT,
      started_at REAL, finished_at REAL, current INTEGER DEFAULT 0,
      UNIQUE(session_id, name));
    CREATE TABLE IF NOT EXISTS eleves(
      id INTEGER PRIMARY KEY, agence_id INTEGER, name TEXT);
    CREATE TABLE IF NOT EXISTS missions(
      num INTEGER PRIMARY KEY, title TEXT, flag TEXT, briefing TEXT,
      hint_leger TEXT, hint_moyen TEXT, hint_fort TEXT, correction TEXT);
    CREATE TABLE IF NOT EXISTS hints(
      id INTEGER PRIMARY KEY, agence_id INTEGER, mission INTEGER, level TEXT, cost INTEGER, ts REAL);
    CREATE TABLE IF NOT EXISTS completions(
      id INTEGER PRIMARY KEY, agence_id INTEGER, mission INTEGER, ts REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    """)
    for m in MISSIONS_SEED:
        if not c.execute("SELECT 1 FROM missions WHERE num=?", (m["num"],)).fetchone():
            c.execute("""INSERT INTO missions(num,title,flag,briefing,hint_leger,hint_moyen,hint_fort,correction)
                         VALUES(?,?,?,?,?,?,?,?)""",
                      (m["num"], m["title"], m["flag"], m["briefing"],
                       m["hint_leger"], m["hint_moyen"], m["hint_fort"], m["correction"]))
    # remplit les indices/corriges restes en placeholder (sans ecraser tes modifications)
    for num, fields in FILLED_CONTENT.items():
        r = c.execute("SELECT hint_leger,hint_moyen,hint_fort,correction FROM missions WHERE num=?",
                      (num,)).fetchone()
        if not r:
            continue
        for i, col in enumerate(("hint_leger", "hint_moyen", "hint_fort", "correction")):
            placeholder = PH_CORR if col == "correction" else PH_HINT
            if r[i] == placeholder:
                c.execute(f"UPDATE missions SET {col}=? WHERE num=?", (fields[col], num))
    # ajoute les liens GitHub aux briefings qui ne les ont pas encore (sans ecraser tes modifs)
    for num, (marker, block) in START_BLOCKS.items():
        row = c.execute("SELECT briefing FROM missions WHERE num=?", (num,)).fetchone()
        if row and row[0] and marker not in row[0]:
            c.execute("UPDATE missions SET briefing=? WHERE num=?", (row[0] + block, num))
    if not c.execute("SELECT 1 FROM users WHERE role='prof'").fetchone():
        c.execute("INSERT INTO users(name,pin,role) VALUES(?,?,?)", ("bstorm", "CycyBerFormation2026", "prof"))
    conn.commit(); conn.close()

with app.app_context():
    init_db()

NB_MISSIONS = len(MISSIONS_SEED)

# ============================================================
#   HELPERS
# ============================================================
def current_prof():
    if session.get("role") != "prof":
        return None
    return db().execute("SELECT * FROM users WHERE id=?", (session.get("uid"),)).fetchone()

def current_agence():
    if session.get("role") != "agence":
        return None
    return db().execute("SELECT * FROM agences WHERE id=?", (session.get("aid"),)).fetchone()

def prof_required(f):
    @wraps(f)
    def w(*a, **k):
        if not current_prof():
            abort(403)
        return f(*a, **k)
    return w

def agence_required(f):
    @wraps(f)
    def w(*a, **k):
        if not current_agence():
            return redirect(url_for("login"))
        return f(*a, **k)
    return w

def hints_of(aid):
    return db().execute("SELECT * FROM hints WHERE agence_id=?", (aid,)).fetchall()

def completions_of(aid):
    return db().execute("SELECT mission FROM completions WHERE agence_id=?", (aid,)).fetchall()

def compute_score(a):
    """Score plancher a 0. 1600 - temps(100/h) - indices + 75/flag."""
    if not a["started_at"]:
        return BASE_POINTS
    end = a["finished_at"] or time.time()
    elapsed_h = (end - a["started_at"]) / 3600.0
    time_pts = elapsed_h * POINTS_PER_HOUR
    hint_pts = sum(h["cost"] for h in hints_of(a["id"]))
    flags = len(completions_of(a["id"]))
    s = BASE_POINTS - time_pts - hint_pts + FLAG_BONUS * flags
    return max(0, round(s))

def hint_points_used(aid):
    return sum(h["cost"] for h in hints_of(aid))

def hint_count_used(aid):
    return len(hints_of(aid))

def random_pin6():
    return "".join(random.choice(string.digits) for _ in range(6))

def gen_password():
    return random.choice(MDP_WORDS) + random_pin6()

def gen_session_code():
    letters = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3))
    digits = "".join(random.choice("23456789") for _ in range(3))
    return letters + digits

# ============================================================
#   AUTH
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mode = request.form.get("mode", "agence")
        if mode == "prof":
            name = request.form.get("pname", "").strip()
            pin = request.form.get("ppin", "").strip()
            u = db().execute("SELECT * FROM users WHERE name=? AND pin=? AND role='prof'",
                             (name, pin)).fetchone()
            if u:
                session.clear()
                session["role"] = "prof"; session["uid"] = u["id"]
                return redirect(url_for("admin"))
            flash("Identifiant professeur ou PIN incorrect.")
        else:
            code = request.form.get("code", "").strip().upper()
            aname = request.form.get("aname", "").strip()
            pwd = request.form.get("password", "").strip()
            row = db().execute("""SELECT a.* FROM agences a JOIN sessions s ON a.session_id=s.id
                                  WHERE s.code=? AND a.name=? AND a.password=?""",
                               (code, aname, pwd)).fetchone()
            if row:
                session.clear()
                session["role"] = "agence"; session["aid"] = row["id"]
                return redirect(url_for("parcours"))
            flash("Code session, nom d'agence ou mot de passe incorrect.")
    return render_template("login.html", title="Connexion")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ============================================================
#   PARCOURS AGENCE
# ============================================================
@app.route("/")
def index():
    if current_prof():
        return redirect(url_for("admin"))
    if current_agence():
        return redirect(url_for("parcours"))
    return redirect(url_for("login"))

@app.route("/parcours")
@agence_required
def parcours():
    a = current_agence()
    if not a["started_at"]:
        return render_template("enonce.html", title="Operation El Jefe", enonce=ENONCE_GLOBAL)
    if a["finished_at"]:
        return redirect(url_for("fin"))
    return redirect(url_for("mission", n=a["current"] or 1))

@app.route("/start", methods=["POST"])
@agence_required
def start():
    a = current_agence()
    if not a["started_at"]:
        db().execute("UPDATE agences SET started_at=?, current=1 WHERE id=?", (time.time(), a["id"]))
        db().commit()
    return redirect(url_for("mission", n=1))

@app.route("/mission/<int:n>", methods=["GET", "POST"])
def mission(n):
    prof = current_prof()
    a = current_agence()
    if not prof and not a:
        return redirect(url_for("login"))

    m = db().execute("SELECT * FROM missions WHERE num=?", (n,)).fetchone()
    if not m:
        abort(404)

    # --- apercu professeur : acces libre, correction ouverte, pas d'action ---
    if prof:
        ctx = dict(title=f"Mission {n}", m=m, n=n, nb=NB_MISSIONS,
                   u={"name": "Apercu prof", "current": NB_MISSIONS},
                   score=BASE_POINTS, hints_used=0, hint_pts=0, max_hints=MAX_HINTS,
                   taken={"leger", "moyen", "fort"}, costs=HINT_COST, correction_open=True,
                   is_done=False, msg=None, preview=True, unlocked=NB_MISSIONS,
                   started_ts=time.time(), flags_count=0,
                   base=BASE_POINTS, pph=POINTS_PER_HOUR, bonus=FLAG_BONUS)
        return render_template("mission.html", **ctx)

    # --- agence ---
    if not a["started_at"]:
        return redirect(url_for("parcours"))
    unlocked = a["current"] or 1
    if n > unlocked:                       # pas d'acces aux missions non debloquees
        return redirect(url_for("mission", n=unlocked))

    done = {r["mission"] for r in completions_of(a["id"])}
    correction_open = False
    msg = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "flag":
            prop = request.form.get("flag", "").strip()
            if prop == m["flag"]:
                if n not in done:
                    db().execute("INSERT INTO completions(agence_id,mission,ts) VALUES(?,?,?)",
                                 (a["id"], n, time.time()))
                    done.add(n)
                if n >= NB_MISSIONS:
                    db().execute("UPDATE agences SET finished_at=?, current=? WHERE id=?",
                                 (time.time(), NB_MISSIONS, a["id"]))
                    db().commit()
                    return redirect(url_for("fin"))
                if n + 1 > (a["current"] or 1):
                    db().execute("UPDATE agences SET current=? WHERE id=?", (n + 1, a["id"]))
                db().commit()
                return redirect(url_for("mission", n=n + 1))
            else:
                msg = ("err", "Flag incorrect. Verifie la casse et le format FLAG{...}.")
        elif action == "hint":
            level = request.form.get("level")
            err = None
            if level not in HINT_COST:
                err = "Niveau d'indice invalide."
            else:
                already = db().execute("SELECT 1 FROM hints WHERE agence_id=? AND mission=? AND level=?",
                                       (a["id"], n, level)).fetchone()
                if already:
                    pass  # deja debloque : idempotent
                elif hint_count_used(a["id"]) >= MAX_HINTS:
                    err = "Vous avez utilise vos 6 indices."
                else:
                    db().execute("INSERT INTO hints(agence_id,mission,level,cost,ts) VALUES(?,?,?,?,?)",
                                 (a["id"], n, level, HINT_COST[level], time.time()))
                    db().commit()
            if wants_json():
                if err:
                    return jsonify(ok=False, error=err), 400
                taken2 = {h["level"] for h in db().execute(
                    "SELECT level FROM hints WHERE agence_id=? AND mission=?", (a["id"], n)).fetchall()}
                html = render_template("_hint_photo.html", lvl=level, lab=HINT_LABELS[level], m=m,
                                       taken=taken2, costs=HINT_COST, hints_used=hint_count_used(a["id"]),
                                       max_hints=MAX_HINTS, preview=False, n=n)
                return jsonify(ok=True, level=level, html=html, score=compute_score(a),
                               hints_used=hint_count_used(a["id"]),
                               hint_pts=hint_points_used(a["id"]), max_hints=MAX_HINTS)
            if err:
                msg = ("err", err)
            return redirect(url_for("mission", n=n))
        elif action == "correction":
            code = request.form.get("code", "").strip()
            if code == m["flag"]:
                correction_open = True
            else:
                msg = ("err", "Code incorrect : il faut le flag de cette mission.")

    taken = {h["level"] for h in db().execute(
        "SELECT level FROM hints WHERE agence_id=? AND mission=?", (a["id"], n)).fetchall()}
    ctx = dict(title=f"Mission {n}", m=m, n=n, nb=NB_MISSIONS, u=a, unlocked=unlocked,
               score=compute_score(a), hints_used=hint_count_used(a["id"]),
               hint_pts=hint_points_used(a["id"]), max_hints=MAX_HINTS,
               taken=taken, costs=HINT_COST, correction_open=correction_open,
               is_done=(n in done), msg=msg, preview=False,
               started_ts=a["started_at"] or time.time(),
               flags_count=len(done), base=BASE_POINTS, pph=POINTS_PER_HOUR, bonus=FLAG_BONUS)
    return render_template("mission.html", **ctx)

@app.route("/fin")
@agence_required
def fin():
    a = current_agence()
    return render_template("fin.html", title="Mission terminee", u=a,
                           score=compute_score(a), nb=NB_MISSIONS,
                           hints_used=hint_count_used(a["id"]),
                           flags=len(completions_of(a["id"])))

def board_for_session(session_id):
    rows = db().execute("SELECT * FROM agences WHERE session_id=?", (session_id,)).fetchall()
    data = []
    for r in rows:
        data.append(dict(name=r["name"], score=compute_score(r),
                         flags=len(completions_of(r["id"])),
                         hints=hint_count_used(r["id"]),
                         finished=r["finished_at"] or float("inf"),
                         started=bool(r["started_at"])))
    data.sort(key=lambda x: (-x["score"], x["finished"], x["hints"]))
    return data

@app.route("/classement")
@agence_required
def classement():
    a = current_agence()
    data = board_for_session(a["session_id"])
    s = db().execute("SELECT * FROM sessions WHERE id=?", (a["session_id"],)).fetchone()
    return render_template("classement.html", title="Classement", data=data, sess=s)

# ============================================================
#   ADMIN (PROF)
# ============================================================
def wants_json():
    return request.headers.get("X-Requested-With") == "fetch"

def session_view(s):
    agences = db().execute("SELECT id FROM agences WHERE session_id=?", (s["id"],)).fetchall()
    nb_el = db().execute("""SELECT COUNT(*) c FROM eleves e JOIN agences a ON e.agence_id=a.id
                            WHERE a.session_id=?""", (s["id"],)).fetchone()["c"]
    return dict(row=s, nb_agences=len(agences), nb_eleves=nb_el)

def agence_view(ag):
    eleves = db().execute("SELECT * FROM eleves WHERE agence_id=? ORDER BY id", (ag["id"],)).fetchall()
    return dict(row=ag, eleves=eleves, nb_eleves=len(eleves),
                score=compute_score(ag), flags=len(completions_of(ag["id"])),
                hints=hint_count_used(ag["id"]), started=bool(ag["started_at"]),
                finished=bool(ag["finished_at"]))

@app.route("/admin")
@prof_required
def admin():
    rows = db().execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
    sessions = [session_view(s) for s in rows]
    missions = db().execute("SELECT * FROM missions ORDER BY num").fetchall()
    profs = db().execute("SELECT * FROM users WHERE role='prof' ORDER BY name").fetchall()
    return render_template("admin.html", title="Espace professeur",
                           sessions=sessions, missions=missions, profs=profs,
                           max_agences=MAX_AGENCES, max_eleves=MAX_ELEVES,
                           suggest_code=gen_session_code())

@app.route("/admin/session/<int:sid>")
@prof_required
def session_detail(sid):
    s = db().execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if not s:
        abort(404)
    rows = db().execute("SELECT * FROM agences WHERE session_id=? ORDER BY id", (sid,)).fetchall()
    agences = [agence_view(a) for a in rows]
    board = board_for_session(sid)
    return render_template("session.html", title=s["title"], sess=s, agences=agences,
                           board=board, max_agences=MAX_AGENCES, max_eleves=MAX_ELEVES)

@app.route("/admin/agence/<int:aid>")
@prof_required
def agence_detail(aid):
    ag = db().execute("SELECT * FROM agences WHERE id=?", (aid,)).fetchone()
    if not ag:
        abort(404)
    s = db().execute("SELECT * FROM sessions WHERE id=?", (ag["session_id"],)).fetchone()
    return render_template("agence.html", title=ag["name"], sess=s,
                           ag=agence_view(ag), max_eleves=MAX_ELEVES)

def build_session_code(mnemonic, stacks_list):
    """Code de connexion = 1 LETTRE au hasard + code mnemonique + 1 stack tiree au hasard."""
    import re
    mnemonic = re.sub(r"[^A-Z0-9]", "", (mnemonic or "").upper())
    if not mnemonic:
        mnemonic = re.sub(r"[^A-Z0-9]", "", gen_session_code())
    stack = ""
    if stacks_list:
        stack = re.sub(r"[^A-Z0-9]", "", random.choice(stacks_list).upper())
    letter = random.choice(string.ascii_uppercase)
    return letter + mnemonic + stack

@app.route("/admin/session/create", methods=["POST"])
@prof_required
def admin_session_create():
    title = request.form.get("title", "").strip()
    mnemonic = request.form.get("code", "").strip()
    s1 = request.form.get("stack1", "").strip()
    s2 = request.form.get("stack2", "").strip()
    stacks_list = [x for x in (s1, s2) if x]
    stacks = ", ".join(stacks_list)
    if not title:
        if wants_json():
            return jsonify(ok=False, error="Intitule requis."), 400
        return redirect(url_for("admin"))
    s = None
    for _ in range(6):   # regenere la lettre en cas de collision
        code = build_session_code(mnemonic, stacks_list)
        try:
            cur = db().execute("INSERT INTO sessions(code,title,stacks,created_at,created_by) VALUES(?,?,?,?,?)",
                               (code, title, stacks, time.time(), current_prof()["id"]))
            db().commit()
            s = db().execute("SELECT * FROM sessions WHERE id=?", (cur.lastrowid,)).fetchone()
            break
        except sqlite3.IntegrityError:
            continue
    if s is None:
        if wants_json():
            return jsonify(ok=False, error="Impossible de generer un code unique, reessaie."), 400
        flash("Impossible de generer un code unique.")
        return redirect(url_for("admin"))
    if wants_json():
        html = render_template("_session_card.html", s=session_view(s))
        return jsonify(ok=True, html=html)
    return redirect(url_for("admin"))

# Suppression de session volontairement non implementee : une session ne peut pas etre supprimee.

@app.route("/admin/agence/create", methods=["POST"])
@prof_required
def admin_agence_create():
    sid = request.form.get("session_id")
    name = request.form.get("name", "").strip()
    n = db().execute("SELECT COUNT(*) c FROM agences WHERE session_id=?", (sid,)).fetchone()["c"]
    if n >= MAX_AGENCES:
        if wants_json():
            return jsonify(ok=False, error=f"Maximum {MAX_AGENCES} agences."), 400
        return redirect(url_for("session_detail", sid=sid))
    if not name:
        if wants_json():
            return jsonify(ok=False, error="Nom requis."), 400
        return redirect(url_for("session_detail", sid=sid))
    try:
        cur = db().execute("INSERT INTO agences(session_id,name,password,current) VALUES(?,?,?,0)",
                           (sid, name, gen_password()))
        db().commit()
        ag = db().execute("SELECT * FROM agences WHERE id=?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        if wants_json():
            return jsonify(ok=False, error=f"L'agence '{name}' existe deja."), 400
        flash(f"Une agence '{name}' existe deja dans cette session.")
        return redirect(url_for("session_detail", sid=sid))
    if wants_json():
        html = render_template("_agence_card.html", a=agence_view(ag), cidx=n % 4, max_eleves=MAX_ELEVES)
        return jsonify(ok=True, html=html)
    return redirect(url_for("session_detail", sid=sid))

@app.route("/admin/agence/delete/<int:aid>", methods=["POST"])
@prof_required
def admin_agence_delete(aid):
    sid = db().execute("SELECT session_id FROM agences WHERE id=?", (aid,)).fetchone()
    db().execute("DELETE FROM hints WHERE agence_id=?", (aid,))
    db().execute("DELETE FROM completions WHERE agence_id=?", (aid,))
    db().execute("DELETE FROM eleves WHERE agence_id=?", (aid,))
    db().execute("DELETE FROM agences WHERE id=?", (aid,))
    db().commit()
    if wants_json():
        return jsonify(ok=True)
    return redirect(url_for("session_detail", sid=sid["session_id"]) if sid else url_for("admin"))

@app.route("/admin/agence/reset/<int:aid>", methods=["POST"])
@prof_required
def admin_agence_reset(aid):
    db().execute("DELETE FROM hints WHERE agence_id=?", (aid,))
    db().execute("DELETE FROM completions WHERE agence_id=?", (aid,))
    db().execute("UPDATE agences SET started_at=NULL, finished_at=NULL, current=0 WHERE id=?", (aid,))
    db().commit()
    if wants_json():
        return jsonify(ok=True)
    ag = db().execute("SELECT session_id FROM agences WHERE id=?", (aid,)).fetchone()
    return redirect(url_for("session_detail", sid=ag["session_id"]) if ag else url_for("admin"))

@app.route("/admin/agence/newpwd/<int:aid>", methods=["POST"])
@prof_required
def admin_agence_newpwd(aid):
    pwd = gen_password()
    db().execute("UPDATE agences SET password=? WHERE id=?", (pwd, aid))
    db().commit()
    if wants_json():
        return jsonify(ok=True, password=pwd)
    ag = db().execute("SELECT session_id FROM agences WHERE id=?", (aid,)).fetchone()
    return redirect(url_for("session_detail", sid=ag["session_id"]) if ag else url_for("admin"))

@app.route("/admin/eleve/create", methods=["POST"])
@prof_required
def admin_eleve_create():
    aid = request.form.get("agence_id")
    name = request.form.get("name", "").strip()
    n = db().execute("SELECT COUNT(*) c FROM eleves WHERE agence_id=?", (aid,)).fetchone()["c"]
    if n >= MAX_ELEVES:
        if wants_json():
            return jsonify(ok=False, error=f"Maximum {MAX_ELEVES} eleves."), 400
        return redirect(url_for("agence_detail", aid=aid))
    if not name:
        if wants_json():
            return jsonify(ok=False, error="Nom requis."), 400
        return redirect(url_for("agence_detail", aid=aid))
    cur = db().execute("INSERT INTO eleves(agence_id,name) VALUES(?,?)", (aid, name))
    db().commit()
    if wants_json():
        e = db().execute("SELECT * FROM eleves WHERE id=?", (cur.lastrowid,)).fetchone()
        html = render_template("_eleve_card.html", e=e, cidx=n % 4)
        return jsonify(ok=True, html=html, count=n + 1)
    return redirect(url_for("agence_detail", aid=aid))

@app.route("/admin/eleve/delete/<int:eid>", methods=["POST"])
@prof_required
def admin_eleve_delete(eid):
    row = db().execute("SELECT agence_id FROM eleves WHERE id=?", (eid,)).fetchone()
    db().execute("DELETE FROM eleves WHERE id=?", (eid,))
    db().commit()
    if wants_json():
        return jsonify(ok=True)
    return redirect(url_for("agence_detail", aid=row["agence_id"]) if row else url_for("admin"))

@app.route("/admin/prof/create", methods=["POST"])
@prof_required
def admin_prof_create():
    name = request.form.get("name", "").strip()
    pin = request.form.get("pin", "").strip() or random_pin6()
    if name:
        try:
            db().execute("INSERT INTO users(name,pin,role) VALUES(?,?,'prof')", (name, pin))
            db().commit()
            flash(f"Professeur cree : {name} / PIN {pin}")
        except sqlite3.IntegrityError:
            flash(f"Le nom '{name}' existe deja.")
    return redirect(url_for("admin"))

@app.route("/admin/mission/<int:num>", methods=["POST"])
@prof_required
def admin_mission(num):
    f = request.form
    db().execute("""UPDATE missions SET title=?, flag=?, briefing=?, hint_leger=?, hint_moyen=?,
                    hint_fort=?, correction=? WHERE num=?""",
                 (f.get("title"), f.get("flag"), f.get("briefing"), f.get("hint_leger"),
                  f.get("hint_moyen"), f.get("hint_fort"), f.get("correction"), num))
    db().commit()
    flash(f"Mission {num} mise a jour.")
    return redirect(url_for("admin") + f"#mission{num}")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
