from flask import Flask, render_template, request
import mysql.connector

# Connexion à la base de données
cnx = mysql.connector.connect(user='root', password='mysql', host='localhost', database='pizzeria_felicio')
cnx.autocommit = False
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/commande')
def commande():
    # Création du curseur avec des résultats nommés
    cursor = cnx.cursor(dictionary=True)

    #SELECT DES CROUTES
    cursor.execute("SELECT * FROM croute ORDER BY id")
    croute = cursor.fetchall()

    #SELECT DES SAUCES
    cursor.execute("SELECT * FROM sauce ORDER BY id")
    sauce = cursor.fetchall()

    #SELECT DES GARNITURES
    cursor.execute("SELECT * FROM garniture ORDER BY id")
    garniture = cursor.fetchall()

    cursor.close()

    return render_template('commande.html', croute=croute, sauce=sauce, garniture=garniture)

###############################
#    TRAITEMENT COMMANDE   #
###############################
prenom = ""
nom = ""
numTel = ""
adresse = ""
ville = ""
crouteID = ""
sauceID = ""

def traitementPizza(prenom, nom, numTel, adresse, ville, crouteID, sauceID, garnitures):
    # Création du curseur avec des résultats nommés
    cursor = cnx.cursor(dictionary=True)

    cursor.execute(""" INSERT INTO client (nom, prenom, numero_telephone, adresse, ville) VALUES ( %s, %s, %s, %s, %s)""", (nom, prenom , numTel, adresse, ville))
    cnx.commit()
    clientID = cursor.lastrowid

    # OBTENTION DE COMMANDE.ID pour le référencement
    cursor.execute(f"SELECT commande.id FROM commande WHERE commande.client_id = {clientID}")
    commandeID = cursor.fetchone()
        
    cursor.execute(f""" INSERT INTO pizza (commande_id, croute_id, sauce_id) VALUES ({commandeID['id']}, {crouteID}, {sauceID})""")
    cnx.commit()
    pizzaID = cursor.lastrowid

    for i in range(0,4):
        if garnitures[i] != '0': 
            print(garnitures[i])
            cursor.execute(f""" INSERT INTO pizza_garniture (pizza_id, garniture_id) VALUES ( {pizzaID}, {garnitures[i]})""")
            cnx.commit()

    return pizzaID

@app.route('/validationPizza', methods=['POST'])
def validationPizza():
    # Création du curseur avec des résultats nommés
    cursor = cnx.cursor(dictionary=True)

    # GESTION CLIENT
    prenom = request.form['prenom']
    nom = request.form['nom']
    numTel = request.form['numTel']
    adresse = request.form['adresse']
    ville = request.form['ville']

    # GESTION PIZZA 
    crouteID = request.form['croute']
    cursor.execute(f"""SELECT croute.type_croute FROM croute WHERE croute.id = {crouteID} """)
    crouteNom = cursor.fetchone()

    sauceID = request.form['sauce']
    cursor.execute(f"""SELECT sauce.type_sauce FROM sauce WHERE sauce.id = {sauceID} """)
    sauceNom = cursor.fetchone()
    
    garnitures = [request.form["garniture1"], request.form["garniture2"], request.form["garniture3"], request.form["garniture4"]]
    
    pizzaID = traitementPizza(prenom, nom, numTel, adresse, ville, crouteID, sauceID, garnitures)

    cursor.execute(f"""SELECT GROUP_CONCAT(garniture.type_garniture ORDER BY garniture.id SEPARATOR ', ') AS garnitures FROM garniture INNER JOIN pizza_garniture ON pizza_garniture.garniture_id = garniture.id WHERE pizza_garniture.pizza_id = {pizzaID} """)
    garnituresNom = cursor.fetchone()
        
    return render_template('validationPizza.html', prenom=prenom, nom=nom, numTel=numTel, adresse=adresse, ville=ville, crouteNom=crouteNom, sauceNom=sauceNom, garnituresNom=garnituresNom)


###############################
#    GESTION LISTE COMMANDE   #
###############################

def affichageCommande():
    # Création du curseur avec des résultats nommés
    cursor = cnx.cursor(dictionary=True)

    # L'utilisation de group concat a été trouvé sur ce site : "https://www.machinelearningplus.com/sql/how-to-concatenate-multiple-rows-into-one-field-in-mysql/#:~:text=Explanation%3A,GROUP_CONCAT()%20function%20as%20well"
    cursor.execute("SELECT pizza.id, croute.type_croute, sauce.type_sauce, GROUP_CONCAT(garniture.type_garniture ORDER BY garniture.id SEPARATOR ', ') AS garnitures, client.nom, client.prenom, client.adresse, client.ville, commande.date, commande.id FROM pizza INNER JOIN croute ON croute.id = pizza.croute_id INNER JOIN sauce ON sauce.id = pizza.sauce_id INNER JOIN pizza_garniture ON pizza.id = pizza_garniture.pizza_id INNER JOIN garniture ON pizza_garniture.garniture_id = garniture.id INNER JOIN commande ON pizza.commande_id = commande.id INNER JOIN client on commande.client_id = client.id GROUP BY pizza.id")
    commande = cursor.fetchall()

    cursor.close()

    return commande

@app.route('/listecommande')
def listecommande():
    commande = affichageCommande()

    return render_template('listecommande.html', commande=commande)

@app.route('/retirerPizza', methods=['POST', 'GET'])
def retirerPizza():
    # Requête de l'id de la commande
    commande_id = request.form.get('commande_id')

    # Création du curseur avec des résultats nommés
    cursor = cnx.cursor(dictionary=True)

    # Suppresion du client qui supprime toutes le reste de la commande
    cursor.execute(f"SELECT commande.client_id FROM commande WHERE commande.id = {commande_id}")
    clientID = cursor.fetchone()
    cursor.execute(f"DELETE FROM client WHERE client.id = {clientID['client_id']}")

    cnx.commit()
    cursor.close()

    # Réaffichage des commandes
    commande = affichageCommande()

    return render_template('listecommande.html', commande=commande)
    

if __name__ == '__main__':
    app.run(debug=True)