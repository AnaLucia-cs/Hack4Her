import os
import re
import io
import base64
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv

# CONFIGURACIÓN PARA GENERAR LAS IMÁGENES DE LAS GRÁFICAS
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt

# IMPORTAMOS EL NUEVO SDK DE GEMINI
from google import genai 

# ==========================
# CONFIGURACIÓN DE ENTORNO Y FLASK
# ==========================
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__, static_folder='static')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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

# =====================
# CONFIGURACIÓN GEMINI
# =====================
GOOGLE_API_KEY = "AQ.Ab8RN6Lnq6OzIJ7N9YSNJ6jMh_PufvQ1FjYwSCu9-iyaY_OlTA" 
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)

# =====================
# CONEXIÓN A MONGODB
# =====================
mongodb_uri = os.getenv('MONGODB_URI') or os.getenv('MONGODB_ATLAS_URI') or "mongodb+srv://hannairachetal_db_user:DrMzpetUcITN0SG1@pilotoscosmicos.osx3t9d.mongodb.net/?appName=PilotosCosmicos"
db_name = os.getenv('MONGODB_DB') or "Hack4Her_DB"

mongo_client = None
mongo_db = None

try:
    if mongodb_uri:
        mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
        mongo_db = mongo_client[db_name]
        print(f"✓ MongoDB conectado: {db_name}")
except Exception as e:
    print(f"✗ Error conectando MongoDB: {e}")
    mongo_db = None


# ==========================================
# 📊 GENERADOR DE IMÁGENES (ESTADO Y TIPO)
# ==========================================
def generar_imagenes_graficas(df):
    """Genera las imágenes de las gráficas 'estado' y 'tipo' en base64"""
    if df.empty:
        return "", ""
    
    plot_estado, plot_tipo = "", ""
    try:
        # 1. Imagen / Gráfica de Estado (Churn por Estado)
        plt.figure(figsize=(6, 4))
        df.groupby("estado")["probabilidad_churn"].mean().sort_values(ascending=False).plot(kind="bar", color="#e74c3c")
        plt.title("Riesgo de Churn Promedio por Estado")
        plt.xlabel("Estado")
        plt.ylabel("Probabilidad %")
        plt.tight_layout()
        
        buf_estado = io.BytesIO()
        plt.savefig(buf_estado, format='png')
        buf_estado.seek(0)
        plot_estado = base64.b64encode(buf_estado.getvalue()).decode('utf-8')
        plt.close()

        # 2. Imagen / Gráfica de Tipo (Distribución de Tipo de Tienda)
        plt.figure(figsize=(6, 4))
        if "tipo_tienda" in df.columns:
            df["tipo_tienda"].value_counts().plot(kind="pie", autopct='%1.1f%%', colors=["#3498db", "#2ecc71", "#f1c40f", "#9b59b6"])
        plt.title("Distribución por Tipo de Tienda")
        plt.ylabel("")
        plt.tight_layout()
        
        buf_tipo = io.BytesIO()
        plt.savefig(buf_tipo, format='png')
        buf_tipo.seek(0)
        plot_tipo = base64.b64encode(buf_tipo.getvalue()).decode('utf-8')
        plt.close()
    except Exception as e:
        print(f"Error generando imágenes de gráficas: {e}")
        
    return plot_estado, plot_tipo


# ==========================
# 🔥 MÉTRICAS REALES (PANDAS)
# ==========================
def obtener_metricas():
    if mongo_db is None:
        return {"total_clientes": 0, "clientes_riesgo": 0, "clientes_retenidos": 0, "cantidad_coolers": 0, "coolers_por_estado": {}, "top10_por_estado": {}, "documentos": []}

    collection = mongo_db["predicciones_churn"]
    documentos = list(collection.find({}, {"_id": 0}))

    if not documentos:
        return {"total_clientes": 0, "clientes_riesgo": 0, "clientes_retenidos": 0, "cantidad_coolers": 0, "coolers_por_estado": {}, "top10_por_estado": {}, "documentos": []}

    df = pd.DataFrame(documentos)
    df["calificacion_riesgo"] = pd.to_numeric(df.get("calificacion_riesgo", 0), errors="coerce").fillna(0)
    df["probabilidad_churn"] = pd.to_numeric(df.get("probabilidad_churn", 0), errors="coerce").fillna(0)
    df["coolers_activos"] = pd.to_numeric(df.get("coolers_activos", 0), errors="coerce").fillna(0)

    total_clientes = len(df)
    clientes_riesgo = len(df[df["calificacion_riesgo"] >= 4])
    clientes_retenidos = len(df[df["calificacion_riesgo"] < 4])
    cantidad_coolers = int(df["coolers_activos"].sum())

    top10_por_estado = {}
    for estado, grupo in df.groupby("estado"):
        top10_por_estado[estado] = (
            grupo.sort_values("probabilidad_churn", ascending=False)
            .head(10)
            [["id_cliente", "probabilidad_churn", "calificacion_riesgo", "coolers_activos", "tipo_tienda"]]
            .to_dict("records")
        )

    return {
        "total_clientes": total_clientes,
        "clientes_riesgo": clientes_riesgo,
        "clientes_retenidos": clientes_retenidos,
        "cantidad_coolers": cantidad_coolers,
        "coolers_por_estado": df.groupby("estado")["coolers_activos"].sum().to_dict(),
        "top10_por_estado": top10_por_estado,
        "df": df,
        "documentos": documentos  # El JSON crudo de Mongo
    }

