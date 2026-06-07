import pandas as pd
import numpy as np
from pymongo import MongoClient
import json

# ==========================================
# FASE 1: CONEXIÓN Y EXTRACCIÓN
# ==========================================
print("1. Conectando a MongoDB Atlas...")
MONGO_URI = "mongodb+srv://hannairachetal_db_user:DrMzpetUcITN0SG1@pilotoscosmicos.osx3t9d.mongodb.net/?appName=PilotosCosmicos"
client = MongoClient(MONGO_URI)
db = client['Hack4Her_DB'] 

print("2. Descargando colecciones...")
df_clientes = pd.DataFrame(list(db['clientes'].find()))
df_ventas = pd.DataFrame(list(db['sales_churn_train'].find()))
df_coolers = pd.DataFrame(list(db['coolers'].find()))

# ==========================================
# FASE 2: LIMPIEZA Y UNIÓN (JOIN)
# ==========================================
print("3. Limpiando y uniendo los datos...")

for d in [df_clientes, df_ventas, df_coolers]:
    if '_id' in d.columns:
        d.drop(columns=['_id'], inplace=True)

df_ventas['num_transacciones'] = pd.to_numeric(df_ventas['num_transacciones'], errors='coerce')
df_ventas['uni_boxes_sold_m'] = pd.to_numeric(df_ventas['uni_boxes_sold_m'], errors='coerce')
df_coolers['num_coolers'] = pd.to_numeric(df_coolers['num_coolers'], errors='coerce')

df_master = pd.merge(df_ventas, df_coolers, on=['customer_id', 'calmonth'], how='left')
df_master['num_coolers'] = df_master['num_coolers'].fillna(0)
df = pd.merge(df_master, df_clientes, on='customer_id', how='left')

df['comercial_subchannel_d'] = df['comercial_subchannel_d'].fillna('Desconocido')
df['territory_d'] = df['territory_d'].fillna('Desconocido')


# ==========================================
# FASE 3: EVALUACIÓN INDEPENDIENTE POR CLIENTE
# ==========================================
print("4. Evaluando el rendimiento individual de cada cliente...")

df = df.sort_values(by=['customer_id', 'calmonth'])

# Calculamos el promedio de ventas de los últimos 3 meses de CADA cliente
df['promedio_ventas_3m'] = df.groupby('customer_id')['uni_boxes_sold_m'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean().shift(1)
)

# Si es nuevo, su promedio es lo que vendió este mes (para no borrarlo)
df['promedio_ventas_3m'] = df['promedio_ventas_3m'].fillna(df['uni_boxes_sold_m'])

# Diferencia exacta en cajas
df['delta_ventas'] = df['uni_boxes_sold_m'] - df['promedio_ventas_3m']

# Caída porcentual respecto a SÍ MISMO
df['porcentaje_caida'] = np.where(
    df['promedio_ventas_3m'] > 0,
    (df['delta_ventas'] / df['promedio_ventas_3m']) * 100,
    0
)


# ==========================================
# FASE 4: ASIGNACIÓN DE RIESGO (REGLAS DE NEGOCIO)
# ==========================================
print("\n" + "="*50)
print(" 🚀 APLICANDO REGLAS DE NEGOCIO INDEPENDIENTES ")
print("="*50 + "\n")

# Nos quedamos solo con los datos del mes actual para calificar
mes_actual = df['calmonth'].max()
clientes_hoy = df[(df['calmonth'] == mes_actual) & (df['uni_boxes_sold_m'] > 0)].copy()

# Reglas Duras e Independientes basadas en la caída porcentual individual
condiciones = [
    (clientes_hoy['porcentaje_caida'] <= -50),  # Cayó más de la mitad (Crítico)
    (clientes_hoy['porcentaje_caida'] <= -25),  # Cayó más de un cuarto (Alto)
    (clientes_hoy['porcentaje_caida'] <= -10),  # Cayó un poco (Medio)
    (clientes_hoy['porcentaje_caida'] < 0),     # Cayó casi nada (Bajo)
    (clientes_hoy['porcentaje_caida'] >= 0)     # Se mantuvo o creció (Sano)
]
valores_riesgo = [5, 4, 3, 2, 1]

clientes_hoy['calificacion_riesgo'] = np.select(condiciones, valores_riesgo, default=1)

print(f"✅ Análisis completado para {len(clientes_hoy)} clientes ACTIVOS en el mes {mes_actual}.")
print("📊 Distribución Real de Riesgos:")
print(clientes_hoy['calificacion_riesgo'].value_counts().sort_index(ascending=False))


# ==========================================
# FASE 5: EXPORTACIÓN JSON
# ==========================================
print("\n5. Categorizando y exportando JSON estructurado...")

datos_agrupados_gemini = {}

for index, fila in clientes_hoy.iterrows():
    estado = str(fila['territory_d'])
    caida = float(fila['porcentaje_caida'])
    
    # Justificación lógica para Gemini
    if caida <= -50:
        justificacion = f"COLAPSO DE VENTAS: El cliente perdió el {abs(caida):.1f}% de su volumen habitual."
    elif caida <= -25:
        justificacion = f"ALERTA ROJA: Las ventas del cliente bajaron un {abs(caida):.1f}% frente a su propio historial."
    elif caida < 0:
        justificacion = f"LIGERA BAJA: El cliente disminuyó sus ventas un {abs(caida):.1f}%. Monitorear."
    else:
        justificacion = "CRECIMIENTO/ESTABILIDAD: El cliente mantiene o mejora sus números."

    cliente_json = {
        "id_cliente": str(fila['customer_id']), 
        "tipo_tienda": str(fila['comercial_subchannel_d']),
        "calificacion_riesgo": int(fila['calificacion_riesgo']),
        "justificacion_riesgo": justificacion,
        "comparativa_compras": {
            "promedio_historico_propio": float(fila['promedio_ventas_3m']),
            "mes_actual": float(fila['uni_boxes_sold_m']),
            "diferencia_cajas": float(fila['delta_ventas']),
            "porcentaje_caida": caida
        },
        "coolers_activos": int(fila['num_coolers'])
    }
    
    if estado not in datos_agrupados_gemini:
        datos_agrupados_gemini[estado] = []
        
    datos_agrupados_gemini[estado].append(cliente_json)

ruta_archivo_json = r"C:\Users\Isidro Zavala\OneDrive\Desktop\Hack4Her\datos_riesgo_por_estado.json"
with open(ruta_archivo_json, 'w', encoding='utf-8') as f:
    json.dump(datos_agrupados_gemini, f, indent=4, ensure_ascii=False)

print(f"📦 ¡Listo! JSON guardado en: {ruta_archivo_json}")

# ==========================================
# FASE 6: SUBIR RESULTADOS A MONGODB
# ==========================================
print("\n6. Subiendo análisis final a MongoDB Atlas...")
coleccion_resultados = db['predicciones_churn']
coleccion_resultados.delete_many({}) 

documentos_a_subir = []
for estado, clientes in datos_agrupados_gemini.items():
    for cliente in clientes:
        doc = cliente.copy()
        doc['estado'] = estado 
        documentos_a_subir.append(doc)

if documentos_a_subir:
    coleccion_resultados.insert_many(documentos_a_subir)
    print(f"🚀 ¡Éxito! {len(documentos_a_subir)} predicciones independientes guardadas en MongoDB.")