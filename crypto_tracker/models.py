"""Modelos de dados para as criptomoedas."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Crypto:
    """Representa uma criptomoeda."""
    
    id: str
    symbol: str
    name: str
    current_price: float
    market_cap_rank: int
    price_change_percentage_24h: float
    # Novos campos
    price_change_percentage_1h: float = 0.0
    price_change_percentage_7d: float = 0.0
    sparkline_7d: List[float] = field(default_factory=list)
    image: Optional[str] = None
    last_updated: Optional[datetime] = None
    is_favorite: bool = False
    brl_price: Optional[float] = None
    
    @property
    def formatted_price(self) -> str:
        """Retorna o preço formatado."""
        if self.current_price >= 1000:
            return f"${self.current_price:,.2f}"
        elif self.current_price >= 1:
            return f"${self.current_price:.2f}"
        else:
            return f"${self.current_price:.6f}"
    
    @property
    def formatted_brl_price(self) -> str:
        """Retorna o preço em BRL formatado."""
        price = self.brl_price if self.brl_price is not None else 0
        if price >= 1000:
            return f"R${price:,.2f}"
        elif price >= 1:
            return f"R${price:.2f}"
        else:
            return f"R${price:.4f}"
    
    @property
    def formatted_change_1h(self) -> str:
        """Retorna a variação 1h formatada."""
        prefix = "▲ " if self.price_change_percentage_1h >= 0 else "▼ "
        return f"{prefix}{abs(self.price_change_percentage_1h):.2f}%"
    
    @property
    def formatted_change_24h(self) -> str:
        """Retorna a variação 24h formatada."""
        prefix = "▲ " if self.price_change_percentage_24h >= 0 else "▼ "
        return f"{prefix}{abs(self.price_change_percentage_24h):.2f}%"
    
    @property
    def formatted_change_7d(self) -> str:
        """Retorna a variação 7d formatada."""
        prefix = "▲ " if self.price_change_percentage_7d >= 0 else "▼ "
        return f"{prefix}{abs(self.price_change_percentage_7d):.2f}%"
    
    @property
    def is_positive_1h(self) -> bool:
        return self.price_change_percentage_1h >= 0
    
    @property
    def is_positive_24h(self) -> bool:
        return self.price_change_percentage_24h >= 0
    
    @property
    def is_positive_7d(self) -> bool:
        return self.price_change_percentage_7d >= 0
    
    @property
    def symbol_upper(self) -> str:
        """Retorna o símbolo em maiúsculas."""
        return self.symbol.upper()


@dataclass
class ApiUsage:
    """Rastreia o uso da API para evitar limites."""
    
    calls_today: int = 0
    last_call_date: Optional[datetime] = None
    total_calls_month: int = 0
    
    def can_make_call(self, max_calls: int = 300) -> bool:
        """Verifica se pode fazer uma chamada (limite diário conservador)."""
        today = datetime.now().date()
        
        # Reseta contador se for novo dia
        if self.last_call_date and self.last_call_date.date() != today:
            self.calls_today = 0
        
        return self.calls_today < max_calls
    
    def register_call(self):
        """Registra uma chamada à API."""
        today = datetime.now()
        
        # Reseta se for novo dia
        if self.last_call_date and self.last_call_date.date() != today.date():
            self.calls_today = 0
        
        self.calls_today += 1
        self.total_calls_month += 1
        self.last_call_date = today
