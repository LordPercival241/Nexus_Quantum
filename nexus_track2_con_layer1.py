# Layer 1 lee noticias -> g_scores -> "stress index" (0 a 1)
# QRC predice swaptions con 6 qubits → predicciones base
# Ajustamos predicciones según el estrés del mercado
# Estrés alto → Tasas de interés cambian → Swaptions suben
# Estrés bajo → Mercado estable → Predicciones sin ajuste

import numpy as np
import pandas as pd
from datetime import datetime

# Importar capas
try:
    from nexus_layer1 import obtener_live_gscores, AtlasEconomico
    from nexus_layer2_quantum_swaptions import QRCSwaptionForecaster, load_and_prepare_data
    LAYERS_OK = True
except ImportError as e:
    print(f"Error: {e}")
    LAYERS_OK = False


def conectar_layer1_con_track2(swaption_csv_path, usar_bancos=False):
    
    # =========================================================================
    # LAYER 1 - Analizar noticias y calcular estrés del mercado
    # =========================================================================
    
    print("Analizando noticias (Layer 1)...")
    print()
    
    if usar_bancos:
        # Analizar bancos 
        entidades = ["JPM", "GS", "MS", "BAC", "C", "WFC"]
        aristas = [('JPM', 'GS', {'tipo': 'competidor_de'})]
        feeds = ["https://www.reuters.com/news/rss/business"]
        print("Monitoreando: Bancos (JPM, GS, MS, BAC, C, WFC)")
    else:
        # Analizar tech 
        entidades = ["INTC", "TSM", "NVDA", "ASML", "AAPL", "MSFT"]
        aristas = [('TSM', 'NVDA', {'tipo': 'proveedor_de'})]
        feeds = ["https://www.reuters.com/news/rss/technology"]
        print("   Monitoreando: Tech (INTC, TSM, NVDA, ASML, AAPL, MSFT)")
    
    print()
    
    try:
        # Crear el grafo y obtener g_scores
        atlas = AtlasEconomico(entidades, aristas)
        g_scores = obtener_live_gscores(atlas, entidades, feeds)
        
        # Calcular el "stress index" (0 a 1)
        if len(g_scores) > 0:
            riesgo_total = sum(g_scores.values())
            # Normalizar (asumiendo max 2.0 por entidad)
            stress_index = min(1.0, riesgo_total / (len(g_scores) * 2.0))
        else:
            stress_index = 0.0
        
        print(f"G-Scores obtenidos:")
        for entidad, score in g_scores.items():
            if score > 0:
                print(f"{entidad}: {score:.3f}")
        
        print()
        print(f"STRESS INDEX DEL MERCADO: {stress_index:.3f} / 1.0")
        
        if stress_index < 0.3:
            print(f"Mercado estable :D")
        elif stress_index < 0.7:
            print(f"Mercado con estres moderado :/")
        else:
            print(f"Mercado con alto estreS (crisis potencial) :( ")
        
    except Exception as e:
        print(f"Error en Layer 1: {e}")
        print(f"stress_index = 0.0 (neutral)")
        stress_index = 0.0
        g_scores = {}
    
    print()
    
    # =========================================================================
    # TRACK 2 - Predecir swaptions con QRC
    # =========================================================================
    
    print(" Prediciendo swaptions con QRC (6 qubits)...")
    print()
    
    # Cargar datos
    print("Cargando CSV de swaptions...")
    X_train, y_train, X_missing, idx_missing, X_future, dates_future, feature_cols = \
        load_and_prepare_data(swaption_csv_path)
    
    print(f" {len(X_train)} muestras de entrenamiento")
    print()
    
    # Entrenar el modelo cuántico
    print("Entrenando Quantum Reservoir Computer...")
    modelo_qrc = QRCSwaptionForecaster(
        n_qubits=6,
        entanglement_depth=2,
        alpha=1.0
    )
    modelo_qrc.fit(X_train, y_train)
    
    print()
    
    # Hacer predicciones BASE (sin ajuste)
    if X_future is not None and len(X_future) > 0:
        print("Generando predicciones BASE...")
        predicciones_base = modelo_qrc.predict(X_future)
        print(f"{len(predicciones_base)} días predichos")
    else:
        print("No hay datos futuros en el CSV")
        return None
    
    print()

    # =========================================================================
    # INTEGRACIÓN - Ajustar por contexto de mercado
    # =========================================================================
    
    print("Ajustando predicciones por contexto de mercado...")
    print()
    
    # Fórmula de integración:
    # PrecioFinal = PrecioQRC × (1 + FactorAjuste)
    # Donde FactorAjuste = g_score × sensibilidad
    
    SENSIBILIDAD = 0.20  # Máximo impacto: crisis total (+100% stress) → precios suben 20%
    
    factor_ajuste_puro = stress_index * SENSIBILIDAD
    factor_multiplicador = 1.0 + factor_ajuste_puro
    
    predicciones_finales = predicciones_base * factor_multiplicador
    
    print(f"Fórmula: PrecioFinal = PrecioQRC × (1 + stress × {SENSIBILIDAD})")
    print(f"Stress index: {stress_index:.3f}")
    print(f"Factor ajuste puro: {factor_ajuste_puro:.4f}")
    print(f"Multiplicador final: {factor_multiplicador:.4f}x")
    print(f"Cambio en precios: {(factor_ajuste_puro * 100):.2f}%")
    
    # Calcular impacto
    diferencia = predicciones_finales - predicciones_base
    impacto_promedio = np.mean(np.abs(diferencia))
    
    print(f"Impacto promedio absoluto: ±{impacto_promedio:.6f}")
    
    print()
    
    if stress_index > 0.5:
        print("Interpretación: Alto estrés -> Volatilidad implícita SUBE")
        print("-> Precios de swaptions ajustados AL ALZA")
    elif stress_index > 0.3:
        print("Interpretación: Estrés moderado -> Ajuste conservador")
    else:
        print("Interpretación: Mercado estable -> Sin ajuste significativo")
    
    print()
    
    # =========================================================================
    # PASO 4: GUARDAR RESULTADOS
    # =========================================================================
    
    print("PASO 4: Guardando resultados...")
    print()
    
    # Crear DataFrame
    df_predicciones = pd.DataFrame(predicciones_finales, columns=feature_cols)
    
    # Agregar metadata
    if dates_future is not None:
        df_predicciones.insert(0, 'Date', dates_future)
    
    df_predicciones.insert(0, 'Market_Stress', stress_index)
    df_predicciones.insert(0, 'Multiplicador', factor_multiplicador)
    
    # Guardar
    output_file = 'nexus_predicciones_con_contexto.csv'
    df_predicciones.to_csv(output_file, index=False)
    
    print(f"Archivo guardado: {output_file}")
    print()
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("RESUMEN ")
    print()
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    print(f"Contexto de Mercado (Layer 1):")
    print(f"Stress Index: {stress_index:.3f} / 1.0")
    
    if g_scores:
        print(f"Top riesgos:")
        sorted_risks = sorted(g_scores.items(), key=lambda x: x[1], reverse=True)
        for ent, sc in sorted_risks[:3]:
            print(f"   - {ent}: {sc:.3f}")
    
    print()
    print(f"Predicciones Cuánticas (Track 2 QRC):")
    print(f"Días predichos: {len(predicciones_finales)}")
    print(f"Features por día: {len(feature_cols)}")
    print(f"Multiplicador aplicado: {factor_multiplicador:.4f}x")
    print(f"Sensibilidad usada: {SENSIBILIDAD} ({SENSIBILIDAD*100:.0f}%)")
    
    print()
    print(f"Output: {output_file}")
    print()
    print("="*70)
    
    return {
        'stress_index': stress_index,
        'g_scores': g_scores,
        'predicciones_base': predicciones_base,
        'predicciones_finales': predicciones_finales,
        'factor_multiplicador': factor_multiplicador,
        'sensibilidad': SENSIBILIDAD,
        'impacto_promedio': impacto_promedio
    }


# ==============================================================================
# MAIN - EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if not LAYERS_OK:
        print("No se pudieron importar los layers")
        print("Verifica que tengas:")
        print("  - nexus_layer1.py")
        print("  - nexus_layer2_quantum_swaptions.py")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Error: Falta el archivo CSV")
        print()
        print("Uso:")
        print("  python nexus_track2_con_layer1.py <archivo_swaptions.csv>")
        print()
        print("Opciones:")
        print("--bancos Analiza bancos en lugar de tech")
        print()
        print("Ejemplo:")
        print("  python nexus_track2_con_layer1.py Dataset_Simulated_Price.csv")
        print("  python nexus_track2_con_layer1.py Dataset.csv --bancos")
        sys.exit(1)
    
    # Parse argumentos
    archivo_csv = sys.argv[1]
    usar_bancos = '--bancos' in sys.argv
    
    # EJECUTAR TODO
    try:
        resultados = conectar_layer1_con_track2(archivo_csv, usar_bancos)
        
        if resultados:
            print()
            print("¡Sistema ejecutado exitosamente!")
            print()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)