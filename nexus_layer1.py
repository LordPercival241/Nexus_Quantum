import networkx as nx
import json
import pandas as pd
import numpy as np
import time
import os
import feedparser
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURACIÓN DE LA API ---
try:
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError("No se encontró la variable de entorno GOOGLE_API_KEY")
    genai.configure(api_key=API_KEY)
    GENERATIVE_MODEL = genai.GenerativeModel('models/gemini-2.5-flash') 
    print(" [Capa 1] Motor de IA (Gemini) v6.1 cargado (Prompt Maestro).")
except Exception as e:
    print(f" [Capa 1] Error al configurar la API de Gemini: {e}")
    GENERATIVE_MODEL = None

# --- CLASE PRINCIPAL DEL ATLAS ---
class AtlasEconomico:
    """Representa el "Atlas Económico" de la Capa 1."""
    def __init__(self, nodos_centrales, aristas_base):
        self.nodos = nodos_centrales
        self.aristas = aristas_base
        self.G = self._construir_grafo_base()
        self._inicializar_gscores()
        print(f"🗺️ [Capa 1] Atlas Económico inicializado con {self.G.number_of_nodes()} nodos.")

    def _construir_grafo_base(self):
        G = nx.DiGraph()
        G.add_nodes_from(self.nodos)
        for u, v, data in self.aristas:
            G.add_edge(u, v, tipo=data['tipo'], peso=data.get('peso', 1.0))
        return G

    def _inicializar_gscores(self):
        nx.set_node_attributes(self.G, 0.0, 'g_score')

    def obtener_gscores(self):
        return nx.get_node_attributes(self.G, 'g_score')

    def aplicar_decay(self, factor_decay=0.99):
        scores = self.obtener_gscores()
        for nodo in scores:
            scores[nodo] *= factor_decay
            if scores[nodo] < 0.01: scores[nodo] = 0.0
        nx.set_node_attributes(self.G, scores, 'g_score')

    def actualizar_grafo_con_ia(self, evento_grafo):
        """
        Lee el *diccionario* del "Constructor de Grafos" y actualiza el "Atlas".
        """
        try:
            accion = evento_grafo.get('accion_de_grafo')
            if not accion or accion == "NINGUNA":
                return False

            origen = evento_grafo.get('nodo_origen')
            destino = evento_grafo.get('nodo_destino')
            tipo = evento_grafo.get('tipo_relacion')

            if not all([origen, destino, tipo]):
                return False
            
            # Asegurarse de que los nodos existan antes de añadir arista
            if origen not in self.G: self.G.add_node(origen)
            if destino not in self.G: self.G.add_node(destino)

            if accion == "AÑADIR_ARISTA":
                if not self.G.has_edge(origen, destino):
                    print(f"  [Atlas Constructor]  NUEVA RELACIÓN: {origen} -> {tipo} -> {destino}")
                    self.G.add_edge(origen, destino, tipo=tipo)
                    return True
            elif accion == "ELIMINAR_ARISTA":
                if self.G.has_edge(origen, destino):
                    print(f"  [Atlas Constructor] ❄️ RELACIÓN ROTA: {origen} -X- {destino}")
                    self.G.remove_edge(origen, destino)
                    return True
        except Exception as e:
            print(f"  [Atlas Constructor Error]: {e}")
        return False

    def procesar_evento_cuantitativo(self, evento_riesgo, log_prefix=""):
        """
        Procesa un evento de RIESGO CUANTITATIVO (del *diccionario*).
        """
        try:
            nodo_afectado = evento_riesgo.get('nodo_afectado_riesgo')
            tipo_impacto = evento_riesgo.get('tipo_de_impacto')
            
            if not nodo_afectado or not tipo_impacto or tipo_impacto == "NINGUNO":
                return False

            mapa_de_riesgo = {
                "RETRASO_PRODUCCION": 0.8,
                "INCENDIO_FABRICA": 1.0,
                "MULTA_REGULATORIA": 0.5,
                "CAIDA_DEMANDA": 0.6,
                "INVESTIGACION_LEGAL": 0.4,
                "RESTRICCION_GEOPOLITICA": 0.9,
                "OTRO_NEGATIVO": 0.3
            }
            shock_base = mapa_de_riesgo.get(tipo_impacto, 0.0)
            if shock_base == 0.0:
                return False

            # --- Propagación ---
            self.G.nodes[nodo_afectado]['g_score'] += shock_base
            print(f"{log_prefix}  [SHOCK 1er O]: {nodo_afectado} ({tipo_impacto}) g_score +{shock_base:.2f}")

            factor_propagacion = 0.4
            for sucesor in self.G.successors(nodo_afectado):
                arista_data = self.G.get_edge_data(nodo_afectado, sucesor)
                if arista_data.get('tipo') == 'proveedor_de':
                    shock_propagado = shock_base * factor_propagacion
                    self.G.nodes[sucesor]['g_score'] += shock_propagado
                    print(f"{log_prefix}   ->  [SHOCK 2º O -> Cliente]: {sucesor} g_score +{shock_propagado:.2f}")
            for predecesor in self.G.predecessors(nodo_afectado):
                arista_data = self.G.get_edge_data(predecesor, nodo_afectado)
                if arista_data.get('tipo') == 'proveedor_de':
                    shock_propagado = shock_base * (factor_propagacion * 0.5)
                    self.G.nodes[predecesor]['g_score'] += shock_propagado
                    print(f"{log_prefix}   ->  [SHOCK 2º O -> Prov]: {predecesor} g_score +{shock_propagado:.2f}")
            return True
        except Exception as e:
            print(f"{log_prefix} ⚠️ Error procesando evento: {e}")
            return False

