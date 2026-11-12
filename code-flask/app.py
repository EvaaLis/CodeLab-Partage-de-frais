from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """

<h1 style="text-align: center;">Partage de frais</h1>

<h2>Groupes</h2>
<ul>
  {% for groupe in groupes %}
    <li>
      {% if groupe["id"] == groupe_actuel["id"] %}
        <strong>{{ groupe["nom"] }} (actif)</strong>
      {% else %}
        <a href="/groupe/{{ groupe['id'] }}">{{ groupe["nom"] }}</a>
      {% endif %}
    </li>
  {% endfor %}
</ul>

<form method="post" action="/groupes">
  <input name="nom_groupe" placeholder="Nom du groupe" required>
  <button>Ajouter un groupe</button>
</form>

<h2>Durée des vacances</h2>

<form method="post" action="/vacances">
    <input type="hidden" name="groupe_id" value="{{ groupe_actuel['id'] }}">

    <label>Date de début :</label>
    <input type="date" name="date_debut" value="{{ groupe_actuel['date_debut'] or '' }}" required>

    <br><br>

    <label>Date de fin :</label>
    <input type="date" name="date_fin" value="{{ groupe_actuel['date_fin'] or '' }}" required>

    <br><br>

    <button type="submit">Enregistrer les dates</button>

</form>
<h2>Membres du groupe : {{ groupe_actuel["nom"] }}</h2>
<ul>
  {% for membre in membres %}
    <li>{{ membre["nom"] }}</li>
  {% endfor %}
</ul>

<form method="post" action="/membres">
  <input type="hidden" name="groupe_id" value="{{ groupe_actuel['id'] }}">
  <input name="nom" placeholder="Nom" required>
  <button>Ajouter un membre</button>
  
  {% if request.args.get("erreur") == "existe" %}
    <p style="color: red;">Ce nom d'utilisateur existe déjà !</p>
{% endif %}
</form>


<h2>Ajouter une dépense</h2>

<form method="post" action="/depenses">
    <input type="hidden" name="groupe_id" value="{{ groupe_actuel['id'] }}">

    <label>Libellé :</label>
    <input type="text" name="libelle" required>
<br>
    <label>Montant :</label>
    <input type="number" name="montant" step="0.01" required>
<br>
    <label>Date :</label>
    <input type="date" name="date" required>
<br>
    <label>Payeur :</label>
    <select name="payeur" required>
        <option value="">Choisir un payeur</option>
        {% for membre in membres %}
            <option value="{{ membre['id'] }}">
                {{ membre['nom'] }}
            </option>
        {% endfor %}
    </select>
<br>

<label>Participants :</label>

{% for membre in membres %}
    <input type="checkbox" name="participants" value="{{ membre['id'] }}">
    {{ membre['nom'] }}
    <br>
{% endfor %}

    <button type="submit">Ajouter la dépense</button>

</form>

<h2>Supprimer une dépense</h2>

<form method="post" action="/supprimer_depense">
    <input type="hidden" name="groupe_id" value="{{ groupe_actuel['id'] }}">

    <label>Choisir la dépense à supprimer :</label>

    <select name="depense_id" required>
        <option value="">Choisir une dépense</option>

        {% for depense in depenses %}
            <option value="{{ depense['id'] }}">
                {{ depense['libelle'] }} - {{ depense['montant_centimes'] / 100 }} €
            </option>
        {% endfor %}

    </select>

    <button type="submit">Supprimer la dépense</button>

</form>

<h2>Soldes</h2>
<ul>
  {% for membre in membres %}
    <li>{{ membre["nom"] }} : {{ soldes[membre["id"]] / 100 }} €</li>
  {% endfor %}
</ul>

<form method="get" action="/groupe/{{ groupe_actuel['id'] }}">
  <button name="remboursement" value="1">Remboursement</button>
</form>

{% if remboursements is not none %}
<ul>
  {% for creancier, debiteur, montant in remboursements %}
    <li>{{ noms[debiteur] }} doit {{ montant / 100 }} € à {{ noms[creancier] }}</li>
  {% endfor %}
</ul>
{% endif %}

"""


