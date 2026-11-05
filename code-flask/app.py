from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """
<h1>Partage de frais</h1>

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

<h2>Ajouter une dépense</h2>

<form method="post" action="/depenses">

    <label>Libellé :</label>
    <input type="text" name="libelle" required>

    <label>Montant :</label>
    <input type="number" name="montant" step="0.01" required>

    <label>Date :</label>
    <input type="date" name="date" required>

    <label>Payeur :</label>
    <select name="payeur" required>
        <option value="">Choisir un payeur</option>
        {% for membre in membres %}
            <option value="{{ membre['nom'] }}">
                {{ membre['nom'] }}
            </option>
        {% endfor %}
    </select>

<label>Participant :</label>
<select name="participant" multiple required>
    {% for membre in membres %}
        <option value="{{ membre['nom'] }}">
            {{ membre['nom'] }}
        </option>
    {% endfor %}
</select>

    <button type="submit">Ajouter la dépense</button>

</form>

"""

app = Flask(__name__)


# Page d'accueil : lit les membres et affiche PAGE.
@app.get("/")
def accueil():
    with ouvrir_base() as conn:
        membres = conn.execute("SELECT nom FROM membres").fetchall()
    return render_template_string(PAGE, membres=membres)


# Exemple : reçoit le formulaire et ajoute un membre au groupe 1.
@app.post("/membres")
def ajouter_membre():
    nom = request.form["nom"]
    with ouvrir_base() as conn:
        conn.execute("INSERT INTO membres (groupe_id, nom) VALUES (1, ?)", [nom])
    return redirect("/")


# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