# --- MOTOR DE "COMBUSTIBLE" (LLMs Y RSS) ---

def _llamar_api_gemini(prompt):
    """Función helper para manejar la API y los límites de tasa."""
    if not GENERATIVE_MODEL:
        return None
    try:
        # Añadir un 'sleep' *antes* de la llamada para respetar el límite
        time.sleep(6) # ~10 llamadas por minuto
        respuesta = GENERATIVE_MODEL.generate_content(prompt)
        json_texto = respuesta.text.strip().replace("```json", "").replace("```", "")
        return json_texto
    except Exception as e:
        print(f"  [LLM Error]: {e}")
        # Manejar el error de límite de tasa 429
        if "429" in str(e):
            print("  [LLM Error] Límite de tasa excedido. Esperando 60 segundos...")
            time.sleep(60)
            return _llamar_api_gemini(prompt) # Reintentar
        return None

# ------------------------------------------------------------------
# --- ¡NUEVA FUNCIÓN! (Soluciona Debilidad 3) ---
# ------------------------------------------------------------------
def analisis_completo_ia(texto_noticia, nodos_relevantes):
    """
    LLM MAESTRO (v6.1) - El "Córtex de 1 Etapa"
    Resuelve Veracidad, Traducción, Hechos Quant y Actualización de Grafo
    en UNA SOLA LLAMADA a la API.
    """
    prompt = f"""
    Eres un equipo de analistas de IA de un fondo de cobertura: "El Verificador", "El Traductor", "El Analista Quant" y "El Constructor de Grafos".
    Tu trabajo es procesar esta noticia en 4 etapas y devolver UN solo objeto JSON.

    Noticia: "{texto_noticia}"
    Empresas a monitorear: {nodos_relevantes}

    ---
    ETAPA 1: TRADUCTOR
    - Si la noticia no está en inglés, tradúcela.

    ETAPA 2: VERIFICADOR
    - ¿Es esta noticia un HECHO CONFIRMADO (reportado por fuentes oficiales/múltiples) o un RUMOR/ESPECULACIÓN?
    - Responde en "es_verificado": true | false.
    - Responde en "razonamiento_verificacion": "Tu razonamiento en 1 frase."
    - Si "es_verificado" es false, ignora las Etapas 3 y 4.

    ETAPA 3: ANALISTA QUANT (Solo si es_verificado = true)
    - Extrae el HECHO de riesgo, no el sentimiento.
    - Tipos de Impacto Válidos: ["RETRASO_PRODUCCION", "INCENDIO_FABRICA", "MULTA_REGULATORIA", "CAIDA_DEMANDA", "INVESTIGACION_LEGAL", "RESTRICCION_GEOPOLITICA", "OTRO_NEGATIVO", "NINGUNO"]
    - Responde en "nodo_afectado_riesgo": "TICKER" | null
    - Responde en "tipo_de_impacto": "<Uno de los Tipos de Impacto Válidos>"

    ETAPA 4: CONSTRUCTOR DE GRAFOS (Solo si es_verificado = true)
    - ¿Describe la noticia el INICIO o FIN de una relación de PROVEEDOR, CLIENTE o COMPETIDOR entre dos de las empresas monitoreadas?
    - Acciones Válidas: ["AÑADIR_ARISTA", "ELIMINAR_ARISTA", "NINGUNA"]
    - Tipos de Relación Válidos: ["proveedor_de", "cliente_de", "competidor_de"]
    - Responde en "accion_de_grafo": "<Acción Válida>"
    - Responde en "nodo_origen": "TICKER_A" | null
    - Responde en "nodo_destino": "TICKER_B" | null
    - Responde en "tipo_relacion": "<Tipo de Relación Válido>" | null
    ---

    Responde SOLAMENTE con el objeto JSON final.
    """
    
    json_texto = _llamar_api_gemini(prompt)
    if not json_texto: return json.dumps({"es_verificado": False})
    
    try:
        # Validar que es un JSON antes de devolver
        json.loads(json_texto)
        return json_texto
    except Exception as e:
        print(f"  [LLM Maestro Error] JSON inválido: {e}")
        return json.dumps({"es_verificado": False})

