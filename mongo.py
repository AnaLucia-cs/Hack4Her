import pandas as pd
from pymongo import MongoClient

# 1. Configuración de conexión
# Asegúrate de que esta URI sea la correcta de tu cluster
MONGO_URI = "mongodb+srv://hannairachetal_db_user:DrMzpetUcITN0SG1@pilotoscosmicos.osx3t9d.mongodb.net/?appName=PilotosCosmicos"
DB_NAME = "Hack4Her_DB"
COLLECTION_NAME = "predicciones_churn"

def obtener_data_mongo():
    """Conecta a MongoDB y descarga toda la colección."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Obtenemos todos los documentos de la colección como una lista
        data = list(collection.find({}))
        print(f"Se encontraron {len(data)} documentos en MongoDB.")
        return data
    except Exception as e:
        print(f"Error al conectar con MongoDB: {e}")
        return None

def flatten_data(data):
    """Transforma la lista de documentos MongoDB a un DataFrame plano."""
    rows = []
    for c in data:
        # Extraemos los datos usando .get() para evitar errores si falta algún campo
        fila = {
            "estado": c.get("estado", "N/A"),
            "id_cliente": c.get("id_cliente", "N/A"),
            "tipo_tienda": c.get("tipo_tienda", "N/A"),
            "calificacion_riesgo": c.get("calificacion_riesgo", 0),
            "probabilidad_churn": c.get("probabilidad_churn", 0.0),
            "coolers_activos": c.get("coolers_activos", 0),
            # Mapeo de la estructura anidada 'comparativa_compras'
            "mes_anterior": c.get("comparativa_compras", {}).get("promedio_historico_3m", 0.0),
            "mes_actual": c.get("comparativa_compras", {}).get("mes_actual", 0.0),
            "diferencia": c.get("comparativa_compras", {}).get("diferencia", 0.0)
        }
        rows.append(fila)
    return pd.DataFrame(rows)

# Ejecución principal
if __name__ == "__main__":
    raw_data = obtener_data_mongo()
    
    if raw_data:
        df_final = flatten_data(raw_data)
        # Guardamos el archivo limpio para usarlo en el siguiente script
        df_final.to_csv("datos_limpios.csv", index=False)
        print("¡Pipeline terminado! Archivo 'datos_limpios.csv' generado exitosamente.")
        print(df_final.head()) # Mostramos las primeras filas para verificar
    else:
        print("No se pudo obtener la información. Revisa tu conexión a MongoDB.")