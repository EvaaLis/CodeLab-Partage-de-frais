from flask import Flask, redirect, render_template_string, request

from base import ouvrir_base

# Le HTML de la page.
PAGE = """
<<h1 style="text-align: center;">Partage de frais</h1>

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
            <option value="{{ membre['nom'] }}">
                {{ membre['nom'] }}
            </option>
        {% endfor %}
    </select>
<br>

<label>Participants :</label>

{% for membre in membres %}
    <input type="checkbox" name="participants" value="{{ membre['nom'] }}">
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
                {{ depense['libelle'] }} - {{ depense['montant'] }} €
            </option>
        {% endfor %}

    </select>

    <button type="submit">Supprimer la dépense</button>

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



@app.post("/depense")
def ajouter_depense():
    libelle = request.forpym["libelle"]
    montant = request.form["montant"]
    date = request.form["date"]
    payeur_id = request.form["payeur_id"]
    dep = request.form["depense"]
    with ouvrir_base() as conn:
        membres = conn.execute("SELECT id, nom FROM membres").fetchall()
        conn.execute("INSERT INTO depenses (groupe_id, libelle, montant_centimes, payeur_id) VALUES (1, ?,?,?,?)", [libelle, montant, centime, date, int(payeur_id)])
    return redirect("/")

#Test
# Ajoutez vos fonctions ici. Le HTML va dans PAGE.


if __name__ == "__main__":
    app.run(debug=True)
