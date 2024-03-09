from flask import Flask, render_template ,request
from flask_mysqldb import MySQL
from datetime import datetime
 
app = Flask(__name__, template_folder='C:\\Users\\eliot\\OneDrive\\Documents\\La petite meteo\\La-petite-Meteo\\Web\\templates')
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'la-petite-meteo'

mysql = MySQL(app)

@app.route('/hello')
def hello():
  return 'Hello, world!'

@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/sonde', methods = ['GET', 'POST'])
def sonde():
    if request.method == "POST":
        try :
            name = request.args['name']
            zone = request.args['zone']
            cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO sonde VALUES('', %s,%s)''',(name,zone))
            mysql.connection.commit()
            cursor.close()
        except KeyError:
            return "Please specify name and zone"
        return f"Done!!"    
    cursor = mysql.connection.cursor()
    cursor.execute(""" SELECT * FROM sonde """)
    rv = cursor.fetchall()
    return str(rv)

@app.route('/releve', methods = ['GET', 'POST'])
def releve():
    if request.method == "POST":
        try :
            temperature = request.args['temperature']
            humidity = request.args['humidity']
            date = datetime.now()
            sonde = request.args['sonde']
            cursor = mysql.connection.cursor()
            cursor.execute(''' INSERT INTO releve VALUES('', %s,%s,%s,%s)''',(temperature,humidity,date,sonde))
            mysql.connection.commit()
            cursor.close()
        except KeyError:
            return "Missing information"
        return f"Done!!"
    cursor = mysql.connection.cursor()
    cursor.execute(""" SELECT * FROM releve """)
    rv = cursor.fetchall()
    return str(rv)

app.run(host='localhost', port=5000)
