import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import time

# --- integración capa 1
try:
    # Importa la función de "snapshot" de nuestro motor de IA (v6.0)
    # y la clase AtlasEconomico
    from nexus_layer1 import obtener_live_gscores, AtlasEconomico
except ImportError:
    print(" ERROR: No se pudo encontrar 'nexus_layer1.py' (v6.0).")
    print("Asegúrate de que ambos archivos ('nexus_layer1.py' y 'nexus_layer2_optimizer.py') estén en la misma carpeta.")
    exit()
# --- FIN DE LA INTEGRACIÓN ---

warnings.filterwarnings('ignore')

print("NEXUSQUANT ENHANCED v6.0 - MODELO INTEGRADO (Atlas Dinámico + Hechos Quant)")

class EnhancedNexusBacktester:
    """
    Versión 6.0:
    - Integra el 'Córtex de 3 Etapas' (Capa 1).
    - El 'Atlas' (grafo) ahora se actualiza dinámicamente con noticias (Corrige Debilidad 2).
    - El 'GScore' se basa en 'hechos cuantitativos', no en 'sentimiento' (Corrige Debilidad 3).
    """

    # ------------------------------------------------------------------
    # --- __init__ RECONSTRUIDO (v6.0) ---
    # ------------------------------------------------------------------
    def __init__(self):
        # --- Configuración del Backtest ---
        self.universo_nodos = [
            "INTC", "TSM", "NVDA", "ASML", "AAPL", "MSFT", 
            "AMD", "QCOM", "MU", "LRCX", "AMAT"
        ]
        # Este es el grafo "semilla" o inicial.
        # La Capa 1 (LLM 3) añadirá/eliminará aristas a partir de aquí.
        self.universo_aristas = [
            ('ASML', 'TSM',  {'tipo': 'proveedor_de'}),
            ('ASML', 'INTC', {'tipo': 'proveedor_de'}),
            ('ASML', 'MU',   {'tipo': 'proveedor_de'}),
            ('LRCX', 'TSM',  {'tipo': 'proveedor_de'}),
            ('LRCX', 'INTC', {'tipo': 'proveedor_de'}),
            ('AMAT', 'TSM',  {'tipo': 'proveedor_de'}),
            ('TSM',  'NVDA', {'tipo': 'proveedor_de'}),
            ('TSM',  'AAPL', {'tipo': 'proveedor_de'}),
            ('TSM',  'AMD',  {'tipo': 'proveedor_de'}),
            ('TSM',  'QCOM', {'tipo': 'proveedor_de'}),
            ('INTC', 'NVDA', {'tipo': 'competidor_de'}),
            ('INTC', 'AMD',  {'tipo': 'competidor_de'}),
            ('NVDA', 'MSFT', {'tipo': 'proveedor_de'}),
            ('AMD',  'MSFT', {'tipo': 'proveedor_de'}),
        ]
        self.universo_feeds = [
            "https://www.reuters.com/news/rss/technology",
            "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
            "https://www.cnbc.com/id/19854515/device/rss/rss.html",
        ]

        self.benchmark_ticker = 'SOXX'
        self.risk_free_rate = 0.045
        self.transaction_cost = 0.001 
        self.optimization_method = 'mean_variance'
        self.max_weight_per_asset = 0.30 
        self.optimized_weights = self.get_optimized_weight_combinations()
        self.ticker_info_cache = {}
        
        # --- ¡INICIALIZACIÓN DE CAPA 1 y 2! ---
        # 1. Creamos el objeto Atlas "base" aquí en la Capa 2
        print("\n--- [CAPA 2] Creando el Atlas Económico base... ---")
        self.atlas_base = AtlasEconomico(self.universo_nodos, self.universo_aristas)

        # 2. Solicitamos a la Capa 1 que "mejore" nuestro atlas y calcule los riesgos
        print("\n--- [CAPA 2] Solicitando Snapshot (Actualización y Riesgo) a la Capa 1... ---")
        # ¡Le pasamos nuestro objeto atlas_base!
        live_gscores_dict = obtener_live_gscores(
            self.atlas_base, # <--- ¡EL CAMBIO CLAVE! El Atlas ahora es dinámico.
            self.universo_nodos, 
            self.universo_feeds
        )
        
        # 3. Guardamos los GScores (igual que antes)
        self.live_gscore_series = pd.Series(live_gscores_dict).fillna(0.0)
        
        print("\n--- [CAPA 2] GScores en Vivo recibidos: ---")
        non_zero_scores = self.live_gscore_series[self.live_gscore_series != 0]
        if non_zero_scores.empty:
            print(" (No se detectaron riesgos en vivo. Todos los GScores son 0.0)")
        else:
            print(non_zero_scores)
        print("----------------------------------------\n")
    # --- FIN DE LAS MODIFICACIONES ---
    # ---------------------------------

    def set_info_cache(self, info_cache):
        """Pre-carga los datos fundamentales .info"""
        print(f" Caché de datos fundamentales pre-cargada para {len(info_cache)} tickers.")
        self.ticker_info_cache = info_cache

    def get_optimized_weight_combinations(self):
        """Diferentes combinations de pesos para el modelo de régimen"""
        return [
            {'resilience_nexus': 0.40, 'momentum_6m': 0.25, 'low_vol': 0.15, 'quality': 0.15, 'valuation': 0.05},
            {'resilience_nexus': 0.30, 'momentum_6m': 0.40, 'low_vol': 0.10, 'quality': 0.15, 'valuation': 0.05},
            {'resilience_nexus': 0.60, 'momentum_6m': 0.10, 'low_vol': 0.15, 'quality': 0.10, 'valuation': 0.05},
            {'resilience_nexus': 0.45, 'momentum_6m': 0.25, 'low_vol': 0.15, 'quality': 0.10, 'valuation': 0.05}
        ]

    def get_regime_weight_set(self, current_volatility, previous_performance, benchmark_trend_signal):
        """Modelo de Régimen Dinámico (CALIBRADO Y CONSCIENTE DE TENDENCIA)"""
        trigger_volatility = 0.40
        if benchmark_trend_signal == 1:
            return 1, "BULL (Trend Following)"
        elif benchmark_trend_signal == -1:
            return 2, "CRISIS (Trend Averse)"
        if current_volatility > trigger_volatility:
            return 2, "CRISIS (Vol Spike)"
        else:
            return 3, "NORMAL (Balanceado)"

    def get_period_data(self, tickers, start, end):
        """Descarga datos de precios para un período específico"""
        # Ocultar impresión para un backtest más limpio
        # print(f"Descargando datos ({start} a {end})...")
        try:
            end_date_dt = pd.to_datetime(end) + pd.Timedelta(days=1)
            end_str = end_date_dt.strftime('%Y-%m-%d')
            data_raw = yf.download(tickers, start=start, end=end_str, auto_adjust=False, progress=False, timeout=30)
            if data_raw.empty: return None

            primary_col = None
            if 'Adj Close' in data_raw.columns:
                primary_col = 'Adj Close'
            elif 'Close' in data_raw.columns:
                primary_col = 'Close'
            else:
                 print("  [!] Columnas 'Adj Close' o 'Close' no encontradas.")
                 return None
            
            # Ocultar impresión para un backtest más limpio
            # print(f" Usando precios de '{primary_col}'")
            if isinstance(tickers, list) and len(tickers) > 1:
                price_data = data_raw[primary_col]
            else:
                price_data = data_raw[[primary_col]]
                price_data.columns = [tickers[0]] if isinstance(tickers, list) else [tickers]

            price_data = price_data.loc[start:end]
            price_data = price_data.dropna(axis=0, how='all')
            return price_data
        except Exception as e:
            print(f" Error descargando datos para {tickers}: {e}")
            return None

    def _z_score_series(self, series):
        """Helper para normalizar una serie de factores"""
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        if series.std() > 1e-8:
            return (series - series.mean()) / series.std()
        return series * 0

    def calculate_enhanced_resilience_scores(self, tickers, price_data, ticker_info_map):
        """
        ¡Esta función NO CAMBIA!
        La "inteligencia" ya fue aplicada al 'self.live_gscore_series'
        durante la inicialización.
        """
        
        # 1. Obtener los GScores EN VIVO (ahora basados en hechos, no en tono)
        resilience_scores = (self.live_gscore_series * -1.0).reindex(tickers).fillna(0.0)
        
        # 2. Calcular factores fundamentales (como antes)
        innovation_scores = self.calculate_innovation_centrality(tickers, ticker_info_map)
        logistics_scores = self.calculate_logistics_resilience(tickers, ticker_info_map)

        enhanced_scores = pd.Series(index=tickers, dtype=float)
        for ticker in tickers:
            # Ponderar el GScore en vivo (40%) con los factores fundamentales (60%)
            live_risk_score = resilience_scores.get(ticker, 0.0)
            innovation_score = innovation_scores.get(ticker, 0.5)
            logistics_score = logistics_scores.get(ticker, 0.5)

            enhanced_score = (live_risk_score * 0.40 +
                                 innovation_score * 0.30 +
                                 logistics_score * 0.30)
            
            enhanced_scores[ticker] = enhanced_score

        # Devolver la señal normalizada (Z-score)
        return self._z_score_series(enhanced_scores.fillna(0.0))

    def calculate_innovation_centrality(self, tickers, ticker_info_map):
        """Factor dinámico de innovación (Márgenes y R&D)"""
        raw_scores = pd.DataFrame(index=tickers, columns=['rd_ratio', 'margins'])
        for ticker in tickers:
            info = ticker_info_map.get(ticker)
            if info:
                rd = info.get('researchDevelopment', 0)
                rev = info.get('totalRevenue', 1)
                margins = info.get('profitMargins', 0)
                rd = rd if isinstance(rd, (int, float)) else 0
                rev = rev if isinstance(rev, (int, float)) and rev != 0 else 1
                margins = margins if isinstance(margins, (int, float)) else 0
                raw_scores.loc[ticker, 'rd_ratio'] = rd / rev
                raw_scores.loc[ticker, 'margins'] = margins
        raw_scores = raw_scores.fillna(0).astype(float)
        rd_norm = self._z_score_series(raw_scores['rd_ratio'])
        margins_norm = self._z_score_series(raw_scores['margins'])
        return (rd_norm * 0.5 + margins_norm * 0.5).fillna(0).to_dict()

    def calculate_logistics_resilience(self, tickers, ticker_info_map):
        """Factor dinámico de resiliencia logística (Inventario y Márgenes Brutos)"""
        raw_scores = pd.DataFrame(index=tickers, columns=['inv_ratio', 'gross_margins'])
        for ticker in tickers:
            info = ticker_info_map.get(ticker)
            if info:
                inv = info.get('inventory', 0)
                rev = info.get('totalRevenue', 1)
                gross_margins = info.get('grossMargins', 0)
                inv = inv if isinstance(inv, (int, float)) else 0
                rev = rev if isinstance(rev, (int, float)) and rev != 0 else 1
                gross_margins = gross_margins if isinstance(gross_margins, (int, float)) else 0
                inv_ratio = inv / rev
                raw_scores.loc[ticker, 'inv_ratio'] = 1.0 / (1.0 + inv_ratio) if inv_ratio > 0 else 1.0
                raw_scores.loc[ticker, 'gross_margins'] = gross_margins
        raw_scores = raw_scores.fillna(0).astype(float)
        inv_norm = self._z_score_series(raw_scores['inv_ratio'])
        margins_norm = self._z_score_series(raw_scores['gross_margins'])
        return (inv_norm * 0.5 + margins_norm * 0.5).fillna(0).to_dict()

    def calculate_traditional_factors(self, price_data, ticker_info_map):
        """Calcula factores tradicionales (Momentum, Value, Quality, Low Vol)"""
        returns = price_data.pct_change().dropna(how='all')
        factors = pd.DataFrame(index=price_data.columns)

        for ticker in price_data.columns:
            prices = price_data[ticker].dropna()
            info = ticker_info_map.get(ticker)
            if len(prices) < 126:
                factors.loc[ticker, :] = 0
                continue

            mom_return = (prices.iloc[-1] / prices.iloc[-126] - 1)
            ticker_returns_mom = returns[ticker].iloc[-126:].dropna()
            mom_vol = ticker_returns_mom.std() if len(ticker_returns_mom) > 1 else 1e-8
            factors.loc[ticker, 'momentum_6m'] = mom_return / max(mom_vol, 1e-8)

            pe = info.get('forwardPE') if info else None
            factors.loc[ticker, 'valuation'] = 1.0 / max(pe, 1) if isinstance(pe, (int, float)) else 0

            ticker_returns_qual = returns[ticker].dropna()
            if len(ticker_returns_qual) > 63:
                ret_annual = ticker_returns_qual.mean() * 252
                vol_annual = ticker_returns_qual.std() * np.sqrt(252)
                factors.loc[ticker, 'quality'] = ret_annual / max(vol_annual, 1e-8)
            else:
                factors.loc[ticker, 'quality'] = 0

            ticker_returns_vol = returns[ticker].dropna()
            if len(ticker_returns_vol) > 1:
                volatility = ticker_returns_vol.std() * np.sqrt(252)
                factors.loc[ticker, 'low_vol'] = 1.0 / (1.0 + volatility)
            else:
                factors.loc[ticker, 'low_vol'] = 0.5

        factors = factors.fillna(0).astype(float)
        for column in factors.columns:
            factors[column] = self._z_score_series(factors[column])
        return factors.fillna(0)

    def traditional_strategy(self, price_data, ticker_info_map):
        """Estrategia tradicional (baseline)"""
        traditional_weights = {'momentum_6m': 0.4, 'low_vol': 0.3, 'quality': 0.2, 'valuation': 0.1}
        factors = self.calculate_traditional_factors(price_data, ticker_info_map)
        composite_scores = pd.Series(0.0, index=factors.index)
        for ticker in factors.index:
            score = 0
            for factor, weight in traditional_weights.items():
                if factor in factors.columns:
                    factor_value = factors.loc[ticker, factor] if ticker in factors.index and factor in factors.columns else 0
                    score += factor_value * weight
            composite_scores[ticker] = score
        return composite_scores

    def nexus_strategy(self, price_data, ticker_info_map, current_volatility, previous_performance, benchmark_trend_signal):
        """Estrategia NexusQuant MEJORADA (con régimen y Capa 1)"""
        weight_set_idx, regime_name = self.get_regime_weight_set(current_volatility, previous_performance, benchmark_trend_signal)
        nexus_weights = self.optimized_weights[weight_set_idx]

        factors = self.calculate_traditional_factors(price_data, ticker_info_map)
        valid_tickers = factors.index.tolist()

        # --- ¡AQUÍ SE USA LA FUNCIÓN MODIFICADA! ---
        enhanced_resilience = self.calculate_enhanced_resilience_scores(valid_tickers, price_data, ticker_info_map)
        
        if 'resilience_nexus' not in factors.columns:
            factors['resilience_nexus'] = 0.0
        factors['resilience_nexus'] = enhanced_resilience.reindex(factors.index).fillna(0)

        composite_scores = pd.Series(0.0, index=factors.index)
        for ticker in factors.index:
            score = 0
            total_weight = 0
            for factor, weight in nexus_weights.items():
                if factor in factors.columns:
                    factor_value = factors.loc[ticker, factor]
                    score += factor_value * weight
                    total_weight += weight
            if total_weight > 0:
                composite_scores[ticker] = score / total_weight
        return composite_scores, regime_name

    def adaptive_rebalancing(self, current_volatility, previous_performance):
        """Rebalanceo adaptativo basado en condiciones"""
        if current_volatility > 0.30:
            rebalance_freq = 21
            top_k = 6
        elif previous_performance > 0.10:
            rebalance_freq = 42
            top_k = 8
        else:
            rebalance_freq = 63
            top_k = 8
        return rebalance_freq, top_k

    def calculate_turnover(self, prev_weights_dict, current_weights_dict):
        """Calcula el turnover (rotación) de la cartera."""
        all_tickers = set(prev_weights_dict.keys()) | set(current_weights_dict.keys())
        turnover = 0
        for ticker in all_tickers:
            prev = prev_weights_dict.get(ticker, 0)
            curr = current_weights_dict.get(ticker, 0)
            turnover += abs(curr - prev)
        return turnover

    def optimize_portfolio_weights(self, scores, top_k, price_data_train):
        """Selecciona y pondera la cartera usando el método optimizado"""
        scores = scores.replace([np.inf, -np.inf], np.nan).dropna()
        if scores.empty:
            # print("   [!] Todos los scores son inválidos. No se puede optimizar.")
            return {}
        
        actual_top_k = min(top_k, len(scores))
        if actual_top_k == 0:
            # print("   [!] No hay scores válidos para seleccionar top_k.")
            return {}

        top_scores = scores.nlargest(actual_top_k)
        top_tickers = top_scores.index.tolist()

        def score_weighted_fallback():
            weights_raw = top_scores.clip(lower=0)
            total_score = weights_raw.sum()
            if total_score > 1e-8:
                weights = weights_raw / total_score
            else:
                weights = pd.Series(1.0 / len(top_tickers), index=top_tickers)
            return weights.to_dict()

        if self.optimization_method == 'mean_variance':
            if not all(ticker in price_data_train.columns for ticker in top_tickers):
                # print("   [!] Faltan tickers en price_data_train para M-V. Usando fallback.")
                return score_weighted_fallback()
            
            returns = price_data_train[top_tickers].pct_change().dropna(how='all')
            if len(returns) < 2 or returns.cov().isnull().values.any() or np.linalg.det(returns.cov()) < 1e-20: # Añadida comprobación de determinante
                # print(f"   [!] Datos insuficientes o covarianza inválida (len={len(returns)}) para M-V. Usando fallback.")
                return score_weighted_fallback()

            cov_matrix = returns.cov() * 252
            exp_returns = top_scores

            def objective(weights):
                port_return = np.dot(weights, exp_returns)
                port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                return - (port_return - self.risk_free_rate) / max(port_vol, 1e-9)

            cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
            bnds = tuple((0, self.max_weight_per_asset) for _ in range(len(top_tickers)))
            init_guess = np.ones(len(top_tickers)) / len(top_tickers)

            try:
                result = minimize(objective, init_guess, method='SLSQP', bounds=bnds, constraints=cons, tol=1e-9)
                if result.success:
                    final_weights = np.maximum(0, result.x)
                    final_weights = final_weights / sum(final_weights)
                    return dict(zip(top_tickers, final_weights))
                else:
                    # print(f"   [!] Fallo en optimización Mean-Variance (No success): {result.message}. Usando fallback.")
                    pass
            except Exception as e:
                # print(f"   [!] Excepción en optimización Mean-Variance: {e}. Usando fallback.")
                pass
            return score_weighted_fallback()
        else:
            return score_weighted_fallback()

    def portfolio_performance(self, weights_arr, returns_arr, benchmark_returns=None, turnover=0.0):
        """Calcula métricas de performance (con costos)"""
        returns_arr = np.asarray(returns_arr)
        weights_arr = np.asarray(weights_arr)
        if returns_arr.size == 0 or weights_arr.size == 0: return {}
        if returns_arr.ndim == 1:
            portfolio_returns = returns_arr
        elif returns_arr.ndim == 2:
            if returns_arr.shape[1] != len(weights_arr): return {}
            portfolio_returns = np.dot(returns_arr, weights_arr)
        else: return {}

        if portfolio_returns.size > 0:
            if not portfolio_returns.flags.writeable:
                portfolio_returns = portfolio_returns.copy()
            if turnover > 1e-8:
                portfolio_returns[0] -= turnover * self.transaction_cost

        portfolio_returns = portfolio_returns.flatten()
        if portfolio_returns.size == 0: return {}

        safe_returns = np.maximum(np.nan_to_num(portfolio_returns), -0.9999)
        total_return = np.prod(1 + safe_returns) - 1
        num_days = len(safe_returns)
        annual_return = (1 + total_return) ** (252 / num_days) - 1 if num_days > 0 else 0
        volatility = np.std(safe_returns) * np.sqrt(252)
        sharpe = (annual_return - self.risk_free_rate) / max(volatility, 1e-9)
        cumulative = np.cumprod(1 + safe_returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        alpha = 0
        beta = 1
        if benchmark_returns is not None:
            benchmark_returns = np.asarray(benchmark_returns).flatten()
            aligned_len = min(len(safe_returns), len(benchmark_returns))
            if aligned_len > 1:
                pr_aligned = safe_returns[:aligned_len]
                br_aligned = np.nan_to_num(benchmark_returns[:aligned_len])
                if np.var(pr_aligned) > 1e-12 and np.var(br_aligned) > 1e-12:
                    covariance = np.cov(pr_aligned, br_aligned)[0, 1]
                    benchmark_variance = np.var(br_aligned)
                    beta = covariance / benchmark_variance
                benchmark_total_return = np.prod(1 + br_aligned) - 1
                benchmark_annual_return = (1 + benchmark_total_return) ** (252 / aligned_len) - 1
                alpha = annual_return - (self.risk_free_rate + beta * (benchmark_annual_return - self.risk_free_rate))

        downside_returns = safe_returns[safe_returns < 0]
        downside_vol = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 1 else 0
        sortino = (annual_return - self.risk_free_rate) / max(downside_vol, 1e-9)

        return {
            'total_return': total_return, 'annual_return': annual_return,
            'volatility': volatility, 'sharpe_ratio': sharpe, 'max_drawdown': max_drawdown,
            'alpha': alpha, 'beta': beta, 'sortino_ratio': sortino,
            'returns': portfolio_returns, 'turnover': turnover
        }
    
    def run_enhanced_backtest(self, tickers, start_date, end_date):
        """Backtest MEJORADO con optimizaciones y régimen dinámico (v4.1 CORREGIDO)"""
        print(f"Iniciando backtest mejorado v6.0...")
        print(f"  Período: {start_date} a {end_date}")
        print(f"  Optimización: {self.optimization_method} (Max Peso: {self.max_weight_per_asset})")
        print(f"  Benchmark: {self.benchmark_ticker}")

        all_tickers = list(set(tickers + [self.benchmark_ticker]))
        
        # 1. Descargar TODOS los datos históricos de una vez
        lookback_start = (pd.to_datetime(start_date) - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
        all_price_data = self.get_period_data(all_tickers, lookback_start, end_date)
        
        if all_price_data is None or all_price_data.empty:
            print("[!] Fallo fatal: No se pudieron descargar datos históricos. Abortando.")
            return None
        
        print(f"Datos históricos descargados: {all_price_data.shape[0]} filas.")

        # 2. Preparar el DataFrame de resultados
        dates = all_price_data.loc[start_date:end_date].index
        portfolio_returns = pd.Series(index=dates, dtype=float)
        regime_log = pd.Series(index=dates)
        turnover_log = pd.Series(index=dates, dtype=float).fillna(0.0)

        # 3. Preparar datos del benchmark (MA200 y retornos)
        benchmark_prices = all_price_data[self.benchmark_ticker]
        benchmark_returns = benchmark_prices.pct_change().loc[start_date:end_date]
        ma200 = benchmark_prices.rolling(window=200).mean()

        # 4. Bucle de simulación
        current_weights = {}
        last_rebalance_date = pd.Timestamp(1970, 1, 1)

        # Usar tqdm para una barra de progreso (opcional pero recomendado)
        # from tqdm import tqdm
        # for date in tqdm(dates, desc="Ejecutando Backtest"):
        for date in dates: # Bucle sin barra de progreso
            
            # 4a. Obtener datos de contexto (volatilidad, performance, tendencia)
            train_data_end = date - pd.Timedelta(days=1)
            
            # Asegurar que train_data_end esté en el índice
            if train_data_end not in all_price_data.index:
                portfolio_returns[date] = 0.0
                regime_log[date] = "NORMAL"
                continue

            current_vol = benchmark_returns.loc[:train_data_end].tail(63).std() * np.sqrt(252)
            
            # --- Corrección para KeyError (fin de semana) ---
            price_today = benchmark_prices.loc[train_data_end]
            target_date_3m_ago = train_data_end - pd.DateOffset(months=3)
            price_3m_ago = benchmark_prices.asof(target_date_3m_ago) 
            
            if pd.isna(price_3m_ago) or price_3m_ago == 0:
                prev_perf = 0.0
            else:
                prev_perf = (price_today / price_3m_ago) - 1
            # --- Fin de la corrección ---

            # Señal de tendencia MA200
            current_price = benchmark_prices.loc[train_data_end]
            current_ma200 = ma200.loc[train_data_end]
            
            if pd.isna(current_ma200):
                trend_signal = 0 
            elif current_price > (current_ma200 * 1.01):
                trend_signal = 1 
            elif current_price < (current_ma200 * 0.99):
                trend_signal = -1
            else:
                trend_signal = 0 

            # 4b. Decidir si rebalancear
            rebalance_freq, top_k = self.adaptive_rebalancing(current_vol, prev_perf)
            
            if (date - last_rebalance_date).days >= rebalance_freq:
                if date.dayofweek == 0: # Para imprimir menos, solo los lunes
                    print(f"\n--- REBALANCEO en {date.date()} ---") 
                
                last_rebalance_date = date
                
                train_data_start = train_data_end - pd.DateOffset(months=6)
                price_data_train = all_price_data.loc[train_data_start:train_data_end, tickers]
                price_data_train = price_data_train.dropna(axis=1) 
                
                if price_data_train.empty:
                    current_weights = {}
                    continue

                scores, regime = self.nexus_strategy(
                    price_data_train, self.ticker_info_cache, 
                    current_vol, prev_perf, trend_signal
                )
                regime_log[date] = regime
                if date.dayofweek == 0:
                    print(f"  Régimen detectado: {regime}")
                
                prev_weights = current_weights.copy()
                current_weights = self.optimize_portfolio_weights(scores, top_k, price_data_train)
                
                turnover = self.calculate_turnover(prev_weights, current_weights)
                turnover_log[date] = turnover
                
            else:
                if date > dates[0]:
                    regime_log[date] = regime_log.iloc[-2] 
                else:
                    regime_log[date] = "NORMAL"

            # 4g. Calcular retorno del día
            if not current_weights:
                portfolio_returns[date] = 0.0
                continue
                
            try:
                # --- ¡AQUÍ ESTÁ LA CORRECCIÓN PARA EL ERROR 'inf'! ---
                current_day_prices = all_price_data.loc[date, current_weights.keys()]
                prev_day_prices = all_price_data.loc[train_data_end, current_weights.keys()]
                prev_day_prices[prev_day_prices == 0] = np.nan 
                day_returns_series = (current_day_prices / prev_day_prices) - 1
                day_returns_series = day_returns_series.replace([np.inf, -np.inf], 0).fillna(0.0) 

                weights_arr = np.array([current_weights[t] for t in day_returns_series.index])
                returns_arr = np.array(day_returns_series.values)
                
                day_port_return = np.dot(weights_arr, returns_arr)
                
                if date == last_rebalance_date:
                    day_port_return -= turnover_log[date] * self.transaction_cost
                    
                portfolio_returns[date] = day_port_return
                
            except KeyError as ke:
                portfolio_returns[date] = 0.0
            except Exception as e:
                portfolio_returns[date] = 0.0

        # 5. Calcular métricas finales
        print("\n--- Backtest Completado. Calculando métricas... ---")
        
        portfolio_returns = portfolio_returns.fillna(0.0)
        benchmark_returns = benchmark_returns.fillna(0.0)

        final_metrics = self.portfolio_performance(
            None,
            portfolio_returns.values,
            benchmark_returns.values,
            0 
        )
        
        final_metrics['avg_turnover'] = turnover_log.mean()
        final_metrics['regime_log'] = regime_log
        
        # --- PRIMERA CORRECCIÓN ---
        # Añadir los retornos del benchmark al diccionario de resultados
        final_metrics['benchmark_returns'] = benchmark_returns 
        
        return final_metrics


# ------------------------------------------------------------------
# --- BLOQUE DE EJECUCIÓN PRINCIPAL (ADAPTADO 2019-2025) ---
# ------------------------------------------------------------------

if __name__ == "__main__":
    
    # --- PERÍODO DE ANÁLISIS 2019-2025 ---
    print("\n--- [ANÁLISIS] Ejecutando en período (2019-2025)... ---")
    
    # 1. Definir el universo y el período del backtest
    tickers = [
        "INTC", "TSM", "NVDA", "ASML", "AAPL", "MSFT", 
        "AMD", "QCOM", "MU", "LRCX", "AMAT"
    ]
    start_date = '2019-01-01'
    end_date = '2025-12-31' 
    # --- FIN DE LA CONFIGURACIÓN ---
    
    # 2. Pre-cargar el caché de datos fundamentales
    print("Pre-cargando caché de datos fundamentales (puede tardar un momento)...")
    ticker_info_cache = {}
    tickers_to_load = list(set(tickers + ['SOXX']))
    
    for ticker in tickers_to_load:
        try:
            print(f"  Cargando info para {ticker}...")
            ticker_obj = yf.Ticker(ticker)
            ticker_info_cache[ticker] = ticker_obj.info
            time.sleep(0.5) 
        except Exception as e:
            print(f"  [!] No se pudo cargar info para {ticker}: {e}")
            ticker_info_cache[ticker] = {}
    print("¡Caché de datos fundamentales lista!")

    # 3. Inicializar el Backtester (¡AQUÍ SE EJECUTA LA CAPA 1!)
    backtester = EnhancedNexusBacktester()
    
    # 4. Pasar el caché al backtester
    backtester.set_info_cache(ticker_info_cache)
    
    # 5. Ejecutar el backtest con la señal de Capa 1
    results_nexus = backtester.run_enhanced_backtest(tickers, start_date, end_date)
    
    # 6. Imprimir Resultados
    if results_nexus:
        print(f"\n\n--- 📈 RESULTADOS FINALES (NEXUS v6.0 - ANÁLISIS 2019-2025) ---")
        print(f"  Retorno Anualizado:   {results_nexus['annual_return']:.2%}")
        print(f"  Volatilidad Anual:      {results_nexus['volatility']:.2%}")
        print(f"  Ratio de Sharpe:          {results_nexus['sharpe_ratio']:.2f}")
        print(f"  Ratio de Sortino:         {results_nexus['sortino_ratio']:.2f}")
        print(f"  Máximo Drawdown:        {results_nexus['max_drawdown']:.2%}")
        print(f"  Alpha:                    {results_nexus['alpha']:.2f}")
        print(f"  Beta:                     {results_nexus['beta']:.2f}")
        print(f"  Turnover Promedio:      {results_nexus['avg_turnover']:.2%}")


        # --- SEGUNDA CORRECCIÓN (BLOQUE DE PLOTEO) ---
        
        # 7. Graficar
        print("\nGenerando gráfico de rendimiento...")
        plt.figure(figsize=(15, 7))
        
        # Ya no descargamos datos nuevos. Usamos los retornos del benchmark 
        # que ya se calcularon y fueron devueltos en 'results_nexus'.
        
        # 1. Obtener retornos del benchmark desde los resultados
        bench_returns = results_nexus.get('benchmark_returns')

        if bench_returns is not None and not bench_returns.empty:
            # Graficar Benchmark
            bench_cumulative = (1 + bench_returns).cumprod()
            bench_cumulative.name = f"Benchmark ({backtester.benchmark_ticker})"
            bench_cumulative.plot(legend=True, color='gray', linestyle='--')

            # 2. Graficar la estrategia (usando el índice del benchmark para alinear las fechas)
            nexus_cumulative = (1 + pd.Series(results_nexus['returns'], index=bench_returns.index).fillna(0)).cumprod()
            nexus_cumulative.name = "NexusQuant v6.0"
            nexus_cumulative.plot(legend=True, color='blue', linewidth=2)

            plt.title(f"Rendimiento del Backtest: NexusQuant v6.0 vs {backtester.benchmark_ticker} ({start_date} a {end_date})")
            plt.ylabel("Rendimiento Acumulado")
            plt.xlabel("Fecha")
            plt.grid(True, linestyle=':', alpha=0.6)
            plt.show()
        
        else:
            # Fallback por si algo saliera mal
            print(" [!] No se encontraron 'benchmark_returns' en los resultados. Graficando solo la estrategia.")
            nexus_cumulative = (1 + pd.Series(results_nexus['returns']).fillna(0)).cumprod()
            nexus_cumulative.name = "NexusQuant v6.0"
            nexus_cumulative.plot(legend=True, color='blue', linewidth=2)
            
            plt.title(f"Rendimiento de la Estrategia: NexusQuant v6.0 ({start_date} a {end_date})")
            plt.ylabel("Rendimiento Acumulado")
            plt.xlabel("Fecha")
            plt.grid(True, linestyle=':', alpha=0.6)
            plt.show()

    else:
        print("El backtest no pudo generar resultados.")