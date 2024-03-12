from flask import Flask, request, render_template, redirect, url_for
import mariadb
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
    
app = Flask(__name__)
 
@app.route('/')
def index():
  now = datetime.now()
  date_time = now.strftime("%d/%m/%Y, %H:%M")
  days = [now + timedelta(days=i) for i in range(7)]
  return render_template("index.html", date_time=date_time, days=days)

@app.route('/gestion-sondes', methods = ['GET', 'POST'])
def gestion_sondes():
    if request.method == "POST":
        bouton = request.form['bouton']
        if bouton == 'maj':
            return redirect(url_for('maj_sonde'))
        elif bouton == 'nouveau':
            return redirect(url_for('ajouter_sonde'))
    else :
        return render_template("gestion_sondes.html")

@app.route('/nouvelle-sonde')
def ajouter_sonde():
    return render_template("form_add_sonde.html")


@app.route('/maj-sonde', methods = ['GET', 'POST'])
def maj_sonde():
    if request.method == "POST":
        name = request.form.get('nom')
        zone = request.form.get('zone')
        id = request.form.get('sonde-select')
        cur.execute(''' UPDATE sonde SET nom = %s, zone = %s WHERE ID_sonde = %s ''', (name, zone, id))
        return "Update done !"
    else :
        cur.execute(''' SELECT * FROM sonde ''')
        sondes = cur.fetchall()
        return render_template("form_maj_sonde.html", sondes=sondes)


@app.route('/sonde', methods = ['GET', 'POST'])
def sonde():
    if request.method == "POST":
        try :
            name = request.form.get('nom')
            zone = request.form.get('zone')
            if name is None or zone is None : raise KeyError
            cur.execute(''' INSERT INTO sonde (nom, zone) VALUES(%s,%s)''',(name,zone))
        except KeyError:
            return "Please specify name and zone"
        return f"Done!!"  
    else:
        cur.execute(''' SELECT * FROM sonde ''')
        return cur.fetchall()
    

@app.route('/releve', methods = ['GET', 'POST'])
def releve():
    if request.method == "POST":
        try :
            temperature = request.args['temperature']
            humidity = request.args['humidity']
            now = datetime.now()
            date = now.strftime("%d/%m/%Y, %H:%M:%S")
            sonde = request.args['sonde']
            cur.execute(''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES(%s,%s,%s,%s)''',(temperature,humidity,date,sonde))
        except KeyError:
            return "Missing information"
        return f"Done!!"
    else:
        cur.execute(''' SELECT * FROM releve ''')
        return cur.fetchall()