app = Flask(__name__)


# Page d'accueil : affiche le groupe demandé (ou le premier groupe par défaut).
@app.get("/")
@app.get("/groupe/<int:groupe_id>")
def accueil(groupe_id=None):
    with ouvrir_base() as conn:
        groupes = conn.execute("SELECT id, nom FROM groupes").fetchall()

        # Si aucun groupe_id n'est passé dans l'URL, on prend le premier
        if groupe_id is None and groupes:
            groupe_id = groupes[0]["id"]

        groupe_actuel = conn.execute("SELECT * FROM groupes WHERE id = ?", [groupe_id]).fetchone()
        if not groupe_actuel and groupes:
            return redirect(f"/groupe/{groupes[0]['id']}")

        membres = conn.execute("SELECT id, nom FROM membres WHERE groupe_id = ?", [groupe_id]).fetchall()
        depenses = conn.execute("SELECT id, libelle, montant_centimes FROM depenses WHERE groupe_id = ?", [groupe_id]).fetchall()
        soldes = calculer_soldes(groupe_id)
        noms = {membre["id"]: membre["nom"] for membre in membres}

        remboursements = None
        if request.args.get("remboursement"):
            remboursements = calculer_remboursements(groupe_id)

    return render_template_string(
        PAGE,
        groupes=groupes,
        groupe_actuel=groupe_actuel,
        membres=membres,
        depenses=depenses,
        soldes=soldes,
        noms=noms,
        remboursements=remboursements
    )


# Crée un groupe et redirige vers sa page
@app.post("/groupes")
def ajouter_groupe():
    nom = request.form.get("nom_groupe", "").strip()
    if nom:
        with ouvrir_base() as conn:
            cur = conn.execute(
                "INSERT INTO groupes (nom, date_debut, date_fin) VALUES (?, '', '')",
                [nom]
            )
            nouveau_id = cur.lastrowid
        return redirect(f"/groupe/{nouveau_id}")
    return redirect("/")


# Ajoute un membre obligatoirement affilié au groupe actuel
@app.post("/membres")
def ajouter_membre():
    nom = request.form.get("nom", "").strip()
    groupe_id = request.form.get("groupe_id")

    if nom and groupe_id:
        with ouvrir_base() as conn:

            existe = conn.execute(
                "SELECT id FROM membres WHERE nom = ? AND groupe_id = ?",
                [nom, groupe_id]
            ).fetchone()

            if existe:
                return redirect(f"/groupe/{groupe_id}?erreur=existe")

            conn.execute(
                "INSERT INTO membres (groupe_id, nom) VALUES (?, ?)",
                [groupe_id, nom]
            )

    return redirect(f"/groupe/{groupe_id}")
        


# Enregistre les dates du séjour pour le groupe actuel
@app.post("/vacances")
def enregistrer_vacances():
    groupe_id = request.form.get("groupe_id")
    date_debut = request.form.get("date_debut", "").strip()
    date_fin = request.form.get("date_fin", "").strip()
    if groupe_id and date_debut and date_fin:
        with ouvrir_base() as conn:
            conn.execute(
                "UPDATE groupes SET date_debut = ?, date_fin = ? WHERE id = ?",
                [date_debut, date_fin, groupe_id]
            )
    return redirect(f"/groupe/{groupe_id}")


