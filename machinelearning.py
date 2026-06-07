import pandas as pd
from pymongo import MongoClient

# ==========================================
# FASE 1: CONEXIÓN Y EXTRACCIÓN
# ==========================================
print("1. Conectando a MongoDB Atlas...")

# Tu cadena de conexión real
MONGO_URI = "mongodb+srv://hannairachetal_db_user:DrMzpetUcITN0SG1@pilotoscosmicos.osx3t9d.mongodb.net/?appName=PilotosCosmicos"
client = MongoClient(MONGO_URI)

# Los nombres EXACTOS que nos dio tu diagnóstico
db = client['Hack4Her_DB'] 

print("2. Descargando colecciones por separado...")
df_clientes = pd.DataFrame(list(db['clientes'].find()))
df_ventas = pd.DataFrame(list(db['sales_churn_train'].find()))
df_coolers = pd.DataFrame(list(db['coolers'].find()))

print(f"-> Clientes: {len(df_clientes)} | Ventas: {len(df_ventas)} | Coolers: {len(df_coolers)}")

# ==========================================
# FASE 2: LIMPIEZA Y UNIÓN (JOIN)
# ==========================================
print("\n3. Limpiando y uniendo los datos...")

# 2.1 Quitar la columna '_id' de Mongo que no nos sirve
for df in [df_clientes, df_ventas, df_coolers]:
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)

# 2.2 Convertir los "números de texto" a números reales para poder hacer matemáticas
df_ventas['num_transacciones'] = pd.to_numeric(df_ventas['num_transacciones'], errors='coerce')
df_ventas['uni_boxes_sold_m'] = pd.to_numeric(df_ventas['uni_boxes_sold_m'], errors='coerce')
df_ventas['target'] = pd.to_numeric(df_ventas['target'], errors='coerce')

df_coolers['num_coolers'] = pd.to_numeric(df_coolers['num_coolers'], errors='coerce')

# 2.3 Unir Ventas con Coolers (Usando el ID del cliente y el Mes)
df_master = pd.merge(df_ventas, df_coolers, on=['customer_id', 'calmonth'], how='left')

# Si un cliente no tiene coolers en ese mes, Pandas pone NaN. Lo cambiamos a 0.
df_master['num_coolers'] = df_master['num_coolers'].fillna(0)

# 2.4 Unir el resultado con la base de Clientes
df = pd.merge(df_master, df_clientes, on='customer_id', how='left')


# ==========================================
# FASE 3: INGENIERÍA DE CARACTERÍSTICAS
# ==========================================
print("4. Calculando métricas de riesgo y tendencias...")

# Ordenar cronológicamente
df = df.sort_values(by=['customer_id', 'calmonth'])

# Calcular caída de ventas (Delta)
df['ventas_mes_anterior'] = df.groupby('customer_id')['uni_boxes_sold_m'].shift(1)
df['delta_ventas'] = df['uni_boxes_sold_m'] - df['ventas_mes_anterior']

# Porcentaje de caída (evitando dividir entre 0)
df['porcentaje_caida'] = df.apply(
    lambda x: (x['delta_ventas'] / x['ventas_mes_anterior']) * 100 if x['ventas_mes_anterior'] > 0 else 0,
    axis=1
)

# Eficiencia: Cajas por Cooler
df['cajas_por_cooler'] = df.apply(
    lambda x: x['uni_boxes_sold_m'] / x['num_coolers'] if x['num_coolers'] > 0 else x['uni_boxes_sold_m'], 
    axis=1
)

# Limpiar los nulos generados por el shift del primer mes
df = df.dropna(subset=['delta_ventas', 'target'])


# ==========================================
# FASE 4: RESULTADOS DEL RETO
# ==========================================
print("\n" + "="*50)
print(" RESULTADOS DEL HACKATON ")
print("="*50 + "\n")

print("📍 PREGUNTA 1: Impacto de las variables en el Churn (Correlación)")
columnas_analisis = [
    'uni_boxes_sold_m', 'num_transacciones', 'num_coolers', 
    'delta_ventas', 'porcentaje_caida', 'cajas_por_cooler', 'target'
]

# Filtrar solo columnas que sí existan y calcular correlación
columnas_existentes = [col for col in columnas_analisis if col in df.columns]
correlaciones = df[columnas_existentes].corr()['target'].sort_values(ascending=False)
correlaciones = correlaciones.drop('target') 

print("🔴 Factores de Riesgo (Positivos impulsan el Churn):")
print(correlaciones[correlaciones > 0].round(3))
print("\n🟢 Factores de Retención (Negativos previenen el Churn):")
print(correlaciones[correlaciones < 0].round(3))
print("-" * 40)

print("\n📍 PREGUNTA 2: Riesgo de Churn por Territorio")
if 'territory_d' in df.columns:
    churn_territorio = df.groupby('territory_d')['target'].mean() * 100
    churn_territorio = churn_territorio.sort_values(ascending=False).round(2)
    print("Porcentaje de clientes perdidos por zona:")
    for zona, porcentaje in churn_territorio.items():
        print(f"- {zona}: {porcentaje}% de churn")
print("-" * 40)

print("\n📍 PREGUNTA 3: Riesgo de Churn vs Cantidad de Coolers")
if 'num_coolers' in df.columns:
    churn_coolers = df.groupby('num_coolers')['target'].mean() * 100
    churn_coolers = churn_coolers.sort_values(ascending=False).round(2)
    print("Porcentaje de fuga según número de refrigeradores:")
    for coolers, porcentaje in churn_coolers.items():
        print(f"- {int(coolers)} Coolers: {porcentaje}% de churn")
print("="*50)