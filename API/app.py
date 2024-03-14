from flask import Flask, jsonify, request, render_template, redirect, url_for
import mariadb
import requests
from datetime import datetime, timedelta

ATMO_URL = "http://api.atmo-aura.fr/api/v1/communes/38185/indices/atmo?api_token=b382779cc858d7828197537836213a07&date_echeance=now"
POLLEN_URL = "https://api.ambeedata.com/latest/pollen/by-lat-lng?lat=45.1875602&lng=5.7357819"

""" API
    host="localhost",
    user="www-data",
    password='www-data',
    database="lapetitemeteo"
"""

conn = mariadb.connect(
    host="localhost",
    port=3307,
    user="root",
    password='',
    database="lapetitemeteo"
)
cur = conn.cursor()

def get_pollen():
    def trad(mesure):
        match mesure:
            case "Low":
                return "Bas"
            case "Moderate":
                return "Modéré"
            case "High":
                return "Élevé"
            case "Very High":
                return "Très élevé"
    try :
        response = requests.get(POLLEN_URL, headers={"x-api-key":"74d530040c05eb64ce5180c0d37262718b4baafaf7b5c08cbb90a9640f279258"}, timeout=3)
        response.raise_for_status()
        json_data = response.json()
        risk = json_data.get('data')[0].get("Risk")
        arbre = trad(risk.get('tree_pollen'))
        graminees = trad(risk.get('weed_pollen'))
        herbacees = trad(risk.get('grass_pollen'))
        return (arbre, graminees, herbacees)
    except requests.HTTPError:
        return "-", "-", "-"
    except requests.Timeout:
        return "-", "-", "-"

def get_qualite_air():
    try :
        response = requests.get(ATMO_URL, timeout=3)
        response.raise_for_status()
        json_data = response.json()
        qualificatif = json_data.get('data')[0].get("qualificatif")
        indice = json_data.get('data')[0].get("indice")
        couleur = json_data.get('data')[0].get("couleur_html")
        if indice > 6 : indice = 0
        return (str(indice), qualificatif, couleur)
    except requests.HTTPError:
        return '0', ''
    except requests.Timeout:
        return '0', ''

def get_last_data_from_releve():
    cur.execute('''  SELECT temperature, humidite, date FROM releve ORDER BY date DESC LIMIT 48 ''')
    data = cur.fetchall()
    labels = [row[2].strftime("%d/%m %H:%M") for row in reversed(data)]
    temperatures = [row[0] for row in reversed(data)]
    humidite = [row[1] for row in reversed(data)]
    return labels, temperatures, humidite

app = Flask(__name__)

@app.route('/')
def index():
    now = datetime.now()
    days = [now + timedelta(days=i) for i in range(7)]
    labels, temperatures, humidite = get_last_data_from_releve()
    air = get_qualite_air()
    pollen = ("Elevé","Bas","Bas") #get_pollen()
    return render_template(
        "index.html",
        now=now,
        days=days,
        labels=labels,
        temperatures=temperatures,
        humidite=humidite,
        air=air,
        pollen=pollen
    )

@app.route('/traitement', methods = ['POST'])
def traitement():
    if request.method == "POST":
        bouton = request.form['bouton']
        if bouton == 'maj_sonde':
            return redirect(url_for('maj_sonde'))
        elif bouton == 'nouveau_sonde':
            return redirect(url_for('ajouter_sonde'))
        elif bouton == "accueil":
            return redirect(url_for('index'))

@app.route('/nouvelle-sonde', methods = ['GET', 'POST'])
def ajouter_sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            if name is None or zone is None : raise KeyError
            #cur.execute(''' INSERT INTO sonde (nom, zone) VALUES(%s,%s)''',(name,zone))
        except KeyError:
            return "Please specify name and zone"
        return redirect(url_for('sondes'))
    else :
        return render_template("form_add_sonde.html")


@app.route('/maj-sonde', methods = ['GET', 'POST'])
def maj_sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            id = request.form.get('sonde-select')
            if name is None or zone is None  or id == "" : raise KeyError
            #cur.execute(''' UPDATE sonde SET nom = %s, zone = %s WHERE ID_sonde = %s ''', (name, zone, id))
        except KeyError:
            return "Please specify name and zone"
        return redirect(url_for('sondes'))
    else :
        cur.execute(''' SELECT * FROM sonde ''')
        sondes = cur.fetchall()
        return render_template("form_maj_sonde.html", sondes=sondes)


@app.route('/sondes', methods = ['GET'])
def sondes():
    cur.execute(''' SELECT * FROM sonde ''')
    sondes = cur.fetchall()
    return render_template("sondes.html", sondes=sondes)  

@app.route('/releve', methods = ['GET', 'POST'])
def releves():
    if request.method == "POST":
        data = request.get_json()
        if data is None:
                return jsonify({'erreur': 'Aucune donnée JSON envoyée'})
        temperature = data.get('temperature')
        humidite = data.get('humidity')
        now = datetime.now()
        date = now.replace(second=00).strftime("%Y-%m-%d %H:%M:%S")
        sonde = 1 #request.args['sonde']
        cur.execute(''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES(%s,%s,%s,%s)''',(temperature,humidite,date,sonde)) 
        return f"Done at {now.strftime('%H:%M:%S')}!!"
    else :
        cur.execute(''' SELECT date, temperature, humidite FROM releve ORDER BY date DESC''')
        releves = cur.fetchall()
        return render_template("releve.html", releves=releves)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404