# ==========================
# RUTAS DE VISTAS (PÁGINAS)
# ==========================

# HOME PAGE ACTUALIZADO (Con mapa, imágenes de gráficas y listas con tus datos JSON)
@app.route("/")
def index():
    res = obtener_metricas()
    df = res.get("df", pd.DataFrame())
    plot_estado, plot_tipo = generar_imagenes_graficas(df)
    
    return render_template(
        "home.html",
        clientes_riesgo=res["clientes_riesgo"],
        total_clientes=res["total_clientes"],
        clientes_retenidos=res["clientes_retenidos"],
        riesgoEstados=res["coolers_por_estado"],  # 🗺️ EL MAPA DEL DASHBOARD AGREGADO A HOME
        clientes=res["documentos"],              # 📋 LISTAS CON LOS DATOS DE TU JSON REAL
        chart_estado=plot_estado,                # 🖼️ IMAGEN LLAMADA ESTADO
        chart_tipo=plot_tipo                     # 🖼️ IMAGEN LLAMADA TIPO
    )

# DASHBOARD PAGE ACTUALIZADO (Con listas con tus datos JSON e imágenes de gráficas)
@app.route('/dashboards')
@app.route('/Dashboards')
def dashboard():
    res = obtener_metricas()
    df = res.get("df", pd.DataFrame())
    plot_estado, plot_tipo = generar_imagenes_graficas(df)
    orden = request.args.get("orden", "riesgo")

    return render_template(
        "dashboards.html",
        riesgoEstados=res["coolers_por_estado"],
        total_clientes=res["total_clientes"],
        clientes_retenidos=res["clientes_retenidos"],
        clientes_riesgo=res["clientes_riesgo"],
        perdida_estimada=300000,
        clientes=res["documentos"],              # 📋 LISTAS CON LOS DATOS DE TU JSON REAL
        proporcion="10%",
        orden=orden,
        id="12345",
        tipo_negocio="Restaurante",
        perdida_aprox=10000,
        indice_riesgo="Alto",
        chart_estado=plot_estado,                # 🖼️ IMAGEN LLAMADA ESTADO
        chart_tipo=plot_tipo                     # 🖼️ IMAGEN LLAMADA TIPO
    )

@app.route('/clientes')
@app.route('/Clientes')
def clientes():
    res = obtener_metricas()
    return render_template(
        "clientes.html",
        clientes=res["documentos"],              # 📋 LISTAS CON LOS DATOS DE TU JSON REAL
        id="12345",
        tipo_negocio="Restaurante",
        perdida_aprox=10000,
        indice_riesgo="Alto"
    )


