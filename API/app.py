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
    except requests.ConnectionError:
        return '0', ''

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
    except requests.ConnectionError:
        return '0', ''

def get_labels():
    date_end = datetime(2024, 3, 24, 17, 0, 0)
    date_start = datetime(2024, 3, 10, 0, 0, 0)
    index_30min=pd.date_range(start=date_start, end=date_end, freq='30min')
    index_1h=pd.date_range(start=date_start, end=date_end, freq='1h')
    index_3h=pd.date_range(start=date_start, end=date_end, freq='3h')
    index_1d=pd.date_range(start=date_start, end=date_end, freq='1d')
    labels = {
        '12h' : index_30min.strftime('%H:%M').to_list()[-25:],
        '24h' : index_1h.strftime('%H:%M').to_list()[-25:],
        '48h' : index_3h.strftime('%d/%m %H:%M').to_list()[-17:],
        '7j' : index_1d.strftime('%d/%m').to_list()[-8:],
        '14j' : index_1d.strftime('%d/%m').to_list()
    }
    return labels

def resample(df:pd.DataFrame, delta, tail):
    return df.resample(delta).mean().round().tail(tail)

def get_last_data_from_releve(sondes):
    #cur.execute(''' SELECT date, temperature, humidite FROM releve WHERE date BETWEEN DATE_SUB(NOW(), INTERVAL 48 HOUR) AND NOW() ''')
    data = []
    for sonde in sondes:
        cur.execute(f''' 
                    SELECT date, temperature, humidite
                    FROM releve
                    WHERE date BETWEEN '2024-03-09' AND '2024-03-25' AND ID_sonde = {sonde[0]}
                    ORDER BY date DESC
        ''')
        rawdata = cur.fetchall()
        temp = {}
        temp["most recent"] = rawdata[0]

        df = pd.DataFrame(rawdata, columns=['date', 'temperature', 'humidite'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        data_30m = resample(df, '30min', 25)
        data_1h = resample(df, '1h', 25)
        data_3h = resample(df, '3h', 17)
        data_1d = resample(df, '1d', 15)
        temp["temperatures"] = { 
                '12h' : data_30m["temperature"].to_list(),
                '24h' : data_1h["temperature"].to_list(),
                '48h' : data_3h["temperature"].to_list(),
                '7j' : data_1d["temperature"].tail(8).to_list(),
                '14j' : data_1d["temperature"].to_list()
        }
        temp["humidites"] = { 
                '12h' : data_30m["humidite"].to_list(),
                '24h' : data_1h["humidite"].to_list(),
                '48h' : data_3h["humidite"].to_list(),
                '7j' : data_1d["humidite"].tail(8).to_list(),
                '14j' : data_1d["humidite"].to_list()
        }
        data.append(temp)
    return data

app = Flask(__name__)

@app.route('/accueil')
def index():
    now = datetime.now()
    cur.execute('''  SELECT * FROM sonde ''')
    sondes = cur.fetchall()
    labels = get_labels()
    data = get_last_data_from_releve(sondes)
    air = get_qualite_air()
    pollen = get_pollen()
    return render_template(
        "index.html",
        now=now,
        sondes=sondes,
        labels=labels,
        data=data,
        air=air,
        pollen=pollen
    )

@app.route('/traitement', methods = ['POST'])
def traitement():
    if request.method == "POST":
        bouton = request.form['bouton']
        if bouton == 'maj_sonde':
            return redirect(url_for('maj_sonde'))
        elif bouton == "accueil":
            return redirect(url_for('index'))
        elif bouton == "sondes":
            return redirect(url_for('sondes'))

#création uniquement avec le premier POST d'une sonde
@app.route('/nouvelle-sonde', methods = ['GET', 'POST'])
def ajouter_sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            if name is None or zone is None : raise KeyError
            cur.execute(f''' INSERT INTO sonde (nom, zone) VALUES("{name}","{zone}")''')
        except KeyError:
            return "Please specify name and zone"
        return redirect(url_for('sondes'))
    else :
        return render_template("form_add_sonde.html")

#faire une vérif lors de l'appui sur submit
@app.route('/maj-sonde', methods = ['GET', 'POST'])
def maj_sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            id = request.form.get('sonde-select')
            if id == "" : return redirect(url_for('maj_sonde'))
            if name is None or zone is None : raise KeyError 
            cur.execute(f''' UPDATE sonde SET nom = "{name}", zone = "{zone}" WHERE ID_sonde = {id} ''')
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
        mac = data["MAC"]
        #cur.execute(f''' SELECT ID_sonde FROM sonde WHERE mac = "{mac}"''')
        sonde = 1 #cur.fetchall()[0][0]
        cur.execute(f''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES({temperature},{humidite},"{date}",{sonde})''') 
        return f"Done at {now.strftime('%H:%M:%S')}!!"
    else :
        cur.execute(''' SELECT ID_sonde, nom FROM sonde ''')
        sondes = cur.fetchall()
        cur.execute(''' SELECT date, temperature, humidite FROM releve ORDER BY date DESC''')
        releves = cur.fetchall()
        return render_template("releve.html", releves=releves, sondes=sondes)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404