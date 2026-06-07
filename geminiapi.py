from google import genai
import json

# ==========================================
# 1. CONFIGURACIÓN DE GEMINI (NUEVO SDK)
# ==========================================
# 🚨 ¡PEGA TU NUEVA LLAVE REAL AQUÍ ENTRE LAS COMILLAS! 🚨
GOOGLE_API_KEY = "AQ.Ab8RN6ItSHvf6TkTY2v5uIi3snPSawTmQN6v_nRGUKDtk4-e8g" 

# Iniciamos el cliente con la nueva librería
client = genai.Client(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. CARGA DE DATOS Y FILTRADO
# ==========================================
print("Cargando clientes en riesgo...")
ruta_archivo = r"C:\Users\Isidro Zavala\OneDrive\Desktop\Hack4Her\datos_riesgo_por_estado.json"

with open(ruta_archivo, 'r', encoding='utf-8') as f:
    datos_agrupados = json.load(f)

# Vamos a recolectar solo a los clientes que necesitan atención urgente (Riesgo 4 y 5)
clientes_urgentes = []

for estado, clientes in datos_agrupados.items():
    for cliente in clientes:
        if cliente['calificacion_riesgo'] >= 4:
            # Le inyectamos el estado al diccionario para que Gemini tenga contexto geográfico
            cliente['estado'] = estado
            clientes_urgentes.append(cliente)

print(f"Se encontraron {len(clientes_urgentes)} clientes en Riesgo Crítico (Nivel 4 y 5).")

# ==========================================
# 3. GENERACIÓN DE PLANES DE ACCIÓN CON IA
# ==========================================
print("\nGenerando estrategias comerciales con Gemini...\n" + "="*50)

# Limitaremos a los primeros 3 clientes para hacer pruebas rápidas. 
# (Quita el [:3] para analizarlos todos cuando ya vayas a presentar)
for cliente in clientes_urgentes[:3]:
    
    # Construimos un contexto claro y estructurado a partir de tu JSON y los filtros del negocio
    contexto_cliente = f"""
    --- DATOS DEL NEGOCIO ---
    Mercado: México (Datos desde 2024)
    Canal de Venta: Tradicional (Abarrotes, Misceláneas, Tenderos)
    Portafolio de Foco: TCC (The Coca-Cola Company), Monster Energy, Jugos del Valle.
    
    --- DATOS DEL CLIENTE EN RIESGO ---
    ID Cliente: {cliente['id_cliente']}
    Estado: {cliente['estado']}
    Tipo de Tienda: {cliente['tipo_tienda']}
    Nivel de Riesgo de Churn: {cliente['calificacion_riesgo']}/5 ({cliente['probabilidad_churn']}% de probabilidad)
    Promedio Histórico Mensual: {cliente.get('comparativa_compras', {}).get('promedio_historico_3m', 'N/A')} cajas
    Ventas Mes Actual: {cliente.get('comparativa_compras', {}).get('mes_actual', 'N/A')} cajas
    Diferencia: {cliente.get('comparativa_compras', {}).get('diferencia', 'N/A')} cajas
    Refrigeradores (Coolers) activos: {cliente['coolers_activos']}
    """

    # El Prompt Maestro Evolucionado con Control de Rentabilidad
    prompt = f"""
    Eres un estratega experto en ejecución comercial, finanzas y retención B2B para Arca Continental. 
    Tu objetivo es evitar que los clientes (tenderos) dejen de comprar, pero PROTEGIENDO LA RENTABILIDAD Y EL ROI de la empresa.
    
    A continuación, te presento el perfil de un cliente en riesgo crítico:
    {contexto_cliente}
    
    Genera un plan de acción de rescate súper breve y directo al grano, con 3 viñetas procesables para que el promotor de ruta lo ejecute mañana mismo.
    
    REGLAS ESTRICTAS PARA TU ANÁLISIS:
    1. FACTOR CANAL TRADICIONAL MÉXICO: Usa terminología local apropiada (tendero, anaquel, rotación, ruta). 
    2. PORTAFOLIO: Al menos una de tus viñetas debe sugerir una táctica directa impulsando TCC, Monster o Jugos del Valle (ej. combos, material POP, exhibición adicional).
    3. FACTOR GEOPOLÍTICO: Menciona cómo la ubicación ({cliente['estado']}) influye en la estrategia de consumo.
    4. RENTABILIDAD Y ACTIVOS (REGLA DE ORO): Analiza su cantidad de refrigeradores ({cliente['coolers_activos']}) vs su volumen de cajas. 
       - ESTÁ PROHIBIDO regalar instalaciones masivas o enviar refrigeradores sin justificación. 
       - Si tiene 0 coolers y volumen bajo, sugiere alternativas baratas (hieleras de mostrador, material POP) o condiciona un equipo a que firme un compromiso de volumen. 
       - Si tiene coolers activos pero sus ventas se desplomaron, exige una advertencia de retiro de equipo por baja rentabilidad o una auditoría para asegurar que no los usa para la competencia.
    5. No uses introducciones largas ni saludos, ve directo a las 3 viñetas.
    """
    
    try:
        # Llamamos a la API usando el modelo estable más actual
        respuesta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # Imprimimos el resultado de forma bonita
        print(f"🚨 ESTRATEGIA PARA CLIENTE: {cliente['id_cliente']}")
        print(f"📍 Contexto: {cliente['tipo_tienda']} en {cliente['estado']} | Riesgo: {cliente['calificacion_riesgo']}/5")
        print("-" * 40)
        print(respuesta.text.strip())
        print("=" * 50 + "\n")
        
    except Exception as e:
        # Si el modelo 2.5 no está disponible por alguna configuración, saltamos automáticamente a la versión 2.0
        try:
            print("Intentando con modelo alternativo de respaldo (2.0-flash)...")
            respuesta = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            print(f"🚨 ESTRATEGIA PARA CLIENTE: {cliente['id_cliente']}")
            print(f"📍 Contexto: {cliente['tipo_tienda']} en {cliente['estado']} | Riesgo: {cliente['calificacion_riesgo']}/5")
            print("-" * 40)
            print(respuesta.text.strip())
            print("=" * 50 + "\n")
        except Exception as e_inner:
            print(f"Hubo un error al consultar a Gemini: {e_inner}")