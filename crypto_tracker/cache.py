"""Sistema de cache para economizar chamadas à API."""

import json
import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .models import Crypto


class CacheManager:
    """Gerencia cache local de dados das criptomoedas."""
    
    CACHE_DURATION = 300  # 5 minutos
    
    EXCHANGE_RATE_DURATION = 1800  # 30 minutos
    
    def __init__(self):
        self.cache_dir = Path.home() / ".cache" / "crypto-tracker"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_file = self.cache_dir / "crypto_data.json"
        self.usage_file = self.cache_dir / "api_usage.json"
        self.exchange_file = self.cache_dir / "exchange_rate.json"
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Verifica se o cache ainda é válido."""
        return (time.time() - timestamp) < self.CACHE_DURATION
    
    def get_cached_cryptos(self) -> Optional[List[Crypto]]:
        """Retorna dados em cache se válidos."""
        if not self.data_file.exists():
            return None
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not self._is_cache_valid(data.get('timestamp', 0)):
                return None
            
            cryptos = []
            for item in data.get('cryptos', []):
                crypto = Crypto(
                    id=item.get('id', ''),
                    symbol=item.get('symbol', ''),
                    name=item.get('name', ''),
                    current_price=item.get('current_price', 0),
                    market_cap_rank=item.get('market_cap_rank', 0),
                    price_change_percentage_24h=item.get('price_change_percentage_24h', 0),
                    price_change_percentage_1h=item.get('price_change_percentage_1h', 0),
                    price_change_percentage_7d=item.get('price_change_percentage_7d', 0),
                    sparkline_7d=item.get('sparkline_7d', []),
                    image=item.get('image'),
                    last_updated=datetime.fromisoformat(item['last_updated']) if item.get('last_updated') else None,
                    is_favorite=item.get('is_favorite', False),
                    brl_price=item.get('brl_price')
                )
                cryptos.append(crypto)
            
            return cryptos
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def save_cryptos(self, cryptos: List[Crypto]):
        """Salva dados no cache."""
        data = {
            'timestamp': time.time(),
            'cryptos': []
        }
        
        for crypto in cryptos:
            data['cryptos'].append({
                'id': crypto.id,
                'symbol': crypto.symbol,
                'name': crypto.name,
                'current_price': crypto.current_price,
                'market_cap_rank': crypto.market_cap_rank,
                'price_change_percentage_24h': crypto.price_change_percentage_24h,
                'price_change_percentage_1h': crypto.price_change_percentage_1h,
                'price_change_percentage_7d': crypto.price_change_percentage_7d,
                'sparkline_7d': crypto.sparkline_7d,
                'image': crypto.image,
                'last_updated': crypto.last_updated.isoformat() if crypto.last_updated else None,
                'is_favorite': crypto.is_favorite,
                'brl_price': crypto.brl_price
            })
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def get_usage(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso."""
        if not self.usage_file.exists():
            return {'calls_today': 0, 'total_calls_month': 0, 'last_call': None}
        
        try:
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {'calls_today': 0, 'total_calls_month': 0, 'last_call': None}
    
    def save_usage(self, calls_today: int, total_calls_month: int):
        """Salva estatísticas de uso."""
        data = {
            'calls_today': calls_today,
            'total_calls_month': total_calls_month,
            'last_call': datetime.now().isoformat()
        }
        
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_exchange_rate(self, pair: str = "USD-BRL") -> Optional[float]:
        """Retorna taxa de câmbio em cache se válida."""
        if not self.exchange_file.exists():
            return None
        
        try:
            with open(self.exchange_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if data.get('pair') != pair:
                return None
            
            timestamp = data.get('timestamp', 0)
            if (time.time() - timestamp) > self.EXCHANGE_RATE_DURATION:
                return None
            
            rate = data.get('rate')
            return float(rate) if rate else None
            
        except (json.JSONDecodeError, ValueError, KeyError):
            return None
    
    def save_exchange_rate(self, pair: str, rate: float):
        """Salva taxa de câmbio no cache."""
        data = {
            'pair': pair,
            'rate': float(rate),
            'timestamp': time.time()
        }
        
        with open(self.exchange_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def clear(self):
        """Limpa o cache."""
        if self.data_file.exists():
            self.data_file.unlink()
        
        if self.exchange_file.exists():
            self.exchange_file.unlink()
