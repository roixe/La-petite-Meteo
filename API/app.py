from flask import Flask, request, render_template, redirect, url_for
import mariadb
import requests
from datetime import datetime, timedelta

""" essai local pc
    
    host="localhost",
    port=3307,
    user="root",
    password='',
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

def get_qualite_air():
    try :
        response = requests.get(ATMO_URL)
        response.raise_for_status()
        json_data = response.json()
        qualificatif = json_data.get('data')[0].get("qualificatif")
        indice = json_data.get('data')[0].get("indice")
        couleur = json_data.get('data')[0].get("couleur_html")
        return (str(indice), qualificatif, couleur)
    except requests.HTTPError: 
        return 'X', ''

def get_last_data_from_releve():
    cur.execute('''  SELECT temperature, humidite, date FROM releve ORDER BY date DESC LIMIT 15 ''')
    data = cur.fetchall()
    labels = [row[2].strftime("%H:%M") for row in reversed(data)]
    temperatures = [row[0] for row in reversed(data)]
    humidite = [row[1] for row in reversed(data)]
    return labels, temperatures, humidite

app = Flask(__name__)
 
@app.route('/hello')
def hello():
    return "Hello world!"
@app.route('/')
def index():
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y, %H:%M")
    days = [now + timedelta(days=i) for i in range(7)]
    labels, temperatures, humidite = get_last_data_from_releve()
    air = get_qualite_air()
    return render_template(
        "index.html", 
        date_time=date_time, 
        days=days, 
        labels=labels, 
        temperatures=temperatures,
        humidite=humidite,
        air=air
    )

@app.route('/nouvelle-sonde', methods = ['GET', 'POST'])
def ajouter_sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            if name is None or zone is None : raise KeyError
            cur.execute(''' INSERT INTO sonde (nom, zone) VALUES(%s,%s)''',(name,zone))
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
            cur.execute(''' UPDATE sonde SET nom = %s, zone = %s WHERE ID_sonde = %s ''', (name, zone, id))
        except KeyError:
            return "Please specify name and zone"
        return redirect(url_for('sondes'))
    else :
        cur.execute(''' SELECT * FROM sonde ''')
        sondes = cur.fetchall()
        return render_template("form_maj_sonde.html", sondes=sondes)


@app.route('/sondes', methods = ['GET', 'POST'])
def sondes():
    if request.method == "POST":
        bouton = request.form['bouton']
        if bouton == 'maj':
            return redirect(url_for('maj_sonde'))
        elif bouton == 'nouveau':
            return redirect(url_for('ajouter_sonde'))
    else :
        cur.execute(''' SELECT * FROM sonde ''')
        sondes = cur.fetchall()
        return render_template("sondes.html", sondes=sondes)
    

@app.route('/releve', methods = ['GET', 'POST'])
def releve():
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
        """try :
            temperature = request.args['temperature']
            humidity = request.args['humidity']
            now = datetime.now()
            date = now.replace(second=00).strftime("%Y-%m-%d %H:%M:%S")
            sonde = 1 # request.args['sonde']
            cur.execute(''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES(%s,%s,%s,%s)''',(temperature,humidity,date,sonde))
        except KeyError:
            return "Missing information"""
        return f"Done!!"
    else:
        cur.execute(''' SELECT * FROM releve ''')
        return cur.fetchall()

ATMO_URL = "http://api.atmo-aura.fr/api/v1/communes/38185/indices/atmo?api_token=b382779cc858d7828197537836213a07&date_echeance=now"
