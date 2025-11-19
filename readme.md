# NEXUS QUANTUM LAYER - Quantum Swaption Forecaster con Quantum Reservoir Computer 
## ¿Qué es?
Es un sistema que usa el algoritmo de Quantum Reservoir Computer para predecir precios de swaptions. Piensen en él como un cerebro cuántico que memoriza patrones de 224 dimensiones simultáneamente (similar a un cubo OLAP).
## ¿Por qué es REALMENTE cuántico?
### Espacio de Hilbert Exponencial
- Con 6 qubits: 2^6 = 64 dimensiones de procesamiento.
- Un LSTM clásico necesitaría 64 neuronas para igualar esto.
- Ventaja: Entanglement = correlaciones no-lineales.
### Reservoir Computing != Algoritmo Cuántico Normal
ES: Un sistema cuántico fijo que actúa como "memoria dinámica" para entrenamiento de la SALIDA (Ridge Regression clásica).
### Respaldo Teórico
- "Quantum Reservoir Computing for Realized Volatility Forecasting" (2023).
- "Impact of the form of weighted networks on quantum extreme reservoir computation" (Physical Review A).
## ¿Qué hace el código?
Input (t): [QUANTUM RESERVOIR: 6 qubits entrelazados] -> Features Cuánticas -> Ridge .Regression: Prediction (t+1).
Pipeline completo:
- Carga datos (500 filas × 224 columnas de Tenor/Maturity)
- Entrena en datos históricos (filas "Complete")
- Imputa valores faltantes (filas con algunos NAs)
- Forecasts 2 semanas (filas "Future prediction")
## Instalación 
bashpip install qiskit qiskit-aer scikit-learn pandas numpy --break-system-packages
Advertencia: Si dan error de "externally-managed-environment":
bashpip install --user qiskit qiskit-aer scikit-learn pandas numpy
## Uso
bashpython nexus_layer2_quantum_swaptions.py sample_Swaption_Price_data_sample.csv
Salida: nexus_predictions.csv con todas las predicciones.
