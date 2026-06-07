import os
from flask import Flask, request,jsonify, render_template
from pymongo import MongoClient

from elevenlabs.client import ElevenLabs

app = Flask(__name__)

elevenlabs = ElevenLabs(api_key="sk_dca29e08e138979ba0f30ceedb0d5e1e02dd10279ee97729")

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

@app.route("/")
def index():
    clientes = [
        {"estado": "Tamaulipas", "tipo": "panaderia", "riesgo": 0.9},
        {"estado": "Nuevo León", "tipo": "farmacia", "riesgo": 0.7},
        {"estado": "Jalisco", "tipo": "abarrotes", "riesgo": 0.88}
    ]

    clientes_riesgo=125

    return render_template(
	"home.html", 
	clientes=clientes, 
    clientes_riesgo=clientes_riesgo,
	)


@app.route('/dashboards')
@app.route('/Dashboards')
def dashboard():

    riesgoEstados = {
        "Nuevo León": 0.85,
        "Jalisco": 0.62,
        "Ciudad de México": 0.30,
        "Puebla": 0.55,
        "Veracruz": 0.72
    }

    total_clientes=1000
    clientes_retenidos=500
    clientes_riesgo=125
    perdida_estimada=300000

    id_cliente = "12345"
    tipo_negocio = "Restaurante"
    perdida_aprox = 10000
    indice_riesgo = "Alto"
	
    proporcion="10%"

    return render_template(
        "dashboards.html",
        riesgoEstados=riesgoEstados,
        total_clientes=total_clientes,
	    clientes_retenidos=clientes_retenidos,
        clientes_riesgo=clientes_riesgo,
        perdida_estimada=perdida_estimada,
        id=id_cliente,
        tipo_negocio=tipo_negocio,
        perdida_aprox=perdida_aprox,
        indice_riesgo=indice_riesgo,
	    proporcion=proporcion,
    )

@app.route('/clientes')
def clientes():

    estado = request.args.get("estado")

    clientes = [
        {"id": "1", "tipo_negocio": "Restaurante", "estado": "Nuevo León", "porcentaje_riesgo": 0.7, "perdida_aprox": 10000},
        {"id": "2", "tipo_negocio": "Tienda", "estado": "Jalisco", "porcentaje_riesgo": 0.4, "perdida_aprox": 5000},
        {"id": "3", "tipo_negocio": "Farmacia", "estado": "Nuevo León", "porcentaje_riesgo": 0.9, "perdida_aprox": 20000},
    ]

    # filtro por estado
    if estado:
        clientes = [c for c in clientes if c["estado"] == estado]

    # 🔥 ORDENAR por riesgo (descendente)
    clientes = sorted(clientes, key=lambda x: x["porcentaje_riesgo"], reverse=True)

    return render_template(
        "clientes.html",
        clientes=clientes,
        estado_seleccionado=estado
    )

@app.route("/generate-audio")
def generate_audio():

    audio_stream = elevenlabs.text_to_speech.convert(
        text="Hola, este audio fue generado desde Flask",
        voice_id="JBFqnCBsd6RMkjVDRZzb"
    )

    audio = b"".join(audio_stream)

    os.makedirs("static/audio", exist_ok=True)

    path = "static/audio/output.mp3"

    with open(path, "wb") as f:
        f.write(audio)

    return {"url": "/static/audio/output.mp3"}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)



