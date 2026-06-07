import os
from flask import Flask, request,jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__, static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.context_processor
def override_url_for():
  return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
  from flask import url_for
  if endpoint == 'static':
    filename = values.get('filename')
    if filename:
      path = os.path.join(app.root_path, 'static', filename)
      try:
        values['v'] = int(os.path.getmtime(path))
      except OSError:
        values['v'] = int(os.path.getmtime(app.root_path))
  return url_for(endpoint, **values)

mongodb_uri = os.getenv('MONGODB_URI') or os.getenv('MONGODB_ATLAS_URI')
mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000) if mongodb_uri else None
mongo_db = mongo_client[os.getenv('MONGODB_DB')] if mongo_client and os.getenv('MONGODB_DB') else None



@app.route('/api/hello')
def hello():
    return jsonify(message="¡Hola desde Flask!")

@app.route('/')
def index():
    clientes_riesgo=125

    return render_template(
        "home.html",
        clientes_riesgo=clientes_riesgo,
    )

@app.route('/dashboards')
@app.route('/Dashboards')
def dashboard():

    total_clientes=1000
    clientes_riesgo=125
    perdida_estimada=300000

    id_cliente = "12345"
    tipo_negocio = "Restaurante"
    perdida_aprox = 10000
    indice_riesgo = "Alto"

    return render_template(
        "dashboards.html",
        total_clientes=total_clientes,
        clientes_riesgo=clientes_riesgo,
        perdida_estimada=perdida_estimada,
        id=id_cliente,
        tipo_negocio=tipo_negocio,
        perdida_aprox=perdida_aprox,
        indice_riesgo=indice_riesgo,
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)



