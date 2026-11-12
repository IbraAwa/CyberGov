import os, sqlite3, random, string, time
from functools import wraps
from flask import (Flask, g, redirect, render_template, request, session, url_for, flash, abort)

APP_TITLE = "Operation El Jefe"
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "labo.db"))

# ---- Bareme (modifiable) ----
BASE_POINTS = 1600          # 16 h
POINTS_PER_HOUR = 100       # le temps coute 100 pts/h
HINT_COST = {"leger": 50, "moyen": 125, "fort": 200}
MAX_HINTS = 6               # nombre total d'indices autorises
FLAG_BONUS = 75            # chaque flag valide rapporte des points (evite les scores a 0)

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

ENONCE_GLOBAL = """
<p>Quatre services (FBI, CIA, NCIS, DEA) se disputent un dossier : faire tomber <strong>El Jefe</strong>, chef du cartel de Sinaloa. Le premier a reconstituer toute l'operation gagne.</p>
<p>La mission se joue en <strong>5 etapes</strong>. A chaque etape, un briefing, un objectif, et un <strong>flag</strong> a trouver pour passer a la suivante.</p>
<p>Vous disposez de <strong>6 indices maximum</strong> pour toute la mission (leger, moyen, fort). Chaque indice et chaque heure ecoulee grignotent votre score : reflechissez avant de demander de l'aide.</p>
<p>On n'attaque que les systemes prevus pour l'exercice. Bonne chasse, agent.</p>
"""

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
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, name TEXT UNIQUE, pin TEXT, role TEXT,
      started_at REAL, finished_at REAL, current INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS missions(
      num INTEGER PRIMARY KEY, title TEXT, flag TEXT, briefing TEXT,
      hint_leger TEXT, hint_moyen TEXT, hint_fort TEXT, correction TEXT);
    CREATE TABLE IF NOT EXISTS hints(
      id INTEGER PRIMARY KEY, user_id INTEGER, mission INTEGER, level TEXT, cost INTEGER, ts REAL);
    CREATE TABLE IF NOT EXISTS completions(
      id INTEGER PRIMARY KEY, user_id INTEGER, mission INTEGER, ts REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    """)
    # seed missions
    for m in MISSIONS_SEED:
        if not c.execute("SELECT 1 FROM missions WHERE num=?", (m["num"],)).fetchone():
            c.execute("""INSERT INTO missions(num,title,flag,briefing,hint_leger,hint_moyen,hint_fort,correction)
                         VALUES(?,?,?,?,?,?,?,?)""",
                      (m["num"], m["title"], m["flag"], m["briefing"],
                       m["hint_leger"], m["hint_moyen"], m["hint_fort"], m["correction"]))
    # seed prof bootstrap
    if not c.execute("SELECT 1 FROM users WHERE role='prof'").fetchone():
        c.execute("INSERT INTO users(name,pin,role,current) VALUES(?,?,?,0)", ("prof", "eljefe2026", "prof"))
    conn.commit(); conn.close()

with app.app_context():
    init_db()

NB_MISSIONS = len(MISSIONS_SEED)

# ============================================================
#   HELPERS
# ============================================================
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return db().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not current_user():
            return redirect(url_for("login"))
        return f(*a, **k)
    return w

def prof_required(f):
    @wraps(f)
    def w(*a, **k):
        u = current_user()
        if not u or u["role"] != "prof":
            abort(403)
        return f(*a, **k)
    return w

def hints_of(uid):
    return db().execute("SELECT * FROM hints WHERE user_id=?", (uid,)).fetchall()

def completions_of(uid):
    return db().execute("SELECT mission FROM completions WHERE user_id=?", (uid,)).fetchall()

def compute_score(u):
    """Score plancher a 0. 1600 - temps(100/h) - indices + 75/flag."""
    if not u["started_at"]:
        return BASE_POINTS
    end = u["finished_at"] or time.time()
    elapsed_h = (end - u["started_at"]) / 3600.0
    time_pts = elapsed_h * POINTS_PER_HOUR
    hint_pts = sum(h["cost"] for h in hints_of(u["id"]))
    flags = len(completions_of(u["id"]))
    s = BASE_POINTS - time_pts - hint_pts + FLAG_BONUS * flags
    return max(0, round(s))

def hint_points_used(uid):
    return sum(h["cost"] for h in hints_of(uid))

def hint_count_used(uid):
    return len(hints_of(uid))

def random_pin():
    return "".join(random.choice(string.digits) for _ in range(4))

# ============================================================
#   AUTH
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        pin = request.form.get("pin", "").strip()
        u = db().execute("SELECT * FROM users WHERE name=? AND pin=?", (name, pin)).fetchone()
        if u:
            session["uid"] = u["id"]
            return redirect(url_for("admin") if u["role"] == "prof" else url_for("parcours"))
        flash("Identifiant ou code PIN incorrect.")
    return render_template("login.html", title="Connexion")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ============================================================
#   PARCOURS ELEVE
# ============================================================
@app.route("/")
def index():
    u = current_user()
    if not u:
        return redirect(url_for("login"))
    return redirect(url_for("admin") if u["role"] == "prof" else url_for("parcours"))

@app.route("/parcours")
@login_required
def parcours():
    u = current_user()
    if u["role"] == "prof":
        return redirect(url_for("admin"))
    if not u["started_at"]:
        return render_template("enonce.html", title="Operation El Jefe", enonce=ENONCE_GLOBAL)
    if u["finished_at"]:
        return redirect(url_for("fin"))
    return redirect(url_for("mission", n=u["current"] or 1))

@app.route("/start", methods=["POST"])
@login_required
def start():
    u = current_user()
    if u["role"] != "prof" and not u["started_at"]:
        db().execute("UPDATE users SET started_at=?, current=1 WHERE id=?", (time.time(), u["id"]))
        db().commit()
    return redirect(url_for("mission", n=1))

@app.route("/mission/<int:n>", methods=["GET", "POST"])
@login_required
def mission(n):
    u = current_user()
    if u["role"] == "prof":
        # apercu prof : acces libre
        pass
    else:
        if not u["started_at"]:
            return redirect(url_for("parcours"))
        if n > (u["current"] or 1):
            return redirect(url_for("mission", n=u["current"] or 1))
    m = db().execute("SELECT * FROM missions WHERE num=?", (n,)).fetchone()
    if not m:
        abort(404)
    done = {r["mission"] for r in completions_of(u["id"])}
    correction_open = (u["role"] == "prof")
    msg = None

    if request.method == "POST" and u["role"] != "prof":
        action = request.form.get("action")
        if action == "flag":
            prop = request.form.get("flag", "").strip()
            if prop == m["flag"]:
                if n not in done:
                    db().execute("INSERT INTO completions(user_id,mission,ts) VALUES(?,?,?)",
                                 (u["id"], n, time.time()))
                    done.add(n)
                if n >= NB_MISSIONS:
                    db().execute("UPDATE users SET finished_at=?, current=? WHERE id=?",
                                 (time.time(), NB_MISSIONS, u["id"]))
                    db().commit()
                    return redirect(url_for("fin"))
                db().execute("UPDATE users SET current=? WHERE id=?", (n + 1, u["id"]))
                db().commit()
                return redirect(url_for("mission", n=n + 1))
            else:
                msg = ("err", "Flag incorrect. Verifie la casse et le format FLAG{...}.")
        elif action == "hint":
            level = request.form.get("level")
            if level in HINT_COST:
                already = db().execute("SELECT 1 FROM hints WHERE user_id=? AND mission=? AND level=?",
                                       (u["id"], n, level)).fetchone()
                if hint_count_used(u["id"]) >= MAX_HINTS:
                    msg = ("err", "Vous avez utilise vos 6 indices.")
                elif already:
                    msg = ("err", "Cet indice est deja debloque.")
                else:
                    db().execute("INSERT INTO hints(user_id,mission,level,cost,ts) VALUES(?,?,?,?,?)",
                                 (u["id"], n, level, HINT_COST[level], time.time()))
                    db().commit()
            return redirect(url_for("mission", n=n))
        elif action == "correction":
            code = request.form.get("code", "").strip()
            if code == m["flag"]:
                correction_open = True
            else:
                msg = ("err", "Code incorrect : il faut le flag de cette mission.")

    taken = {h["level"] for h in db().execute(
        "SELECT level FROM hints WHERE user_id=? AND mission=?", (u["id"], n)).fetchall()}
    ctx = dict(title=f"Mission {n}", m=m, n=n, nb=NB_MISSIONS, u=u,
               score=compute_score(u), hints_used=hint_count_used(u["id"]),
               hint_pts=hint_points_used(u["id"]), max_hints=MAX_HINTS,
               taken=taken, costs=HINT_COST, correction_open=correction_open,
               is_done=(n in done), msg=msg,
               started_ts=u["started_at"] or time.time(),
               flags_count=len(done), base=BASE_POINTS, pph=POINTS_PER_HOUR, bonus=FLAG_BONUS)
    return render_template("mission.html", **ctx)

@app.route("/fin")
@login_required
def fin():
    u = current_user()
    return render_template("fin.html", title="Mission terminee", u=u,
                           score=compute_score(u), nb=NB_MISSIONS,
                           hints_used=hint_count_used(u["id"]),
                           flags=len(completions_of(u["id"])))

@app.route("/classement")
@login_required
def classement():
    rows = db().execute("SELECT * FROM users WHERE role='eleve'").fetchall()
    data = []
    for r in rows:
        data.append(dict(name=r["name"], score=compute_score(r),
                         flags=len(completions_of(r["id"])),
                         hints=hint_count_used(r["id"]),
                         finished=r["finished_at"] or float("inf"),
                         started=bool(r["started_at"])))
    data.sort(key=lambda x: (-x["score"], x["finished"], x["hints"]))
    return render_template("classement.html", title="Classement", data=data)

# ============================================================
#   ADMIN (PROF)
# ============================================================
@app.route("/admin")
@prof_required
def admin():
    users = db().execute("SELECT * FROM users ORDER BY role, name").fetchall()
    missions = db().execute("SELECT * FROM missions ORDER BY num").fetchall()
    board = []
    for r in db().execute("SELECT * FROM users WHERE role='eleve'").fetchall():
        board.append(dict(name=r["name"], score=compute_score(r),
                          flags=len(completions_of(r["id"])), hints=hint_count_used(r["id"]),
                          finished=r["finished_at"] or float("inf")))
    board.sort(key=lambda x: (-x["score"], x["finished"]))
    return render_template("admin.html", title="Espace professeur", users=users,
                           missions=missions, board=board)

@app.route("/admin/create", methods=["POST"])
@prof_required
def admin_create():
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "eleve")
    pin = request.form.get("pin", "").strip() or random_pin()
    if name:
        try:
            db().execute("INSERT INTO users(name,pin,role,current) VALUES(?,?,?,0)", (name, pin, role))
            db().commit()
            flash(f"Compte cree : {name} / PIN {pin} ({role})")
        except sqlite3.IntegrityError:
            flash(f"Le nom '{name}' existe deja.")
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:uid>", methods=["POST"])
@prof_required
def admin_delete(uid):
    db().execute("DELETE FROM hints WHERE user_id=?", (uid,))
    db().execute("DELETE FROM completions WHERE user_id=?", (uid,))
    db().execute("DELETE FROM users WHERE id=?", (uid,))
    db().commit()
    return redirect(url_for("admin"))

@app.route("/admin/reset/<int:uid>", methods=["POST"])
@prof_required
def admin_reset(uid):
    db().execute("DELETE FROM hints WHERE user_id=?", (uid,))
    db().execute("DELETE FROM completions WHERE user_id=?", (uid,))
    db().execute("UPDATE users SET started_at=NULL, finished_at=NULL, current=0 WHERE id=?", (uid,))
    db().commit()
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