# =====================
# API RECOMENDACIONES GEMINI
# =====================
@app.route('/api/recomendacion-gemini', methods=['POST'])
def obtener_recomendacion_gemini():
    data = request.json
    id_cliente = data.get('id_cliente')
    estado = data.get('estado')
    
    if not id_cliente or not estado:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    
    try:
        cliente_data = None
        if mongo_db is not None:
            coleccion = mongo_db['predicciones_churn']
            cliente_data = coleccion.find_one({"id_cliente": id_cliente, "estado": estado})
            
        if not cliente_data:
            return jsonify({"error": "Cliente no encontrado"}), 404

        comparativa = cliente_data.get('comparativa_compras', {})
        contexto_cliente = f"""
        --- DATOS DEL NEGOCIO ---
        Mercado: México (Datos desde 2024)
        Canal de Venta: Tradicional (Abarrotes, Misceláneas, Tenderos)
        Portafolio de Foco: TCC, Monster Energy, Jugos del Valle.
        
        --- DATOS DEL CLIENTE EN RIESGO ---
        ID Cliente: {cliente_data.get('id_cliente')}
        Estado: {cliente_data.get('estado')}
        Tipo de Tienda: {cliente_data.get('tipo_tienda')}
        Nivel de Riesgo de Churn: {cliente_data.get('calificacion_riesgo', 0)}/5 ({cliente_data.get('probabilidad_churn', 0)}% de probabilidad)
        Promedio Histórico Mensual: {comparativa.get('promedio_historico_propio', 'N/A')} cajas
        Ventas Mes Actual: {comparativa.get('mes_actual', 'N/A')} cajas
        Diferencia: {comparativa.get('diferencia_cajas', 'N/A')} cajas
        Refrigeradores (Coolers) activos: {cliente_data.get('coolers_activos', 0)}
        """

        prompt = f"""
        Eres un estratega experto en ejecución comercial, finanzas y retención B2B para Arca Continental. 
        Tu objetivo es evitar que los clientes (tenderos) dejen de comprar, pero PROTEGIENDO LA RENTABILIDAD Y EL ROI de la empresa.
        
        {contexto_cliente}
        
        Genera un plan de acción de rescate súper breve y directo al grano, con 3 viñetas procesables para que el promotor de ruta lo ejecute mañana mismo.
        REGLAS ESTRICTAS:
        1. FACTOR CANAL TRADICIONAL MÉXICO: Usa terminología local (tendero, anaquel, rotación, ruta). 
        2. PORTAFOLIO: Tácticas impulsando TCC, Monster o Jugos del Valle.
        3. FACTOR GEOPOLÍTICO: Ubicación ({cliente_data.get('estado')}).
        4. RENTABILIDAD: Analiza refrigeradores ({cliente_data.get('coolers_activos', 0)}) vs volumen. No regales equipos sin justificación.
        5. Ve directo a las 3 viñetas.
        """

        respuesta = gemini_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto_crudo = respuesta.text.strip()

        texto_limpio = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_crudo)
        texto_limpio = texto_limpio.replace('* ', '• ').replace('\n', '<br>')
        
        return jsonify({"success": True, "recomendacion": texto_limpio, "cliente_id": id_cliente, "desde_bd": True})
    except Exception as e:
        return jsonify({"success": True, "recomendacion": "• Realizar visita inmediata.<br>• Auditar activos.", "cliente_id": id_cliente, "fallback": True})


# =====================
# ENDPOINTS RESTANTES MONGODB
# =====================
@app.route('/api/dashboard_data')
def api_dashboard_data():
    return jsonify(obtener_metricas())

@app.route('/api/estructura-datos')
def estructura_datos():
    if mongo_db is None: return jsonify({"error": "MongoDB no conectado"}), 500
    try:
        coleccion = mongo_db['predicciones_churn']
        documento = coleccion.find_one()
        if documento: documento['_id'] = str(documento['_id'])
        return jsonify({"success": True, "documento_ejemplo": documento})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/cliente-detail/<id_cliente>/<estado>')
def cliente_detail(id_cliente, estado):
    if mongo_db is None: return jsonify({"error": "MongoDB no conectado"}), 500
    try:
        coleccion = mongo_db['predicciones_churn']
        cliente = coleccion.find_one({"id_cliente": id_cliente, "estado": estado})
        if cliente:
            cliente['_id'] = str(cliente['_id'])
            return jsonify({"success": True, "cliente": cliente, "encontrado": True})
        return jsonify({"success": True, "encontrado": False})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/filtros-cascada')
def obtener_filtros_cascada():
    if mongo_db is None: return jsonify({"error": "MongoDB no conectado"}), 500
    try:
        coleccion = mongo_db['predicciones_churn']
        pipeline = [
            {"$group": {"_id": "$estado", "cantidad": {"$sum": 1}, "riesgo_promedio": {"$avg": "$probabilidad_churn"}, "clientes": {"$push": {"id_cliente": "$id_cliente", "probabilidad_churn": "$probabilidad_churn", "tipo_tienda": "$tipo_tienda"}}}},
            {"$sort": {"cantidad": -1}}, {"$limit": 10}
        ]
        datos = list(coleccion.aggregate(pipeline))
        resultado = []
        for item in datos:
            if item["_id"] is None: continue
            clientes_ordenados = sorted(item["clientes"], key=lambda x: x["probabilidad_churn"], reverse=True)[:3]
            resultado.append({"estado": item["_id"], "cantidad": item["cantidad"], "riesgo_promedio": round(item["riesgo_promedio"], 1), "clientes": clientes_ordenados})
        return jsonify({"success": True, "estados": resultado, "source": "mongodb"})
    except Exception as e: return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)