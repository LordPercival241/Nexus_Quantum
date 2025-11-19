#!/bin/bash
# ==============================================================================
# NEXUS QUANTUM SETUP SCRIPT
# Qiskit Fall Fest Lima 2025 - Track 2
# ==============================================================================

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
else
    OS="Unknown"
fi

echo "Sistema detectado: $OS"
echo ""
install_pip_packages() {
    echo "Instalando dependencias de Python..."
    echo ""
    
    # Intentar instalación normal primero
    pip install qiskit qiskit-aer scikit-learn pandas numpy matplotlib networkx feedparser google-generativeai --break-system-packages 2>/dev/null
    
    # Si falla, intentar con --user
    if [ $? -ne 0 ]; then
        echo "Instalación con --break-system-packages falló. Intentando con --user..."
        pip install --user qiskit qiskit-aer scikit-learn pandas numpy matplotlib networkx feedparser google-generativeai
    fi
    
    echo ""
}

# Instalación principal
install_pip_packages

# Verificar instalación
echo "Verificando instalación..."
echo ""

python3 << 'PYEOF'
import sys

packages = {
    'qiskit': 'Qiskit',
    'qiskit_aer': 'Qiskit Aer',
    'sklearn': 'scikit-learn',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'matplotlib': 'Matplotlib',
    'networkx': 'NetworkX',
    'feedparser': 'FeedParser',
    'google.generativeai': 'Google Generative AI'
}

all_ok = True
for module, name in packages.items():
    try:
        __import__(module)
        print(f"{name} instalado correctamente")
    except ImportError:
        print(f"{name} NO instalado")
        all_ok = False

if all_ok:
    print("\n¡Todas las dependencias están listas!")
    sys.exit(0)
else:
    print("\nAlgunas dependencias faltan. Revisa los errores arriba.")
    sys.exit(1)
PYEOF

# Guardar código de salida
VERIFICATION_STATUS=$?

echo ""
echo "========================================================================"

if [ $VERIFICATION_STATUS -eq 0 ]; then
    echo " INSTALACIÓN COMPLETA"
    echo "  Puedes ejecutar los layers con:"
    echo ""
    echo "  # Layer 1 (Grafo de Noticias):"
    echo "  python nexus_layer1.py"
    echo ""
    echo "  # Layer 2 (Quantum Swaption Forecasting):"
    echo "  python nexus_layer2_quantum_swaptions.py <archivo.csv>"
    echo ""
    echo "  # Test rápido del Quantum Reservoir:"
    echo "  python3 test_quantum_reservoir.py"
else
    echo "  INSTALACIÓN INCOMPLETA"
    echo "  Por favor, revisa los errores e intenta instalar manualmente:"
    echo "  pip install --user qiskit qiskit-aer scikit-learn pandas numpy"
fi

echo "========================================================================"
echo ""