def obtener_noticias_rss(feeds_rss, articulos_vistos):
    """Se conecta a los feeds RSS y devuelve nuevos artículos."""
    # (Sin cambios)
    print(f"Buscando nuevas noticias en {len(feeds_rss)} feeds...")
    nuevos_articulos = []
    for feed_url in feeds_rss:
        try:
            d = feedparser.parse(feed_url)
            for entry in d.entries:
                if entry.link not in articulos_vistos:
                    articulos_vistos.add(entry.link)
                    texto_noticia = f"{entry.title} - {entry.summary}"
                    nuevos_articulos.append(texto_noticia)
        except Exception as e:
            print(f"  Error en feed {feed_url}: {e}")
    return nuevos_articulos, articulos_vistos


# ------------------------------------------------------------------
# --- ¡FUNCIÓN PRINCIPAL MODIFICADA! (v6.1) ---
# ------------------------------------------------------------------
def obtener_live_gscores(atlas_vivo, nodos_relevantes, feeds):
    """
    FUNCIÓN PRINCIPAL DE CAPA 1 (v6.1 - Optimizada y Escalable)
    Usa el "Córtex de 1 Etapa" (1 llamada a la API por artículo).
    """
    print(f"\n--- [CAPA 1] Iniciando Snapshot de Riesgo v6.1 (Prompt Maestro) ---")
    
    articulos_nuevos, _ = obtener_noticias_rss(feeds, set())
    if not articulos_nuevos:
        print("[Capa 1] No se encontraron noticias nuevas. GScores en 0.")
        return atlas_vivo.obtener_gscores()

    print(f"[Capa 1] Encontrados {len(articulos_nuevos)} artículos para analizar.")
    
    shocks_detectados = 0
    shocks_descartados = 0
    relaciones_actualizadas = 0
    
    for i, texto in enumerate(articulos_nuevos):
        print(f"\n  Procesando Artículo {i+1}/{len(articulos_nuevos)}...")
        
        # --- UNA SOLA LLAMADA A LA IA ---
        json_respuesta = analisis_completo_ia(texto, nodos_relevantes)
        try:
            respuesta = json.loads(json_respuesta)
        except Exception:
            print("  [Analista] Respuesta de IA inválida. Descartando.")
            respuesta = {"es_verificado": False}
        
        # --- ETAPA 1: VERIFICADOR ---
        if respuesta.get("es_verificado") == True:
            print(f"  [Analista] Noticia VERIFICADA. {respuesta.get('razonamiento_verificacion')}")

            # --- ETAPA 2: CONSTRUCTOR DE GRAFOS ---
            # Pasamos el *diccionario* de respuesta
            if atlas_vivo.actualizar_grafo_con_ia(respuesta):
                relaciones_actualizadas += 1
            
            # --- ETAPA 3: ANALISTA DE RIESGO ---
            # Pasamos el *diccionario* de respuesta
            if atlas_vivo.procesar_evento_cuantitativo(respuesta):
                shocks_detectados += 1
        else:
            print(f"  [Analista] Noticia DESCARTADA. {respuesta.get('razonamiento_verificacion')}")
            shocks_descartados += 1
            
    print(f"\n[Capa 1] Snapshot completado.")
    print(f"  {shocks_detectados} shocks de riesgo procesados.")
    print(f"  {relaciones_actualizadas} relaciones del Atlas actualizadas.")
    print(f"  {shocks_descartados} artículos descartados como falsos/ruido.")
    
    return atlas_vivo.obtener_gscores()


# --- Sección de Prueba (si ejecutas este archivo directamente) ---
if __name__ == "__main__":
    print("--- [Capa 1] Ejecutando prueba de módulo v6.1 ---")
    
    NODOS_PRUEBA = ["INTC", "TSM", "NVDA", "ASML", "AAPL", "MSFT", "AMD", "QCOM"]
    ARISTAS_PRUEBA = [('ASML', 'TSM', {'tipo': 'proveedor_de'}), ('TSM', 'NVDA', {'tipo': 'proveedor_de'})]
    FEEDS_PRUEBA = ["https://www.reuters.com/news/rss/technology"]
    
    mi_atlas_prueba = AtlasEconomico(NODOS_PRUEBA, ARISTAS_PRUEBA)
    scores = obtener_live_gscores(mi_atlas_prueba, NODOS_PRUEBA, FEEDS_PRUEBA)
    
    print("\n--- [Capa 1] Resultado de la Prueba ---")
    print("GScores Finales:")
    print(scores)
    print("\nNuevas Aristas (si las hubiera):")
    print(list(mi_atlas_prueba.G.edges(data=True)))