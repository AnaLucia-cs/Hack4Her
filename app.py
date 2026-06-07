import os
import re
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from dotenv import load_dotenv

# IMPORTAMOS EL NUEVO SDK EXACTAMENTE COMO LO TENÍAS
from google import genai 

# Cargar variables de entorno desde .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

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

# =====================
# CONEXIÓN A MONGODB
# =====================
mongodb_uri = os.getenv('MONGODB_URI') or os.getenv('MONGODB_ATLAS_URI')
mongo_client = None
mongo_db = None

try:
    if mongodb_uri:
        mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=3000)
        mongo_db = mongo_client[os.getenv('MONGODB_DB')]
        print(f"✓ MongoDB conectado: {os.getenv('MONGODB_DB')}")
except Exception as e:
    print(f"✗ Error conectando MongoDB: {e}")
    mongo_db = None

# =====================
# CONFIGURACIÓN GEMINI (NUEVO SDK)
# =====================
# 🚨 ¡PEGA TU LLAVE REAL AQUÍ ENTRE LAS COMILLAS! 🚨
GOOGLE_API_KEY = "AQ.Ab8RN6Lnq6OzIJ7N9YSNJ6jMh_PufvQ1FjYwSCu9-iyaY_OlTA" 
gemini_client = genai.Client(api_key=GOOGLE_API_KEY)


# =====================
# RUTAS DE VISTAS (PÁGINAS)
# =====================
@app.route('/api/hello')
def hello():
    return jsonify(message="¡Hola desde Flask!")

@app.route('/')
def index():
    return render_template("home.html", clientes_riesgo=125)

@app.route('/dashboards')
@app.route('/Dashboards')
def dashboard():
    return render_template(
        "dashboards.html",
        total_clientes=1000,
        clientes_riesgo=125,
        perdida_estimada=300000,
        id="12345",
        tipo_negocio="Restaurante",
        perdida_aprox=10000,
        indice_riesgo="Alto"
    )

@app.route('/clientes')
@app.route('/Clientes')
def clientes():
    return render_template(
        "clientes.html",
        id="12345",
        tipo_negocio="Restaurante",
        perdida_aprox=10000,
        indice_riesgo="Alto"
    )


# =====================
# API PARA RECOMENDACIONES CON GEMINI (CON TU PROMPT MAESTRO)
# =====================

@app.route('/api/recomendacion-gemini', methods=['POST'])
def obtener_recomendacion_gemini():
    """
    Genera una recomendación usando el Prompt Evolucionado
    Extrayendo los datos directamente de MongoDB
    """
    data = request.json
    id_cliente = data.get('id_cliente')
    estado = data.get('estado')
    
    if not id_cliente or not estado:
        return jsonify({"error": "Faltan parámetros requeridos"}), 400
    
    try:
        # 1. EXTRAER DATOS DEL CLIENTE DESDE MONGODB
        cliente_data = None
        if mongo_db is not None:
            coleccion = mongo_db['predicciones_churn']
            cliente_data = coleccion.find_one({"id_cliente": id_cliente, "estado": estado})
            
        if not cliente_data:
            return jsonify({"error": "Cliente no encontrado en la base de datos"}), 404

        # 2. CONSTRUIR TU CONTEXTO CON LOS DATOS DE LA BD
        comparativa = cliente_data.get('comparativa_compras', {})
        contexto_cliente = f"""
        --- DATOS DEL NEGOCIO ---
        Mercado: México (Datos desde 2024)
        Canal de Venta: Tradicional (Abarrotes, Misceláneas, Tenderos)
        Portafolio de Foco: TCC (The Coca-Cola Company), Monster Energy, Jugos del Valle.
        
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

        # 3. TU PROMPT MAESTRO EVOLUCIONADO
        prompt = f"""
        Eres un estratega experto en ejecución comercial, finanzas y retención B2B para Arca Continental. 
        Tu objetivo es evitar que los clientes (tenderos) dejen de comprar, pero PROTEGIENDO LA RENTABILIDAD Y EL ROI de la empresa.
        
        A continuación, te presento el perfil de un cliente en riesgo crítico:
        {contexto_cliente}
        
        Genera un plan de acción de rescate súper breve y directo al grano, con 3 viñetas procesables para que el promotor de ruta lo ejecute mañana mismo.
        
        REGLAS ESTRICTAS PARA TU ANÁLISIS:
        1. FACTOR CANAL TRADICIONAL MÉXICO: Usa terminología local apropiada (tendero, anaquel, rotación, ruta). 
        2. PORTAFOLIO: Al menos una de tus viñetas debe sugerir una táctica directa impulsando TCC, Monster o Jugos del Valle (ej. combos, material POP, exhibición adicional).
        3. FACTOR GEOPOLÍTICO: Menciona cómo la ubicación ({cliente_data.get('estado')}) influye en la estrategia de consumo.
        4. RENTABILIDAD Y ACTIVOS (REGLA DE ORO): Analiza su cantidad de refrigeradores ({cliente_data.get('coolers_activos', 0)}) vs su volumen de cajas. 
           - ESTÁ PROHIBIDO regalar instalaciones masivas o enviar refrigeradores sin justificación. 
           - Si tiene 0 coolers y volumen bajo, sugiere alternativas baratas (hieleras de mostrador, material POP) o condiciona un equipo a que firme un compromiso de volumen. 
           - Si tiene coolers activos pero sus ventas se desplomaron, exige una advertencia de retiro de equipo por baja rentabilidad o una auditoría para asegurar que no los usa para la competencia.
        5. No uses introducciones largas ni saludos, ve directo a las 3 viñetas.
        """

        # 4. LLAMADA A GEMINI CON TU LÓGICA DE RESPALDO (TRY/EXCEPT)
        texto_crudo = ""
        try:
            # Intento con el modelo 2.5
            respuesta = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            texto_crudo = respuesta.text.strip()
            
        except Exception as e_25:
            print(f"Modelo 2.5 no disponible, intentando con 2.0-flash... ({e_25})")
            # Respaldo con el modelo 2.0
            respuesta = gemini_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            texto_crudo = respuesta.text.strip()

        # 5. FORMATEO DE MARKDOWN A HTML
        # Convertir **texto** de Markdown a <b>texto</b> de HTML (Negritas)
        texto_limpio = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto_crudo)
        # Cambiar el asterisco de lista por un punto de viñeta estético
        texto_limpio = texto_limpio.replace('* ', '• ')
        # Mantener los saltos de línea reales usando <br> para que no se amontone
        texto_limpio = texto_limpio.replace('\n', '<br>')
        
        recomendacion = texto_limpio

        # 6. RETORNAR AL FRONTEND
        return jsonify({
            "success": True,
            "recomendacion": recomendacion,
            "cliente_id": id_cliente,
            "desde_bd": True
        })
    
    except Exception as e:
        print(f"Error general en la ruta de Gemini: {str(e)}")
        # Fallback de emergencia por si truena la conexión o el prompt
        return jsonify({
            "success": True,
            "recomendacion": f"""<b>Acciones recomendadas de emergencia:</b><br><br>
• Realizar visita de supervisión inmediata.<br>
• Revisar portafolio de foco (TCC, Monster).<br>
• Auditar rentabilidad del equipo en comodato.""",
            "cliente_id": id_cliente,
            "fallback": True
        })


# =====================
# RESTO DE TUS ENDPOINTS DE DATOS (MANTENIDOS INTACTOS)
# =====================

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
            {"$sort": {"cantidad": -1}},
            {"$limit": 10}
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
    