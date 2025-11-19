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
        n = self.n_qubits
        expval = 0.0
        for i in range(2**n):
            j = i ^ (1 << qubit_idx)
            bit_val = (i >> qubit_idx) & 1
            sign = 1 if bit_val == 0 else -1
            expval += sign * np.imag(np.conj(state[i]) * state[j])
        return expval
    
    def _measure_pauli_z(self, state, qubit_idx):
        n = self.n_qubits
        expval = 0.0
        for i in range(2**n):
            bit_val = (i >> qubit_idx) & 1
            sign = 1 if bit_val == 0 else -1
            expval += sign * np.abs(state[i])**2
        return expval
    
    # 224 features a 18 features cuánticas
    def transform_batch(self, X_matrix):
        print(f" Procesando {len(X_matrix)} samples por el reservoir cuántico...")
        features_list = []
        for i, x in enumerate(X_matrix):
            if i % 50 == 0:
                print(f"      Sample {i}/{len(X_matrix)}", end='\r')
            features_list.append(self.transform_single(x))
        print()  
        return np.array(features_list)
    
# ============================================================================
# MÓDULO 2: QRC FORECASTER (Precios de Swaptions)
# 1. QR transforma inputs al espacio de Hilbert
# 2. Ridge Regression en features cuánticas
# ============================================================================
class QRCSwaptionForecaster:
    
    def __init__(self, n_qubits=6, entanglement_depth=2, alpha=1.0):
        self.reservoir = QuantumReservoir(n_qubits, entanglement_depth)
        self.readout = Ridge(alpha=alpha)
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        
        print(f"QRC Forecaster listo par entrenar")
        print(f"Regularización Ridge: α={alpha}")
    
    #Entrenamiento del modelo con Features históricas (x) y targets (features un paso adelante)
    def fit(self, X_train, y_train):
        print("\n Iniciando entrenamiento")
        
        # 1. Normalizar inputs
        X_scaled = self.scaler_X.fit_transform(X_train)
        y_scaled = self.scaler_y.fit_transform(y_train)
        
        # 2. Quantum Reservoir Transform
        X_quantum = self.reservoir.transform_batch(X_scaled)
        
        # 3. Entrenar capa de readout (Ridge Regression)
        print("Entrenando capa de readout clásica...")
        self.readout.fit(X_quantum, y_scaled)
        
        # Calcular error de training
        y_pred_scaled = self.readout.predict(X_quantum)
        y_pred = self.scaler_y.inverse_transform(y_pred_scaled)
        mse = mean_squared_error(y_train, y_pred)
        mae = mean_absolute_error(y_train, y_pred)
        
        print(f"Training completado - MSE: {mse:.6f}, MAE: {mae:.6f}")
        return self
    
    # Predicción de valores 
    def predict(self, X_test):
        X_scaled = self.scaler_X.transform(X_test)
        X_quantum = self.reservoir.transform_batch(X_scaled)
        y_pred_scaled = self.readout.predict(X_quantum)
        return self.scaler_y.inverse_transform(y_pred_scaled)

# ============================================================================
# MÓDULO 3: DATA PIPELINE
# Carga de CSV dado y preparación de data para Q Reservoir
# ============================================================================

def load_and_prepare_data(filepath):
    print("\n[Data] Cargando dataset...")
    df = pd.read_csv(filepath)
    
    # Separar columnas de features vs metadata
    feature_cols = [col for col in df.columns if 'Tenor' in col]
    n_features = len(feature_cols)
    print(f"   Features encontradas: {n_features}")
    
    # Identificar filas completas, con valores faltantes, y futuras
    complete_rows = []
    missing_rows = []
    future_rows = []
    
    for idx, row in df.iterrows():
        if 'Date' in df.columns:
            row_type = row.get('Type', 'Complete')  # En sample hay columna Type
        else:
            row_type = 'Complete'  # En dataset final no hay Type
        
        # Checar si tiene NAs
        has_na = row[feature_cols].isna().any()
        all_na = row[feature_cols].isna().all()
        
        if all_na:
            future_rows.append(idx)
        elif has_na:
            missing_rows.append(idx)
        else:
            complete_rows.append(idx)
    
    print(f"Filas completas: {len(complete_rows)}")
    print(f"Filas con valores faltantes: {len(missing_rows)}")
    print(f"Filas futuras (all NA): {len(future_rows)}")
    
    # Preparar X_train, y_train (usando filas completas)
    # Estrategia: usar fila t para predecir fila t+1
    X_train = []
    y_train = []
    
    for i in range(len(complete_rows) - 1):
        idx_current = complete_rows[i]
        idx_next = complete_rows[i + 1]
        
        X_train.append(df.loc[idx_current, feature_cols].values.astype(float))
        y_train.append(df.loc[idx_next, feature_cols].values.astype(float))
    
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    
    # Preparar X_missing (filas con algunos valores para imputar)
    X_missing = []
    for idx in missing_rows:
        row_vals = df.loc[idx, feature_cols].values
        # Reemplazar NAs con 0 temporalmente
        row_vals = np.where(pd.isna(row_vals), 0, row_vals).astype(float)
        X_missing.append(row_vals)
    X_missing = np.array(X_missing) if len(X_missing) > 0 else None
    
    # Preparar X_future (usar última fila completa como seed)
    if len(future_rows) > 0:
        last_complete = df.loc[complete_rows[-1], feature_cols].values.astype(float)
        X_future = np.tile(last_complete, (len(future_rows), 1))
        dates_future = df.loc[future_rows, 'Date'].values if 'Date' in df.columns else None
    else:
        X_future = None
        dates_future = None
    
    return X_train, y_train, X_missing, missing_rows, X_future, dates_future, feature_cols

