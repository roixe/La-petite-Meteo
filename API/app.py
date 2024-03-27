from flask import Flask, jsonify, request, render_template, redirect, url_for
import mariadb
import pandas as pd
import requests
from datetime import datetime
from werkzeug.exceptions import UnsupportedMediaType

ATMO_URL = "http://api.atmo-aura.fr/api/v1/communes/38185/indices/atmo?api_token=b382779cc858d7828197537836213a07&date_echeance=now"
POLLEN_URL = "https://api.ambeedata.com/latest/pollen/by-lat-lng?lat=45.1875602&lng=5.7357819"

""" 
    port=3307,
    user="root",
    password='',
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

def get_most_recent():
    most_recent = {}
    cur.execute(f''' 
                    SELECT date, temperature, humidite, ID_sonde FROM releve 
                    WHERE (ID_sonde, date) IN 
                    (   SELECT id_sonde, MAX(date)
                        AS max_date FROM releve 
                        GROUP BY id_sonde 
                    ); 
    ''')
    rawdata = cur.fetchall()
    for data in rawdata:
        most_recent[data[3]] = (data[0], data[1], data[2])
    return most_recent

def get_data_from_releve(sondes):
    """
                   SELECT date, temperature, humidite 
                   FROM releve 
                   WHERE date BETWEEN DATE_SUB(NOW(), INTERVAL 48 HOUR) AND NOW() 
                   AND ID_sonde = {sonde[0]}
                   ORDER BY date DESC
    """
    data = []
    for sonde in sondes:
        cur.execute(f''' 
                    SELECT date, temperature, humidite
                    FROM releve
                    WHERE date BETWEEN '2024-03-09' AND '2024-03-25'
                    AND ID_sonde = {sonde[0]}
                    ORDER BY date DESC
        ''')
        rawdata = cur.fetchall()
        if len(rawdata) != 0 :
            temp = {}

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

def check_sonde(mac):
    cur.execute(f''' SELECT ID_sonde FROM sonde WHERE mac_address = "{mac}"''')
    rawdata=cur.fetchall()
    if len(rawdata) == 0 :
        cur.execute(f''' INSERT INTO sonde (nom, zone, mac_address) VALUES("new","new", "{mac}")''')
        cur.execute(f''' SELECT ID_sonde FROM sonde WHERE mac_address = "{mac}"''')
        rawdata=cur.fetchall()
    return rawdata[0][0]

app = Flask(__name__)

@app.route('/accueil')
def index():
    now = datetime.now()
    cur.execute('''  SELECT * FROM sonde ''')
    sondes = cur.fetchall()
    labels = get_labels()
    most_recent = get_most_recent()
    data = get_data_from_releve(sondes)
    air = get_qualite_air()
    pollen = get_pollen()
    return render_template(
        "index.html",
        now=now,
        sondes=sondes,
        labels=labels,
        most_recent=most_recent,
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

@app.route('/maj-sonde', methods = ['GET', 'POST'])
def maj_sonde():
    if request.method == "POST":
        name = request.form.get('nom')
        zone = request.form.get('zone')
        id = request.form.get('sonde-select')
        if id == "" or name is None or zone is None or id is None: 
            return redirect(url_for('sondes'))
        cur.execute(f''' UPDATE sonde SET nom = "{name}", zone = "{zone}" WHERE ID_sonde = {id} ''')
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
        try :
            data = request.get_json()
            temperature = data['temperature']
            humidite = data['humidity']
            now = datetime.now()
            date = now.replace(second=00).strftime("%Y-%m-%d %H:%M:%S")
            mac = data["MAC"]
            sonde = check_sonde(mac)
            cur.execute(f''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES({temperature},{humidite},"{date}",{sonde})''') 
            return f"Done at {now.strftime('%H:%M:%S')}!!"
        except UnsupportedMediaType:
            return 'Type de média non pris en charge'
        except KeyError:
            return 'Données manquantes'
    else :
        cur.execute(''' 
                    SELECT r.date, r.temperature, r.humidite, s.nom AS nom_sonde 
                    FROM releve r 
                    JOIN sonde s ON r.ID_sonde = s.ID_sonde 
                    ORDER BY r.date DESC
        ''')
        releves = cur.fetchall()
        return render_template("releve.html", releves=releves)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
