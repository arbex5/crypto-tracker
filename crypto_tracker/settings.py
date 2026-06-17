"""Gerenciamento de configurações do usuário."""

import json
import os
from pathlib import Path
from typing import Optional


class Settings:
    """Gerencia configurações do aplicativo."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "crypto-tracker"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "settings.json"
        self._data = self._load()
    
    def _load(self) -> dict:
        """Carrega configurações do arquivo."""
        if not self.config_file.exists():
            return self._default_settings()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return {**self._default_settings(), **json.load(f)}
        except (json.JSONDecodeError, IOError):
            return self._default_settings()
    
    def _default_settings(self) -> dict:
        """Retorna configurações padrão."""
        return {
            'cmc_api_key': '',
            'use_cmc': False,
            'cache_duration_minutes': 5,
            'max_daily_calls': 300,  # Conservador para plano free
            'theme': 'system',
            'window_width': 1000,
            'window_height': 700,
            'favorites': [],
            'show_brl_price': False,
            'display_asset': 'bitcoin',
            'display_opacity': 0.95,
            'display_pinned': False,
            'auto_refresh_interval': 5,
            'display_quick_assets': []
        }
    
    def save(self):
        """Salva configurações no arquivo."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)
    
    @property
    def cmc_api_key(self) -> str:
        return self._data.get('cmc_api_key', '')
    
    @cmc_api_key.setter
    def cmc_api_key(self, value: str):
        self._data['cmc_api_key'] = value.strip()
        self.save()
    
    @property
    def use_cmc(self) -> bool:
        return bool(self._data.get('use_cmc', False) and self.cmc_api_key)
    
    @use_cmc.setter
    def use_cmc(self, value: bool):
        self._data['use_cmc'] = value
        self.save()
    
    @property
    def cache_duration(self) -> int:
        return self._data.get('cache_duration_minutes', 5)
    
    @property
    def max_daily_calls(self) -> int:
        return self._data.get('max_daily_calls', 300)
    
    @property
    def window_width(self) -> int:
        return self._data.get('window_width', 1000)
    
    @window_width.setter
    def window_width(self, value: int):
        self._data['window_width'] = max(400, int(value))
        self.save()
    
    @property
    def window_height(self) -> int:
        return self._data.get('window_height', 700)
    
    @window_height.setter
    def window_height(self, value: int):
        self._data['window_height'] = max(300, int(value))
        self.save()
    
    @property
    def favorites(self) -> list:
        return self._data.get('favorites', [])
    
    @favorites.setter
    def favorites(self, value: list):
        self._data['favorites'] = list(value)
        self.save()
    
    def is_favorite(self, crypto_id: str) -> bool:
        """Verifica se uma criptomoeda é favorita."""
        return crypto_id in self._data.get('favorites', [])
    
    def add_favorite(self, crypto_id: str):
        """Adiciona uma criptomoeda aos favoritos."""
        favs = set(self._data.get('favorites', []))
        favs.add(crypto_id)
        self._data['favorites'] = list(favs)
        self.save()
    
    def remove_favorite(self, crypto_id: str):
        """Remove uma criptomoeda dos favoritos."""
        favs = set(self._data.get('favorites', []))
        favs.discard(crypto_id)
        self._data['favorites'] = list(favs)
        self.save()
    
    @property
    def show_brl_price(self) -> bool:
        return self._data.get('show_brl_price', False)
    
    @show_brl_price.setter
    def show_brl_price(self, value: bool):
        self._data['show_brl_price'] = bool(value)
        self.save()
    
    @property
    def display_asset(self) -> str:
        return self._data.get('display_asset', 'bitcoin')
    
    @display_asset.setter
    def display_asset(self, value: str):
        self._data['display_asset'] = str(value).lower()
        self.save()
    
    @property
    def display_opacity(self) -> float:
        return self._data.get('display_opacity', 0.95)
    
    @display_opacity.setter
    def display_opacity(self, value: float):
        self._data['display_opacity'] = max(0.3, min(1.0, float(value)))
        self.save()
    
    @property
    def display_pinned(self) -> bool:
        return self._data.get('display_pinned', False)
    
    @display_pinned.setter
    def display_pinned(self, value: bool):
        self._data['display_pinned'] = bool(value)
        self.save()

    @property
    def auto_refresh_interval(self) -> int:
        """Intervalo de auto-atualização em minutos (0 = desativado)."""
        return int(self._data.get('auto_refresh_interval', 5))

    @auto_refresh_interval.setter
    def auto_refresh_interval(self, value: int):
        self._data['auto_refresh_interval'] = max(0, int(value))
        self.save()

    @property
    def display_quick_assets(self) -> list:
        """Lista de símbolos dos ativos de acesso rápido do modo display."""
        return list(self._data.get('display_quick_assets', []))

    @display_quick_assets.setter
    def display_quick_assets(self, value: list):
        self._data['display_quick_assets'] = [str(v).lower() for v in value]
        self.save()

    def has_api_key(self) -> bool:
        """Verifica se há uma API key configurada."""
        return bool(self.cmc_api_key)
