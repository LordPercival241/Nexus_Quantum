import numpy as np
import time
# ============================================================================
# TEST 1: Imports básicos
# ============================================================================
print("Test 1: Verificando imports...")
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from sklearn.linear_model import Ridge
    import pandas as pd
    print("OKi")
except ImportError as e:
    print(f"Error en imports: {e}")
    print("Ejecuta: pip install qiskit qiskit-aer scikit-learn pandas --break-system-packages")
    exit(1)

print()

# ============================================================================
# TEST 2: Quantum Reservoir básico
# ============================================================================
print("Test 2: Inicializando Quantum Reservoir...")
try:
    from nexus_layer2_quantum_swaptions import QuantumReservoir
    
    reservoir = QuantumReservoir(n_qubits=4, entanglement_depth=1)
    print("Quantum Reservoir creado")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

print()

# ============================================================================
# TEST 3: Transform single input
# ============================================================================
print("Test 3: Probando transformación cuántica de un input...")
try:
    test_input = np.random.randn(224)  # Vector de 224 features
    
    start = time.time()
    quantum_features = reservoir.transform_single(test_input)
    elapsed = time.time() - start
    
    print(f"Input shape: {test_input.shape}")
    print(f"Quantum features shape: {quantum_features.shape}")
    print(f"Tiempo: {elapsed:.3f} segundos")
    print(f"Dimensión cuántica: {len(quantum_features)} (de 2^4 = 16 dimensiones)")
    
    if len(quantum_features) == 12:  # 4 qubits × 3 mediciones (X,Y,Z)
        print("Transformación correcta")
    else:
        print(f"Features inesperadas: {len(quantum_features)} (esperaba 12)")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()

# ============================================================================
# TEST 4: Visualizar circuito
# ============================================================================
print("Test 4: Generando visualización del circuito cuántico...")
try:
    qc = reservoir._build_circuit()
    print()
    print("Circuito cuántico:")
    print("   " + "-"*60)
    circuit_str = str(qc.draw(output='text'))
    for line in circuit_str.split('\n'):
        print(f"   {line}")
    print("   " + "-"*60)
    print("Circuito generado")
except Exception as e:
    print(f"Error: {e}")

print()

# ============================================================================
# TEST 5: Batch processing
# ============================================================================
print("Test 5: Probando procesamiento de batch (10 samples)...")
try:
    X_batch = np.random.randn(10, 224)
    
    start = time.time()
    quantum_batch = reservoir.transform_batch(X_batch)
    elapsed = time.time() - start
    
    print(f"Input shape: {X_batch.shape}")
    print(f"Output shape: {quantum_batch.shape}")
    print(f"Tiempo total: {elapsed:.2f} segundos ({elapsed/10:.2f} s/sample)")
    
    if quantum_batch.shape == (10, 12):
        print("Batch processing OK")
    else:
        print(f"Shape inesperado: {quantum_batch.shape}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# TEST 6: Full QRC Model (mini training)
# ============================================================================
print("Test 6: Entrenando modelo QRC")
try:
    from nexus_layer2_quantum_swaptions import QRCSwaptionForecaster
    
    # Crear datos sintéticos
    X_train = np.random.randn(20, 224) * 0.1
    y_train = X_train + np.random.randn(20, 224) * 0.01  # Correlación simple
    
    model = QRCSwaptionForecaster(n_qubits=4, entanglement_depth=1, alpha=1.0)
    
    start = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - start
    
    print(f"Tiempo de training: {elapsed:.2f} segundos")
    
    # Test prediction
    X_test = np.random.randn(5, 224) * 0.1
    predictions = model.predict(X_test)
    
    print(f"Predictions shape: {predictions.shape}")
    
    if predictions.shape == (5, 224):
        print("Modelo QRC funcional")
    else:
        print(f"Shape inesperado: {predictions.shape}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# RESULTADO FINAL
# ============================================================================
print("="*70)
print("TESTS COMPLETADOS")
print()
print("Siguiente paso:")
print("1. Ejecuta con el dataset real:")
print("python3 nexus_layer2_quantum_swaptions.py <tu_archivo.csv>")

# Performance summary
print("Performance Summary:")
print(f"- Single transform: ~{elapsed/10:.2f}s (esperado: 0.1-0.3s)")
print(f"- Mini training (20 samples): ~{elapsed:.1f}s")
print(f"- Estimado para 500 samples: ~{elapsed * 25:.1f}s ({elapsed * 25 / 60:.1f} min)")
print()