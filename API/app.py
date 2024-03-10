from flask import Flask, request, render_template
import mariadb
from datetime import datetime

""" essai local pc
conn = mariadb.connect(
    host="localhost",
    port=3307,
    user="root",
    password='',
    database="lapetitemeteo"
)"""

conn = mariadb.connect(
    host="localhost",
    user="www-data",
    password='www-data',
    database="lapetitemeteo"
)
cur = conn.cursor()
    
app = Flask(__name__)
 
@app.route('/')
def index():
  return render_template("index.html")


@app.route('/sonde', methods = ['GET', 'POST'])
def sonde():
    if request.method == "POST":
        try :
            name = request.args['name']
            zone = request.args['zone']
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
            date = datetime.now()
            sonde = request.args['sonde']
            cur.execute(''' INSERT INTO releve (temperature, humidite, date, id_sonde) VALUES(%s,%s,%s,%s)''',(temperature,humidity,date,sonde))
        except KeyError:
            return "Missing information"
        return f"Done!!"
    else:
        cur.execute(''' SELECT * FROM releve ''')
        return cur.fetchall()

