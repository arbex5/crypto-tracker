"""Crypto Tracker by Fernando Arbex - Aplicativo GTK4 para criptomoedas."""

__version__ = "1.1.0"
__author__ = "Fernando Arbex"
__email__ = ""

# Exporta módulos principais
from .models import Crypto, ApiUsage
from .api import CryptoAPI, APIWorker
from .cache import CacheManager
from .settings import Settings

__all__ = [
    'Crypto',
    'ApiUsage',
    'CryptoAPI',
    'APIWorker',
    'CacheManager',
    'Settings',
]
