"""Integração com APIs CoinMarketCap e CoinGecko."""

import json
import random
import threading
import urllib.request
import urllib.error
from typing import List, Callable, Optional, Dict, Any
from datetime import datetime
from .models import Crypto, ApiUsage
from .cache import CacheManager
from .settings import Settings


class CryptoAPI:
    """Cliente unificado para APIs de criptomoedas."""
    
    def __init__(self):
        self.settings = Settings()
        self.cache = CacheManager()
        self._lock = threading.Lock()
        self._last_error: Optional[str] = None
        self._usage = ApiUsage()
        self._load_usage()
        self._usd_brl_rate: Optional[float] = None
    
    def _load_usage(self):
        """Carrega estatísticas de uso."""
        data = self.cache.get_usage()
        self._usage.calls_today = data.get('calls_today', 0)
        self._usage.total_calls_month = data.get('total_calls_month', 0)
        if data.get('last_call'):
            try:
                self._usage.last_call_date = datetime.fromisoformat(data['last_call'])
            except ValueError:
                pass
    
    def _save_usage(self):
        """Salva estatísticas de uso."""
        self.cache.save_usage(self._usage.calls_today, self._usage.total_calls_month)
    
    @property
    def last_error(self) -> Optional[str]:
        with self._lock:
            return self._last_error
    
    @property
    def usage_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de uso."""
        return {
            'calls_today': self._usage.calls_today,
            'total_month': self._usage.total_calls_month,
            'remaining_today': max(0, self.settings.max_daily_calls - self._usage.calls_today)
        }
    
    @property
    def usd_brl_rate(self) -> Optional[float]:
        """Retorna a taxa de câmbio USD/BRL, se disponível."""
        return self._usd_brl_rate
    
    def fetch_usd_brl_rate(self) -> Optional[float]:
        """Busca a cotação atual do USD para BRL (com cache)."""
        # Verifica cache primeiro
        cached_rate = self.cache.get_exchange_rate("USD-BRL")
        if cached_rate and cached_rate > 0:
            self._usd_brl_rate = cached_rate
            print(f"[DEBUG] USD/BRL rate from cache: {cached_rate}")
            return cached_rate
        
        try:
            url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "User-Agent": "CryptoTracker/1.0"},
                method='GET'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            rate = float(data.get("USDBRL", {}).get("bid", 0))
            if rate > 0:
                self._usd_brl_rate = rate
                self.cache.save_exchange_rate("USD-BRL", rate)
                print(f"[DEBUG] USD/BRL rate: {rate}")
                return rate
            
            return None
            
        except Exception as e:
            print(f"[DEBUG] USD/BRL fetch failed (non-critical): {e}")
            return None
    
    def _apply_usd_brl_rate(self, cryptos: List[Crypto]):
        """Aplica a taxa USD/BRL aos preços das criptomoedas."""
        if not self._usd_brl_rate or self._usd_brl_rate <= 0:
            return
        
        for crypto in cryptos:
            crypto.brl_price = crypto.current_price * self._usd_brl_rate
    
    def _fetch_usd_brl_crypto(self) -> Optional[Crypto]:
        """Busca dados históricos do USD/BRL e cria um Crypto artificial."""
        try:
            # Busca cotação atual
            current_url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
            request = urllib.request.Request(
                current_url,
                headers={"Accept": "application/json", "User-Agent": "CryptoTracker/1.0"},
                method='GET'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                current_data = json.loads(response.read().decode("utf-8"))
            
            current = current_data.get("USDBRL", {})
            current_bid = float(current.get("bid", 0))
            if current_bid <= 0:
                return None
            
            # Busca últimas 24 horas para variação 1h e 24h
            hourly_url = "https://economia.awesomeapi.com.br/json/USD-BRL/24"
            request = urllib.request.Request(
                hourly_url,
                headers={"Accept": "application/json", "User-Agent": "CryptoTracker/1.0"},
                method='GET'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                hourly_data = json.loads(response.read().decode("utf-8"))
            
            hourly_bids = [float(item.get("bid", 0)) for item in hourly_data if float(item.get("bid", 0)) > 0]
            
            # Calcula variações de 1h e 24h
            change_1h = 0.0
            change_24h = 0.0
            if len(hourly_bids) >= 2:
                # O primeiro é o mais recente, o último é o mais antigo
                change_1h = ((hourly_bids[0] - hourly_bids[1]) / hourly_bids[1]) * 100 if hourly_bids[1] > 0 else 0
            if len(hourly_bids) >= 24:
                change_24h = ((hourly_bids[0] - hourly_bids[23]) / hourly_bids[23]) * 100 if hourly_bids[23] > 0 else 0
            elif len(hourly_bids) >= 2:
                change_24h = ((hourly_bids[0] - hourly_bids[-1]) / hourly_bids[-1]) * 100 if hourly_bids[-1] > 0 else 0
            
            # Busca últimos 7 dias para variação 7d e sparkline
            daily_url = "https://economia.awesomeapi.com.br/json/daily/USD-BRL/7"
            request = urllib.request.Request(
                daily_url,
                headers={"Accept": "application/json", "User-Agent": "CryptoTracker/1.0"},
                method='GET'
            )
            
            with urllib.request.urlopen(request, timeout=5) as response:
                daily_data = json.loads(response.read().decode("utf-8"))
            
            daily_bids = [float(item.get("bid", 0)) for item in daily_data if float(item.get("bid", 0)) > 0]
            
            change_7d = 0.0
            if len(daily_bids) >= 2:
                change_7d = ((daily_bids[0] - daily_bids[-1]) / daily_bids[-1]) * 100 if daily_bids[-1] > 0 else 0
            
            # Sparkline: inverte para ordem cronológica (mais antigo -> mais recente)
            sparkline = list(reversed(daily_bids))
            # Se tiver poucos pontos, preenche com repetição do primeiro
            while len(sparkline) < 7:
                sparkline.insert(0, sparkline[0] if sparkline else current_bid)
            
            # Salva taxa no cache
            self._usd_brl_rate = current_bid
            self.cache.save_exchange_rate("USD-BRL", current_bid)
            
            return Crypto(
                id="USD-BRL",
                symbol="USD",
                name="Dólar / Real",
                current_price=current_bid,
                market_cap_rank=0,
                price_change_percentage_24h=change_24h,
                price_change_percentage_1h=change_1h,
                price_change_percentage_7d=change_7d,
                sparkline_7d=sparkline,
                image=None,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            print(f"[DEBUG] USD/BRL crypto fetch failed (non-critical): {e}")
            return None
    
    def get_top_cryptos(self, limit: int = 50, force_refresh: bool = False) -> List[Crypto]:
        """
        Obtém as principais criptomoedas.
        
        Estratégia:
        1. Tenta cache primeiro
        2. Se CMC configurado e tem crédito -> usa CMC
        3. Senão -> usa CoinGecko (gratuita)
        4. Adiciona USD/BRL como posição 0
        """
        cryptos = []
        
        # Tenta cache primeiro (se não for forçado refresh)
        if not force_refresh:
            cached = self.cache.get_cached_cryptos()
            if cached:
                print(f"[DEBUG] Usando cache: {len(cached)} cryptos")
                cryptos = cached
        
        # Se não tem cache, busca das APIs
        if not cryptos:
            # Tenta CMC se configurado e tem crédito
            if self.settings.use_cmc and self._usage.can_make_call(self.settings.max_daily_calls):
                print(f"[DEBUG] Tentando CMC API...")
                cryptos = self._fetch_from_cmc(limit)
                if cryptos:
                    print(f"[DEBUG] CMC retornou {len(cryptos)} cryptos")
                    self._usage.register_call()
                    self._save_usage()
                    self.cache.save_cryptos(cryptos)
                else:
                    print(f"[DEBUG] CMC falhou, erro: {self._last_error}")
            else:
                if not self.settings.use_cmc:
                    print(f"[DEBUG] CMC não configurado ou desativado")
                else:
                    print(f"[DEBUG] Limite de chamadas atingido")
            
            # Fallback para CoinGecko (gratuita)
            if not cryptos:
                print(f"[DEBUG] Usando CoinGecko...")
                cryptos = self._fetch_from_coingecko(limit)
                if cryptos:
                    print(f"[DEBUG] CoinGecko retornou {len(cryptos)} cryptos")
                    self.cache.save_cryptos(cryptos)
        
        # Adiciona USD/BRL como posição 0
        usd_brl = self._fetch_usd_brl_crypto()
        if usd_brl:
            cryptos.insert(0, usd_brl)
        
        return cryptos
    
    def _fetch_from_cmc(self, limit: int) -> List[Crypto]:
        """Busca dados da CoinMarketCap API."""
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            
            headers = {
                'Accept': 'application/json',
                'X-CMC_PRO_API_KEY': self.settings.cmc_api_key,
            }
            
            params = f"?limit={limit}&convert=USD"
            
            request = urllib.request.Request(url + params, headers=headers, method='GET')
            
            print(f"[DEBUG] CMC Request: {url + params}")
            print(f"[DEBUG] CMC Headers: {headers}")
            
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                result = json.loads(data.decode('utf-8'))
            
            print(f"[DEBUG] CMC Response status: {response.status}")
            
            cryptos = []
            for item in result.get('data', []):
                quote = item.get('quote', {}).get('USD', {})
                
                crypto = Crypto(
                    id=str(item.get('id', '')),
                    symbol=item.get('symbol', ''),
                    name=item.get('name', ''),
                    current_price=quote.get('price', 0) or 0,
                    market_cap_rank=item.get('cmc_rank', 0) or 0,
                    price_change_percentage_24h=quote.get('percent_change_24h', 0) or 0,
                    price_change_percentage_1h=quote.get('percent_change_1h', 0) or 0,
                    price_change_percentage_7d=quote.get('percent_change_7d', 0) or 0,
                    sparkline_7d=[],  # CMC não fornece sparkline diretamente
                    image=None,  # Será carregado separadamente
                    last_updated=datetime.now()
                )
                cryptos.append(crypto)
            
            print(f"[DEBUG] Processed {len(cryptos)} cryptos from CMC")
            
            # Busca logos em lote (economiza chamadas)
            self._fetch_cmc_logos(cryptos)
            
            # Enriquece com sparklines da CoinGecko (CMC não fornece)
            self._enrich_with_coingecko_sparklines(cryptos)
            
            # Se ainda não tem sparklines, gera sintéticos
            for crypto in cryptos:
                if not crypto.sparkline_7d or len(crypto.sparkline_7d) < 10:
                    crypto.sparkline_7d = self._generate_synthetic_sparkline(
                        crypto.current_price,
                        crypto.price_change_percentage_7d
                    )
            
            with self._lock:
                self._last_error = None
            
            return cryptos
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            error_msg = f"CMC HTTP {e.code}: {error_body}"
            print(f"[ERROR] {error_msg}")
            with self._lock:
                self._last_error = error_msg
            return []
        except Exception as e:
            error_msg = f"CMC Error: {str(e)}"
            print(f"[ERROR] {error_msg}")
            with self._lock:
                self._last_error = error_msg
            return []
    
    def _fetch_cmc_logos(self, cryptos: List[Crypto]):
        """Busca URLs dos logos das criptos."""
        try:
            if len(cryptos) == 0:
                return
                
            ids = ','.join([str(c.id) for c in cryptos[:50]])
            url = f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id={ids}"
            
            headers = {
                'Accept': 'application/json',
                'X-CMC_PRO_API_KEY': self.settings.cmc_api_key,
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            data = result.get('data', {})
            for crypto in cryptos:
                if str(crypto.id) in data:
                    crypto.image = data[str(crypto.id)].get('logo')
                    
        except Exception as e:
            print(f"[DEBUG] Logo fetch failed: {e}")
            # Falha silenciosa - logos são opcionais
            pass
    
    def _generate_synthetic_sparkline(self, base_price: float, change_7d_pct: float, points: int = 100) -> List[float]:
        """Gera um sparkline sintético suave baseado na variação percentual de 7 dias."""
        if base_price <= 0:
            base_price = 1.0
        
        # Variação absoluta em decimal
        change_decimal = change_7d_pct / 100
        total_factor = 1 + change_decimal
        
        # Preço no início do período
        start_price = base_price / total_factor if total_factor != 0 else base_price
        
        # Volatilidade por passo: proporcional à variação total, mas com limite
        # Stablecoins (< 0.5% de variação) ficam quase retas
        abs_change = abs(change_decimal)
        if abs_change < 0.005:
            step_volatility = 0.00005  # ~0.005% por passo
        elif abs_change < 0.02:
            step_volatility = abs_change / points * 2.5
        else:
            step_volatility = abs_change / points * 1.8
        
        # Gera um random walk com mean reversion para a linha target
        raw_data = [start_price]
        current = start_price
        velocity = 0.0
        
        for i in range(1, points):
            progress = i / points
            # Tendência linear (o caminho "ideal")
            target = start_price + (base_price - start_price) * progress
            
            # Mean reversion: puxa de volta em direção ao target
            deviation = current - target
            pull_back = -deviation * 0.08
            
            # Random walk com momentum (velocity)
            velocity += random.uniform(-step_volatility, step_volatility) * base_price
            velocity *= 0.85  # damping (amortecimento)
            
            current = current + velocity + pull_back
            if current <= 0:
                current = target * 0.999
            
            raw_data.append(current)
        
        # Força o último ponto ser exatamente o preço atual
        raw_data[-1] = base_price
        
        # Suavização com média móvel de 5 pontos para curva orgânica
        smoothed = []
        window = 5
        half = window // 2
        for i in range(len(raw_data)):
            start = max(0, i - half)
            end = min(len(raw_data), i + half + 1)
            avg = sum(raw_data[start:end]) / (end - start)
            smoothed.append(avg)
        
        # Ajusta extremidades para manter preço inicial/final
        smoothed[0] = start_price
        smoothed[-1] = base_price
        
        return smoothed
    
    def _enrich_with_coingecko_sparklines(self, cryptos: List[Crypto]):
        """Busca sparklines da CoinGecko e atualiza os objetos Crypto."""
        try:
            if not cryptos:
                return
                
            # Busca sparklines para as top 250 (mesmo limite da chamada normal)
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                "?vs_currency=usd"
                "&order=market_cap_desc"
                "&per_page=250"
                "&page=1"
                "&sparkline=true"
            )
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTracker/1.0"
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            # Cria um mapa por símbolo (lowercase para comparação)
            sparkline_map = {}
            for item in data:
                symbol = item.get("symbol", "").lower()
                sparkline = item.get("sparkline_in_7d", {}).get("price", [])
                if symbol and sparkline:
                    sparkline_map[symbol] = sparkline
            
            # Atualiza os cryptos com os sparklines
            updated = 0
            for crypto in cryptos:
                symbol = crypto.symbol.lower()
                if symbol in sparkline_map:
                    crypto.sparkline_7d = sparkline_map[symbol]
                    updated += 1
            
            print(f"[DEBUG] Enriched {updated}/{len(cryptos)} cryptos with sparklines from CoinGecko")
            
        except Exception as e:
            print(f"[DEBUG] Sparkline enrichment failed (non-critical): {e}")
            # Falha silenciosa - sparklines são opcionais
            pass
    
    def _fetch_from_coingecko(self, limit: int) -> List[Crypto]:
        """Busca dados da CoinGecko API (gratuita)."""
        try:
            url = (
                "https://api.coingecko.com/api/v3/coins/markets"
                f"?vs_currency=usd"
                f"&order=market_cap_desc"
                f"&per_page={min(limit, 250)}"
                f"&page=1"
                f"&sparkline=true"  # Inclui sparkline de 7 dias
                f"&price_change_percentage=1h,24h,7d"
            )
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "CryptoTracker/1.0 (by Fernando Arbex)"
            }
            
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            
            cryptos = []
            for item in data:
                sparkline = item.get('sparkline_in_7d', {}).get('price', [])
                
                # Pega variações - CoinGecko retorna em formato diferente
                changes = item.get('price_change_percentage_1h_in_currency', 0) or 0
                change24 = item.get('price_change_percentage_24h_in_currency', 0)
                if change24 is None:
                    change24 = item.get('price_change_percentage_24h', 0) or 0
                change7d = item.get('price_change_percentage_7d_in_currency', 0) or 0
                
                crypto = Crypto(
                    id=item.get("id", ""),
                    symbol=item.get("symbol", ""),
                    name=item.get("name", ""),
                    current_price=item.get("current_price", 0) or 0,
                    market_cap_rank=item.get("market_cap_rank", 0) or 0,
                    price_change_percentage_24h=change24,
                    price_change_percentage_1h=changes,
                    price_change_percentage_7d=change7d,
                    sparkline_7d=sparkline if sparkline else [],
                    image=item.get("image"),
                    last_updated=datetime.now()
                )
                cryptos.append(crypto)
            
            with self._lock:
                self._last_error = None
            
            return cryptos
            
        except Exception as e:
            with self._lock:
                self._last_error = f"CoinGecko Error: {str(e)}"
            return self._get_fallback_cryptos(limit)
    
    def _get_fallback_cryptos(self, limit: int) -> List[Crypto]:
        """Retorna dados de fallback quando todas as APIs falham."""
        fallback_data = [
            {
                "id": "bitcoin", "symbol": "btc", "name": "Bitcoin",
                "current_price": 67542.30, "market_cap_rank": 1,
                "price_change_percentage_24h": 2.45,
                "price_change_percentage_1h": 0.35,
                "price_change_percentage_7d": 5.20,
                "image": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
            },
            {
                "id": "ethereum", "symbol": "eth", "name": "Ethereum",
                "current_price": 3520.80, "market_cap_rank": 2,
                "price_change_percentage_24h": -1.23,
                "price_change_percentage_1h": -0.15,
                "price_change_percentage_7d": 3.45,
                "image": "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
            },
            {
                "id": "tether", "symbol": "usdt", "name": "Tether",
                "current_price": 1.00, "market_cap_rank": 3,
                "price_change_percentage_24h": 0.01,
                "price_change_percentage_1h": 0.00,
                "price_change_percentage_7d": -0.02,
                "image": "https://assets.coingecko.com/coins/images/325/small/Tether.png"
            },
        ]
        
        cryptos = []
        for item in fallback_data[:limit]:
            crypto = Crypto(
                id=item["id"],
                symbol=item["symbol"],
                name=item["name"],
                current_price=item["current_price"],
                market_cap_rank=item["market_cap_rank"],
                price_change_percentage_24h=item["price_change_percentage_24h"],
                price_change_percentage_1h=item.get("price_change_percentage_1h", 0),
                price_change_percentage_7d=item.get("price_change_percentage_7d", 0),
                sparkline_7d=[item["current_price"] * (1 + (i-50)*0.001) for i in range(100)],
                image=item.get("image"),
                last_updated=datetime.now()
            )
            cryptos.append(crypto)
        
        return cryptos
    
    def search_cryptos(self, query: str, cryptos: List[Crypto]) -> List[Crypto]:
        """Filtra criptomoedas baseado em uma busca."""
        query = query.lower().strip()
        if not query:
            return cryptos
        
        return [
            c for c in cryptos
            if query in c.name.lower() 
            or query in c.symbol.lower()
            or query in c.id.lower()
        ]


class APIWorker(threading.Thread):
    """Thread worker para fazer requisições à API sem travar a UI."""
    
    def __init__(self, api: CryptoAPI, callback: Callable[[List[Crypto]], None], 
                 limit: int = 50, force_refresh: bool = False):
        super().__init__(daemon=True)
        self.api = api
        self.callback = callback
        self.limit = limit
        self.force_refresh = force_refresh
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        if not self._cancelled:
            cryptos = self.api.get_top_cryptos(self.limit, self.force_refresh)
            if not self._cancelled:
                from gi.repository import GLib
                GLib.idle_add(self.callback, cryptos)
