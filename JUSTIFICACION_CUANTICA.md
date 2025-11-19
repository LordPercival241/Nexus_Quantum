# "¿Por qué Quantum?"
Los precios de swaptions dependen de 224 combinaciones de Tenor × Maturity con correlaciones no-lineales complejas. Un Quantum Reservoir Computer (QRC) explota el espacio de Hilbert exponencial (2^n dimensiones) para **capturar estas dependencias con menos parámetros entrenables que modelos clásicos**, evitando overfitting en datos financieros ruidosos.

## Fundamentos Teóricos
### ¿Qué es Reservoir Computing?
Reservoir Computing (RC) es un paradigma de machine learning donde:
- Un sistema dinámico no-lineal fijo (el "reservoir") actúa como proyector de alta dimensión
- Solo se entrena una capa de salida lineal (Ridge Regression). Evita el problema del vanishing/exploding gradient de RNNs tradicionales.
### ¿Por qué hacerlo cuántico?
#### Ventaja 1: Dimensionalidad Exponencial
Clásico: Un reservoir de N neuronas tiene N dimensiones
Cuántico: Un reservoir de N qubits tiene 2^N dimensiones
Con 6 qubits:
Espacio de Hilbert = 2^6 = 64 dimensiones
Un LSTM clásico necesitaría 64 neuronas ocultas para igualar esta capacidad.
#### Ventaja 2: Entanglement = Correlaciones No-Lineales Gratis
El entanglement cuántico permite capturar correlaciones de alto orden entre variables sin costo computacional adicional:
|ψ⟩ = α|00⟩ + β|11⟩  (estado entrelazado)
En finanzas, esto significa que el modelo puede detectar:
- Correlaciones entre múltiples tenores simultáneamente
- Dependencias temporales complejas
- Regímenes de mercado no-lineales
#### Ventaja 3: Menos Parámetros Entrenables
QRC Solo entrena la capa de readout (224 outputs × 18 quantum features = 4,032 parámetros)
LSTM clásico:
Parámetros = 4 × hidden_size × (input_size + hidden_size + 1)
Para hidden_size=64, input_size=224:
= 4 × 64 × (224 + 64 + 1) = 73,984 parámetros
Menos parámetros = Menos riesgo de overfitting en datasets financieros pequeños (~500 samples).
### Papers de Respaldo
"Quantum Reservoir Computing for Realized Volatility Forecasting" de Fujii & Nakagawa (2023) demuestra que QRC supera a LSTMs en predicción de volatilidad realizada.
#### Paper de Arquitectura:
"Impact of the form of weighted networks on quantum extreme reservoir computation" de Physical Review A (2024) analiza el impacto de diferentes topologías de entanglement.
Conclusión: Redes circulares (como la nuestra) son óptimas para series temporales
#### Referencias de IBM:
IBM Quantum Learning: "Quantum Machine Learning Fundamentals"
Hybrid Quantum-Classical Models (Merlin Framework)

## Detalles de Implementación
### Arquitectura del Circuito Cuántico:
Input Layer:    RY(θ₀) RY(θ₁) ... RY(θ₅)
                  |      |           |
Entanglement:    ●──────┼───────────┼
                 │      ●───────────┼
                 │      │           ●
                 └──────┴───────────┘
Evolution:      RZ(φ₀) RZ(φ₁) ... RZ(φ₅)
                  |      |           |
(Repetir depth veces)
                  |      |           |
Readout:        ⟨X⟩    ⟨Y⟩         ⟨Z⟩
Encoding de Input:

Los 224 features se normalizan a [-1, 1]
Se mapean a ángulos: θᵢ = tanh(xᵢ) × π
Solo los primeros 6 features se usan directamente (el resto influye vía la capa de salida)
### Medición (Readout):
Se calcula el expectation value de operadores de Pauli (X, Y, Z) en cada qubit
Total: 6 qubits × 3 operadores = 18 features cuánticas
#### Ventaja sobre VQE/QAOA:
- VQE/QAOA requieren optimización cuántica (costosa)
- QRC usa el circuito cuántico como feature extractor fijo (barato)
## ¿Por qué NO usar...?
### ¿Por qué NO VQE (Variational Quantum Eigensolver)?
- VQE es para problemas de optimización (encontrar ground state)
- Requiere entrenar el circuito cuántico (costoso, 100s de iteraciones)
- QRC entrena solo la salida (1 iteración)
### ¿Por qué NO QAOA (Quantum Approximate Optimization Algorithm)?
- QAOA es para problemas combinatoriales (TSP, Max-Cut)
- No está diseñado para series temporales
- QRC está específicamente validado para forecasting financiero
### ¿Por qué NO Quantum Neural Networks (QNN)?
- QNNs son "black boxes" (difícil interpretar)
- Sufren de barren plateaus (gradientes desaparecen)
- QRC evita este problema al no entrenar el circuito cuántico

## Escalabilidad y Limitaciones
### Hardware Cuántico Real:
- Simulador: Usamos Qiskit Aer 
- Hardware real: Podría ejecutarse en IBM Quantum (127 qubits disponibles)
- Ventaja: El algoritmo es NISQ-friendly (pocos qubits, pocas gates)
### Limitaciones Actuales:
- Velocidad: Simulación clásica es lenta (pero en hardware real sería más rápido)
- Qubits: 6 qubits es conservador (podríamos usar 10-12 en hardware real)
- Noise: No consideramos ruido cuántico (habría que usar técnicas de mitigación)

## Otras preguntas
### ¿Por qué no usar más qubits?
6 qubits es un balance entre expresividad (2^6 = 64 dims) y viabilidad computacional. Más qubits = simulación exponencialmente más lenta. En hardware cuántico real, podríamos escalar a 10-12 qubits.
### ¿Cómo sabemos que el quantum advantage es real?"
El quantum advantage aquí NO es velocidad (eso requiere hardware real). Es expresividad: capturamos correlaciones de 224 variables en 18 features usando entanglement. Un modelo clásico necesitaría una red más profunda con más parámetros, arriesgando overfitting.

## Referencias Adicionales

IBM Quantum Learning: https://learning.quantum.ibm.com/
Qiskit Textbook - Quantum ML: https://qiskit.org/learn/intro-qml
Physical Review A - Quantum Reservoir Computing: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.108.042609 
Fujii et al. - QRC for Volatility: https://www.researchgate.net/publication/391910873_Quantum_Reservoir_Computing_for_Realized_Volatility_Forecasting


Última actualización: Noviembre 19, 2025
Equipo: Nexus Quantum - Qiskit Fall Fest Lima