from flask import Flask, jsonify, request, render_template, redirect, url_for
import mariadb
import pandas as pd
import requests
from datetime import datetime, timedelta

ATMO_URL = "http://api.atmo-aura.fr/api/v1/communes/38185/indices/atmo?api_token=b382779cc858d7828197537836213a07&date_echeance=now"
POLLEN_URL = "https://api.ambeedata.com/latest/pollen/by-lat-lng?lat=45.1875602&lng=5.7357819"

""" 
    host="localhost",
    user="www-data",
    password='www-data',
    database="lapetitemeteo"
    host="localhost",
    port=3307,
    user="root",
    password='',
    database="lapetitemeteo"
"""

conn = mariadb.connect(
    host="localhost",
    user="www-data",
    password='www-data',
    database="lapetitemeteo"
)
cur = conn.cursor()

def get_pollen():
    def trad(mesure):
        if mesure == "Low":
            return "Bas"
        elif mesure == "Moderate":
            return "Modéré"
        elif mesure == "High":
            return "Élevé"
        elif mesure == "Very High":
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

def resample(df:pd.DataFrame, delta, tail):
    return df.resample(delta).mean().round().dropna().tail(tail)

def get_last_data_from_releve():
    #cur.execute(''' SELECT date, temperature, humidite FROM releve WHERE date BETWEEN DATE_SUB(NOW(), INTERVAL 48 HOUR) AND NOW() ''')
    cur.execute(''' SELECT date, temperature, humidite FROM releve WHERE date BETWEEN '2024-03-01' AND '2024-03-16' ORDER BY date DESC ''')
    rawdata = cur.fetchall()
    most_recent = rawdata[0]
    df = pd.DataFrame(rawdata, columns=['date', 'temperature', 'humidite'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    data_30m = resample(df, '30min', 25)
    data_1h = resample(df, '1h', 25)
    data_3h = resample(df, '3h', 17)
    data_1d = resample(df, '1d', 15)
    labels = { 
              '12h' : data_30m.index.strftime('%H:%M').to_list(),
              '24h' : data_1h.index.strftime('%H:%M').to_list(),
              '48h' : data_3h.index.strftime('%d/%m %H:%M').to_list(),
              '7j' : data_1d.tail(8).index.strftime('%d/%m').to_list(),
              '14j' : data_1d.index.strftime('%d/%m').to_list()
    }
    temperatures = { 
              '12h' : data_30m["temperature"].to_list(),
              '24h' : data_1h["temperature"].to_list(),
              '48h' : data_3h["temperature"].to_list(),
              '7j' : data_1d["temperature"].tail(8).to_list(),
              '14j' : data_1d["temperature"].to_list()
    }
    humidites = { 
              '12h' : data_30m["humidite"].to_list(),
              '24h' : data_1h["humidite"].to_list(),
              '48h' : data_3h["humidite"].to_list(),
              '7j' : data_1d["humidite"].tail(8).to_list(),
              '14j' : data_1d["humidite"].to_list()
    }
    ticks = {
        '12h' : (2,0),
        '24h' : (1,0),
        '48h' : (3,0),
        '7j' : (1,0),
        '14j' : (1,0)
    }
    return labels, temperatures, humidites, ticks, most_recent

app = Flask(__name__)

@app.route('/accueil')
def index():
    now = datetime.now()
    cur.execute('''  SELECT ID_sonde, nom FROM sonde ''')
    sondes = cur.fetchall()
    labels, temperatures, humidites, ticks, most_recent = get_last_data_from_releve()
    air = get_qualite_air()
    pollen = get_pollen()
    return render_template(
        "index.html",
        now=now,
        sondes=sondes,
        most_recent=most_recent,
        labels=labels,
        temperatures=temperatures,
        humidites=humidites,
        ticks=ticks,
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
        temperature = data['temperature']
        humidite = data['humidity']
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