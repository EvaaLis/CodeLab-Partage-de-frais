from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """

<h1 style="text-align: center;">Partage de frais</h1>

<h2>Groupes</h2>

<ul>
    {% for groupe in groupes %}
        <li>{{ groupe["nom"] }}</li>
    {% endfor %}
</ul>

<form method="post" action="/groupes">

    <input name="nom_groupe" placeholder="Nom du groupe" required>

    <button type="submit">Créer un groupe</button>

<h2>Membres</h2>
<ul>
  {% for membre in membres %}
    <li>{{ membre["nom"] }}</li>
  {% endfor %}
</ul>

<form method="post" action="/membres">
  <input name="nom" placeholder="Nom" required>
  <button>Ajouter</button>



</form>

<h2>Durée des vacances</h2>

<form method="post" action="/vacances">

    <label>Date de début :</label>
    <input type="date" name="date_debut" required>

    <br><br>

    <label>Date de fin :</label>
    <input type="date" name="date_fin" required>

    <br><br>

    <button type="submit">Enregistrer les dates</button>

</form>

<h2>Ajouter une dépense</h2>

<form method="post" action="/depenses">

    <label>Libellé :</label>
    <input type="text" name="libelle" required>
<br>
    <label>Type de dépense :</label>
    <input type="text" name="type_depense" required>
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

<form method="get" action="/">
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


# Page d'accueil : lit les membres et affiche PAGE.
@app.get("/")
def accueil():
    with ouvrir_base() as conn:
        membres = conn.execute("SELECT id, nom FROM membres").fetchall()
        depenses = conn.execute("SELECT id, libelle, montant_centimes FROM depenses").fetchall()
    noms = {membre["id"]: membre["nom"] for membre in membres}
    remboursements = None
    if request.args.get("remboursement"):
        remboursements = calculer_remboursements(1)
    return render_template_string(PAGE, membres=membres, depenses=depenses, soldes=calculer_soldes(1), noms=noms, remboursements=remboursements)


# Exemple : reçoit le formulaire et ajoute un membre au groupe 1.
@app.post("/membres")
def ajouter_membre():
    nom = request.form["nom"]
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO membres (groupe_id, nom) VALUES (1, ?)", [nom])
    return redirect("/")



@app.post("/depenses")
def ajouter_depense():
    libelle = request.form["libelle"]
    type_depense = request.form["type_depense"]
    montant_centimes = round(float(request.form["montant"]) * 100)
    date = request.form["date"]
    payeur_id = int(request.form["payeur"])
    participants = request.form.getlist("participants")
    with ouvrir_base() as conn:
        cur = conn.execute("INSERT INTO depenses (groupe_id, libelle,type_depense, montant_centimes, date, payeur_id) VALUES (1, ?,?, ?, ?, ?)", [libelle,type_depense, montant_centimes, date, payeur_id])
        for membre_id in participants:
            conn.execute("INSERT INTO participants (depense_id, membre_id) VALUES (?, ?)", [cur.lastrowid, int(membre_id)])
    return redirect("/")

#Test
# Ajoutez vos fonctions ici. Le HTML va dans PAGE.
@app.post("/supprimer_depense")
def supprimer_depense():
    with ouvrir_base() as conn:
        conn.execute("DELETE FROM depenses WHERE id = ?", [request.form["depense_id"]])
    return redirect("/")

def repartir_depense(montant_centimes, participants):
    if montant_centimes <= 0 or not participants:
        raise ValueError("Dépense invalide")

    part = montant_centimes // len(participants)
    reste = montant_centimes % len(participants)

    parts = {}

    for i, participant_id in enumerate(participants):
        parts[participant_id] = part + (reste if i == 0 else 0)

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

            soldes[depense["payeur_id"]] += depense["montant_centimes"]

            for membre_id, part in parts.items():
                soldes[membre_id] -= part

    return soldes


def calculer_remboursements(groupe_id):
    remboursement = []
    soldes = calculer_soldes(groupe_id)
    with ouvrir_base() as conn:
        membres = conn.execute(
            "SELECT id FROM membres WHERE groupe_id = ?",
            [groupe_id]
        ).fetchall()
        membres = [membre["id"] for membre in membres]
        positif = [membres[i] for i in range(len(membres)) if soldes[membres[i]] > 0]
        negatif = [membres[i] for i in range(len(membres)) if soldes[membres[i]] < 0]
        while positif != [] and negatif != []:
            x = len(positif) - 1
            y = len(negatif) - 1
            montant = min(soldes[positif[x]], -soldes[negatif[y]])
            remboursement.append((positif[x], negatif[y], montant))
            soldes[positif[x]] -= montant
            soldes[negatif[y]] += montant
            if soldes[positif[x]] == 0: positif.pop()
            if soldes[negatif[y]] == 0: negatif.pop()
    return remboursement

if __name__ == "__main__":
    app.run(debug=True)