# Ajoute une dépense au groupe actuel
@app.post("/depenses")
def ajouter_depense():
    groupe_id = request.form.get("groupe_id")
    libelle = request.form.get("libelle", "").strip()
    montant_str = request.form.get("montant", "").strip().replace(",", ".")
    date = request.form.get("date", "").strip()
    payeur_id = request.form.get("payeur", "").strip()
    participants = request.form.getlist("participants")

    if not groupe_id or not libelle or not montant_str or not date or not payeur_id or not participants:
        return redirect(f"/groupe/{groupe_id}")

    try:
        montant_centimes = round(float(montant_str) * 100)
        payeur_id = int(payeur_id)
    except (ValueError, TypeError):
        return redirect(f"/groupe/{groupe_id}")

    if montant_centimes <= 0:
        return redirect(f"/groupe/{groupe_id}")

    with ouvrir_base() as conn:
        groupe = conn.execute("SELECT date_debut, date_fin FROM groupes WHERE id = ?", [groupe_id]).fetchone()
        if groupe and groupe["date_debut"] and groupe["date_fin"]:
            if date < groupe["date_debut"] or date > groupe["date_fin"]:
                return redirect(f"/groupe/{groupe_id}")

        cur = conn.execute(
            "INSERT INTO depenses (groupe_id, libelle, montant_centimes, date, payeur_id) VALUES (?, ?, ?, ?, ?)",
            [groupe_id, libelle, montant_centimes, date, payeur_id]
        )
        for membre_id in participants:
            try:
                conn.execute(
                    "INSERT INTO participants (depense_id, membre_id) VALUES (?, ?)",
                    [cur.lastrowid, int(membre_id)]
                )
            except (ValueError, TypeError):
                continue

    return redirect(f"/groupe/{groupe_id}")


# Supprime une dépense du groupe actuel
@app.post("/supprimer_depense")
def supprimer_depense():
    groupe_id = request.form.get("groupe_id")
    depense_id = request.form.get("depense_id")
    if depense_id:
        with ouvrir_base() as conn:
            conn.execute("DELETE FROM participants WHERE depense_id = ?", [depense_id])
            conn.execute("DELETE FROM depenses WHERE id = ?", [depense_id])
    return redirect(f"/groupe/{groupe_id}")


def repartir_depense(montant_centimes, participants):
    if montant_centimes <= 0 or not participants:
        raise ValueError("Dépense invalide")

    part = montant_centimes // len(participants)
    reste = montant_centimes % len(participants)

    parts = {}
    for i, participant_id in enumerate(participants):
        parts[participant_id] = part + (1 if i < reste else 0)

    return parts


def calculer_soldes(groupe_id):
    with ouvrir_base() as conn:
        membres = conn.execute(
            "SELECT id FROM membres WHERE groupe_id = ?",
            [groupe_id]
        ).fetchall()

        depenses = conn.execute(
            "SELECT id, montant_centimes, payeur_id FROM depenses WHERE groupe_id = ?",
            [groupe_id]
        ).fetchall()

        soldes = {membre["id"]: 0 for membre in membres}

        for depense in depenses:
            participants = conn.execute(
                "SELECT membre_id FROM participants WHERE depense_id = ? ORDER BY rowid",
                [depense["id"]]
            ).fetchall()

            ids_participants = [p["membre_id"] for p in participants]
            if not ids_participants:
                continue

            parts = repartir_depense(
                depense["montant_centimes"],
                ids_participants
            )

            if depense["payeur_id"] in soldes:
                soldes[depense["payeur_id"]] += depense["montant_centimes"]

            for membre_id, part in parts.items():
                if membre_id in soldes:
                    soldes[membre_id] -= part

    return soldes


def calculer_remboursements(groupe_id):
    remboursement = []
    soldes = calculer_soldes(groupe_id).copy()
    with ouvrir_base() as conn:
        membres = conn.execute(
            "SELECT id FROM membres WHERE groupe_id = ?",
            [groupe_id]
        ).fetchall()
        membres = [membre["id"] for membre in membres]
        positif = [m for m in membres if soldes.get(m, 0) > 0]
        negatif = [m for m in membres if soldes.get(m, 0) < 0]
        while positif and negatif:
            x = len(positif) - 1
            y = len(negatif) - 1
            montant = min(soldes[positif[x]], -soldes[negatif[y]])
            remboursement.append((positif[x], negatif[y], montant))
            soldes[positif[x]] -= montant
            soldes[negatif[y]] += montant
            if soldes[positif[x]] == 0:
                positif.pop()
            if soldes[negatif[y]] == 0:
                negatif.pop()
    return remboursement


if __name__ == "__main__":
    app.run(debug=True)
