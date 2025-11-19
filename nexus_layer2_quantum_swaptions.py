import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.circuit import Parameter
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# MÓDULO 1: QUANTUM RESERVOIR 6 qubits
# 1.- Encoding de inputs (RY)
# 2.- Capa de enlazamiento (CZ)
# 3.- Capa de evolucion (RZ)
# ============================================================================

class QuantumReservoir:
    
    def __init__(self, n_qubits=6, entanglement_depth=2):
        self.n_qubits = n_qubits
        self.entanglement_depth = entanglement_depth
        self.backend = AerSimulator(method='statevector')
        
        # Parámetros 
        self.theta_params = [Parameter(f'θ_{i}') for i in range(n_qubits)]
        self.phi_params = [Parameter(f'φ_{i}') for i in range(n_qubits)]
        
        print(f"Quantum Reservoir de: {n_qubits} qubits, entanglement depth={entanglement_depth}")
        print(f"Dimensión del espacio de Hilbert: 2^{n_qubits} = {2**n_qubits}")
    
    def _build_circuit(self):
        qc = QuantumCircuit(self.n_qubits)
        # 1. Encoding de inputs (RY)
        for i in range(self.n_qubits):
            qc.ry(self.theta_params[i], i)
        
        qc.barrier()
        
        # 2. ENTANGLEMENT LAYER 
        for depth in range(self.entanglement_depth):
            # CZ gates
            for i in range(self.n_qubits - 1):
                qc.cz(i, i + 1)
            qc.cz(self.n_qubits - 1, 0)  
            
            # Rotaciones intermedias para romper simetría
            for i in range(self.n_qubits):
                qc.rz(self.phi_params[i], i)
        
        qc.barrier()
        
        # 3. FINAL MIXING (RX gates)
        for i in range(self.n_qubits):
            qc.rx(np.pi / 4, i)
        
        return qc
    
    def transform_single(self, input_vector): #Vector de 224 features a espacio cuántico
        # NORMALIZACIÓN: mapear input a rango [-π, π]
        normalized = np.tanh(input_vector[:self.n_qubits])  # Tomar solo primeros n_qubits
        theta_values = normalized * np.pi
        phi_values = normalized * np.pi / 2  # Diferentes escalas para theta y phi
        
        # Construir circuito y asignar parámetros
        qc = self._build_circuit()
        param_dict = {}
        for i in range(self.n_qubits):
            param_dict[self.theta_params[i]] = theta_values[i]
            param_dict[self.phi_params[i]] = phi_values[i]
        
        qc_bound = qc.assign_parameters(param_dict)
        
        # Ejecutar y obtener statevector
        qc_bound.save_statevector()
        job = self.backend.run(transpile(qc_bound, self.backend), shots=1)
        result = job.result()
        statevector = result.get_statevector()
        
        # READOUT: Extraer expectation values <Pauli>
        features = []
        for i in range(self.n_qubits):
            # Calcular <X>, <Y>, <Z> para cada qubit
            features.extend([
                self._measure_pauli_x(statevector, i),
                self._measure_pauli_y(statevector, i),
                self._measure_pauli_z(statevector, i)
            ])
        
        return np.array(features)
    
    def _measure_pauli_x(self, state, qubit_idx):
        n = self.n_qubits
        expval = 0.0
        for i in range(2**n):
            j = i ^ (1 << qubit_idx)  # Flip bit en posición qubit_idx
            expval += np.real(np.conj(state[i]) * state[j])
        return expval
    
    def _measure_pauli_y(self, state, qubit_idx):
        return self #??
    
    def _measure_pauli_z(self, state, qubit_idx):
        return self #??
    
    # def transform_batch(self, X_matrix):