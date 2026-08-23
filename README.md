

## 🏗️ Arquitectura de FlowFi

```mermaid
flowchart TD
    subgraph "1. Experiencia de Usuario (FlowFi Frontend)"
        A[Usuario: 0.00 ETH | 50.00 USDt] --> B[WDK Gasless Service: @tetherto/wdk-wallet-evm-erc-4337]
        B --> C[Cotizador: Estimar Tarifa en USDt]
        C --> D[Empaquetar UserOp: Approve USDt + Deposit FlowFiVault]
    end

    subgraph "2. Infraestructura Tether WDK Gasless (Pista 2)"
        D --> E[Pimlico Bundler RPC en Arbitrum Sepolia 421614]
        E --> F[Paymaster Contract: Liquidación de Gas en USDt / Patrocinio]
        F --> G[EntryPoint 0.7 Contract]
    end

    subgraph "3. Smart Contracts On-Chain"
        G --> H[GasslessPilotVault.sol ERC-4626]
        H --> I[Aave V3 Pool: Supply / Withdraw]
    end

    subgraph "4.Optimización IA (Backend)"
        J[Datos Aave V3] --> K[Gemini LLM: Análisis de Rendimiento]
        K --> L[Signer EIP-712: Firma Criptográfica]
        L --> H
    end
```

---
## 📦 Paquetes de Tether WDK Instalados

```json
{
  "dependencies": {
    "@tetherto/wdk": "^1.0.0-beta.16",
    "@tetherto/wdk-wallet-evm-erc-4337": "^1.0.0-beta.16",
    "viem": "^2.55.19",
    "ethers": "^6.11.1"
  }
}
```

---

## 🚀 Guía de Inicio Rápido (Setup desde cero)

### Prerrequisitos
* Node.js >= 22.18.0
* Python 3.10+

### 1. Clonar e Instalar Frontend
```bash
cd client
npm install
cp .env.example .env
npm run dev
```

### 2. Variables de Entorno del Cliente (`client/.env`)
```env
VITE_PIMLICO_RPC_URL=https://api.pimlico.io/v2/421614/rpc?apikey=TU_PIMLICO_API_KEY
VITE_VAULT_CONTRACT_ADDRESS=0x9b24ADD6fe458f1d620A17ceC8d20944C37296d7
VITE_USDC_CONTRACT_ADDRESS=0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d
VITE_CHAIN_ID=421614
VITE_API_URL=http://localhost:8000
```

### 3. Ejecutar Backend de IA
```bash
cd server
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

---

## 👥 Equipo y Roles

* **Jesús Alfaro:** Smart Contracts (ERC-4626, Aave V3, EIP-712 Verification & Foundry Tests en Arbitrum Sepolia).
* **Dante Olivas:** Integración Tether WDK Gasless (ERC-4337 & Pimlico Paymaster), Frontend React, Backend FastAPI con Gemini LLM y Arquitectura de Producto.