# Guardar predicciones en el dataframe
def save_predictions(df, predictions, indices, feature_cols, output_path):
    df_output = df.copy()
    for i, idx in enumerate(indices):
        df_output.loc[idx, feature_cols] = predictions[i]
    df_output.to_csv(output_path, index=False)
    print(f"Predicciones guardadas en: {output_path}")

# ============================================================================
# MÓDULO 4: MAIN 
# Cargar, Entrenar QR en data historica, predecir, forecast a 2 semanas, guardar
# ============================================================================

def train_and_predict_qrc(data_path, output_path='nexus_predictions.csv'):
    print("="*70)
    print("QUANTUM SWAPTION FORECASTER")
    print("Qiskit Fall Fest Lima 2025 - Track 2")
    print("="*70)
    
    # 1. CARGAR DATOS
    X_train, y_train, X_missing, idx_missing, X_future, dates_future, feature_cols = \
        load_and_prepare_data(data_path)
    
    # 2. ENTRENAR MODELO
    model = QRCSwaptionForecaster(
        n_qubits=6, 
        entanglement_depth=2,
        alpha=1.0  # Regularización Ridge
    )
    model.fit(X_train, y_train)
    
    # 3. PREDECIR VALORES FALTANTES (si existen)
    all_predictions = []
    all_indices = []
    
    if X_missing is not None and len(X_missing) > 0:
        print("\nPrediciendo valores faltantes")
        missing_pred = model.predict(X_missing)
        all_predictions.append(missing_pred)
        all_indices.extend(idx_missing)
    
    # 4. FORECAST FUTURO (2 semanas)
    if X_future is not None: # Forecast
        print("\nPrediciendo 2 semanas hacia el futuro...")
        
        # Forecasting iterativo: usar predicción anterior como input
        future_predictions = []
        current_state = X_future[0:1]  # Última observación como seed
        
        for i in range(len(X_future)):
            pred = model.predict(current_state)
            future_predictions.append(pred[0])
            current_state = pred  # Feed prediction como next input
            
            if dates_future is not None:
                print(f"Día {i+1} ({dates_future[i]}): predicción completa")
        
        future_predictions = np.array(future_predictions)
        all_predictions.append(future_predictions)
        all_indices.extend([i for i in range(len(dates_future))])  # Indices relativos
    
    # 5. GUARDAR RESULTADOS
    print("\nGuardando predicciones finales...")
    try:
        # Cargar DF original 
        df_original = pd.read_csv(data_path, index_col='Date', parse_dates=True) 
        df_final = df_original.copy()
        print(f" DF Original cargado con shape: {df_final.shape}")

    except Exception as e:
        print(f" ERROR: No se pudo cargar el DF original para actualizar: {e}")
        # Si falla se usa método simple de guardar solo las predicciones:
        if len(all_predictions) > 0:
            all_pred_array = np.vstack(all_predictions)
            pred_df = pd.DataFrame(all_pred_array, columns=feature_cols)
            pred_df.to_csv(output_path, index=False)
            print(f"Guardado de emergencia: {output_path}")
        return model, None
    
    # 5b. IMPUTAR VALORES FALTANTES (Missing)
    if X_missing is not None and len(X_missing) > 0:
        print(" 1. Imputando valores faltantes en el DF original...")
        # .loc para actualizar las filas y columnas correspondientes
        for i, idx in enumerate(idx_missing):
            df_final.loc[df_final.index[idx], feature_cols] = missing_pred[i]
        
    # 5c. AÑADIR EL FORECAST FUTURO
    if X_future is not None and len(future_predictions) > 0:
        print(" 2. Añadiendo el forecast de 2 semanas al final del DF...")
        
        # Crear un DF temporal para las predicciones futuras con sus fechas
        future_df = pd.DataFrame(
            future_predictions, 
            index=dates_future, 
            columns=feature_cols
        )
        # Asegurarse de que el índice se llame 'Date'
        future_df.index.name = 'Date' 

        # Concatenar el DF histórico con el DF futuro
        df_final = pd.concat([df_final, future_df])

    # 5d. GUARDAR EL RESULTADO FINAL CONTEXTUALIZADO
    print(f"Total de filas en el DF final (Histórico + Forecast): {df_final.shape[0]}")
    df_final.to_csv(output_path, index=True) # index=True para guardar la columna 'Date'
    print(f"Archivo final guardado: {output_path}")

    return model, df_final