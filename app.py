import os
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pandas as pd

from elevenlabs.client import ElevenLabs

app = Flask(__name__, static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# ==========================
# ELEVENLABS
# ==========================
elevenlabs = ElevenLabs(api_key="sk-REPLACE_THIS")


# ==========================
# STATIC FIX
# ==========================
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


# ==========================
# MONGODB
# ==========================
from pymongo import MongoClient

mongodb_uri = "mongodb+srv://hannairachetal_db_user:DrMzpetUcITN0SG1@pilotoscosmicos.osx3t9d.mongodb.net/?appName=PilotosCosmicos"

mongo_client = MongoClient(mongodb_uri)
mongo_db = mongo_client["Hack4Her_DB"]
collection = mongo_db["predicciones_churn"]

# ==========================
# 🔥 MÉTRICAS REALES (TU FUNCIÓN INTEGRADA)
# ==========================
def obtener_metricas():

    if mongo_db is None:
        return {
            "total_clientes": 0,
            "clientes_riesgo": 0,
            "clientes_retenidos": 0,
            "cantidad_coolers": 0,
            "estado_mayor_churn": None,
            "estado_menor_churn": None,
            "coolers_por_estado": {},
            "top10_por_estado": {}
        }

    collection = mongo_db["predicciones_churn"]
    documentos = list(collection.find({}, {"_id": 0}))

    if not documentos:
        return {
            "total_clientes": 0,
            "clientes_riesgo": 0,
            "clientes_retenidos": 0,
            "cantidad_coolers": 0,
            "estado_mayor_churn": None,
            "estado_menor_churn": None,
            "coolers_por_estado": {},
            "top10_por_estado": {}
        }

    df = pd.DataFrame(documentos)

    df["calificacion_riesgo"] = pd.to_numeric(df.get("calificacion_riesgo", 0), errors="coerce").fillna(0)
    df["probabilidad_churn"] = pd.to_numeric(df.get("probabilidad_churn", 0), errors="coerce").fillna(0)
    df["coolers_activos"] = pd.to_numeric(df.get("coolers_activos", 0), errors="coerce").fillna(0)

    total_clientes = len(df)

    clientes_riesgo = len(df[df["calificacion_riesgo"] >= 4])
    clientes_retenidos = len(df[df["calificacion_riesgo"] < 4])

    cantidad_coolers = int(df["coolers_activos"].sum())

    # TOP 10
    top10_por_estado = {}

    for estado, grupo in df.groupby("estado"):

        top10_por_estado[estado] = (
            grupo.sort_values("probabilidad_churn", ascending=False)
            .head(10)
            [["id_cliente", "probabilidad_churn", "calificacion_riesgo", "coolers_activos"]]
            .to_dict("records")
        )

    # CHURN POR ESTADO
    churn_por_estado = df.groupby("estado")["probabilidad_churn"].mean().sort_values()

    return {
        "total_clientes": total_clientes,
        "clientes_riesgo": clientes_riesgo,
        "clientes_retenidos": clientes_retenidos,
        "cantidad_coolers": cantidad_coolers,

        "estado_mayor_churn": {
            "estado": churn_por_estado.index[-1],
            "valor": float(churn_por_estado.iloc[-1])
        },

        "estado_menor_churn": {
            "estado": churn_por_estado.index[0],
            "valor": float(churn_por_estado.iloc[0])
        },

        "coolers_por_estado": df.groupby("estado")["coolers_activos"].sum().to_dict(),
        "top10_por_estado": top10_por_estado
    }


# ==========================
# API
# ==========================
@app.route('/api/hello')
def hello():
    return jsonify(message="¡Hola desde Flask!")


@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(obtener_metricas())


# ==========================
# MAIN PAGE (SIN FAKE)
# ==========================
@app.route("/")
def index():
    metricas = obtener_metricas()

    return render_template(
        "home.html",
        clientes_riesgo=metricas["clientes_riesgo"]
    )


# ==========================
# DASHBOARDS (YA SIN FAKE TOTAL)
# ==========================
@app.route('/dashboards')
@app.route('/Dashboards')
def dashboard():

    metricas = obtener_metricas()

    riesgoEstados = {}  # puedes llenarlo después con coolers_por_estado si quieres

    clientes = []  # ya no fake, lo puedes consumir por API en frontend

    orden = request.args.get("orden", "riesgo")

    return render_template(
        "dashboards.html",
        riesgoEstados=riesgoEstados,
        total_clientes=metricas["total_clientes"],
        clientes_retenidos=metricas["clientes_retenidos"],
        clientes_riesgo=metricas["clientes_riesgo"],
        perdida_estimada=0,
        clientes=clientes,
        proporcion="10%",
        orden=orden
    )


# ==========================
# CLIENTES PAGE (SIN FAKE DATA)
# ==========================
@app.route('/clientes')
def clientes():
    return render_template("clientes.html")


# ==========================
# AUDIO (SIN CAMBIOS)
# ==========================
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


# ==========================
# RUN
# ==========================
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)