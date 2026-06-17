"""Sistema de gerenciamento de ícones das criptomoedas."""

import os
import urllib.request
import threading
from pathlib import Path
from typing import Optional, Dict
from gi.repository import Gtk, GdkPixbuf, Gdk, GLib
import cairo


class IconManager:
    """Gerencia ícones locais das criptomoedas."""
    
    # Mapeamento de symbols para nomes de arquivo
    ICON_MAP = {
        'btc': 'bitcoin',
        'eth': 'ethereum', 
        'usdt': 'tether',
        'bnb': 'bnb',
        'sol': 'solana',
        'xrp': 'xrp',
        'usdc': 'usd-coin',
        'ada': 'cardano',
        'doge': 'dogecoin',
        'trx': 'tron',
        'avax': 'avalanche',
        'link': 'chainlink',
        'ton': 'toncoin',
        'wbtc': 'wrapped-bitcoin',
        'sui': 'sui',
        'xlm': 'stellar',
        'hbar': 'hedera',
        'shib': 'shiba-inu',
        'dot': 'polkadot',
        'leo': 'leo-token',
        'bch': 'bitcoin-cash',
        'ltc': 'litecoin',
        'uni': 'uniswap',
        'pepe': 'pepe',
        'near': 'near',
        'icp': 'internet-computer',
        'apt': 'aptos',
        'dai': 'dai',
        'pol': 'polygon',
        'etc': 'ethereum-classic',
        'render': 'render-token',
        'cro': 'cronos',
        'tao': 'bittensor',
        'vet': 'vechain',
        'arb': 'arbitrum',
        'imx': 'immutable-x',
        'mnt': 'mantle',
        'kas': 'kaspa',
        'fil': 'filecoin',
        'okb': 'okb',
        'stx': 'stacks',
        'atom': 'cosmos',
        'grt': 'the-graph',
    }
    
    def __init__(self):
        self.icons_dir = Path.home() / ".local" / "share" / "crypto-tracker" / "icons"
        self.icons_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Optional[GdkPixbuf.Pixbuf]] = {}
        self._lock = threading.Lock()
    
    def get_icon_path(self, symbol: str) -> Optional[Path]:
        """Retorna o caminho do ícone local se existir."""
        symbol_lower = symbol.lower()
        
        # Tenta várias extensões
        for ext in ['.png', '.svg', '.jpg', '.jpeg', '.webp']:
            # Tenta pelo symbol direto
            icon_path = self.icons_dir / f"{symbol_lower}{ext}"
            if icon_path.exists():
                return icon_path
            
            # Tenta pelo mapeamento
            mapped_name = self.ICON_MAP.get(symbol_lower)
            if mapped_name:
                icon_path = self.icons_dir / f"{mapped_name}{ext}"
                if icon_path.exists():
                    return icon_path
        
        return None
    
    def get_icon_pixbuf(self, symbol: str, size: int = 32) -> Optional[GdkPixbuf.Pixbuf]:
        """Retorna um Pixbuf do ícone redimensionado."""
        cache_key = f"{symbol.lower()}_{size}"
        
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        icon_path = self.get_icon_path(symbol)
        if not icon_path:
            return None
        
        try:
            # Carrega e redimensiona
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(icon_path),
                width=size,
                height=size,
                preserve_aspect_ratio=True
            )
            
            with self._lock:
                self._cache[cache_key] = pixbuf
            
            return pixbuf
            
        except Exception as e:
            print(f"[ERROR] Failed to load icon {icon_path}: {e}")
            return None
    
    def get_icon_image(self, symbol: str, size: int = 32) -> Optional[Gtk.Image]:
        """Retorna um Gtk.Image com o ícone."""
        pixbuf = self.get_icon_pixbuf(symbol, size)
        
        if pixbuf:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            return image
        
        return None
    
    def create_icon_with_fallback(self, symbol: str, size: int = 32) -> Gtk.Widget:
        """Cria um widget com ícone ou fallback."""
        # Tenta ícone local
        pixbuf = self.get_icon_pixbuf(symbol, size)
        if pixbuf:
            return self._create_icon_widget(pixbuf, symbol, size)
        
        # Fallback: cria ícone circular com letra
        return self._create_fallback_icon(symbol, size)
    
    def _create_icon_widget(self, pixbuf: GdkPixbuf.Pixbuf, symbol: str, size: int = 32) -> Gtk.DrawingArea:
        """Cria um widget circular que desenha o ícone preenchendo todo o espaço."""
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_content_width(size)
        drawing_area.set_content_height(size)
        
        def draw_icon(da, ctx, width, height, user_data):
            center_x = width / 2
            center_y = height / 2
            radius = min(width, height) / 2
            
            # Clip circular
            ctx.arc(center_x, center_y, radius, 0, 2 * 3.14159)
            ctx.clip()
            
            # Escala o ícone para preencher o círculo (pode cortar um pouco para manter proporção)
            img_width = pixbuf.get_width()
            img_height = pixbuf.get_height()
            
            if img_width > 0 and img_height > 0:
                # Usa a maior escala para cobrir todo o círculo (crop centralizado)
                scale = max(width / img_width, height / img_height)
                draw_width = img_width * scale
                draw_height = img_height * scale
                
                x = (width - draw_width) / 2
                y = (height - draw_height) / 2
                
                # Desenha o pixbuf escalado
                Gdk.cairo_set_source_pixbuf(ctx, pixbuf, x, y)
                ctx.paint()
        
        drawing_area.set_draw_func(draw_icon, None)
        return drawing_area
    
    def _create_fallback_icon(self, symbol: str, size: int = 32) -> Gtk.DrawingArea:
        """Cria um ícone circular de fallback com a primeira letra."""
        drawing_area = Gtk.DrawingArea()
        drawing_area.set_content_width(size)
        drawing_area.set_content_height(size)
        
        # Gera cor baseada no symbol
        colors = [
            (0.9, 0.3, 0.3),  # Vermelho
            (0.3, 0.7, 0.3),  # Verde
            (0.3, 0.5, 0.9),  # Azul
            (0.9, 0.6, 0.2),  # Laranja
            (0.7, 0.3, 0.8),  # Roxo
            (0.2, 0.7, 0.8),  # Ciano
            (0.9, 0.7, 0.2),  # Amarelo
            (0.5, 0.5, 0.5),  # Cinza
        ]
        color_idx = hash(symbol.lower()) % len(colors)
        bg_color = colors[color_idx]
        
        letter = symbol[0].upper() if symbol else "?"
        
        def draw_icon(da, ctx, width, height, user_data):
            # Fundo circular
            center_x = width / 2
            center_y = height / 2
            radius = min(width, height) / 2 - 1
            
            ctx.arc(center_x, center_y, radius, 0, 2 * 3.14159)
            ctx.set_source_rgb(*bg_color)
            ctx.fill_preserve()
            
            # Borda
            ctx.set_source_rgba(1, 1, 1, 0.3)
            ctx.set_line_width(1)
            ctx.stroke()
            
            # Texto
            ctx.set_source_rgb(1, 1, 1)
            ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            
            # Calcula tamanho da fonte
            font_size = radius * 1.2
            ctx.set_font_size(font_size)
            
            # Centraliza texto
            extents = ctx.text_extents(letter)
            text_x = center_x - extents.width / 2 - extents.x_bearing
            text_y = center_y + extents.height / 2 - extents.y_bearing
            
            ctx.move_to(text_x, text_y)
            ctx.show_text(letter)
        
        drawing_area.set_draw_func(draw_icon, None)
        return drawing_area
    
    def get_icons_directory(self) -> Path:
        """Retorna o diretório de ícones."""
        return self.icons_dir
    
    def list_supported_icons(self) -> list:
        """Lista os ícones disponíveis localmente."""
        icons = []
        for f in self.icons_dir.iterdir():
            if f.suffix.lower() in ['.png', '.svg', '.jpg', '.jpeg', '.webp']:
                icons.append(f.stem)
        return sorted(icons)
    
    def download_icon(self, symbol: str, url: str) -> bool:
        """Baixa um ícone da URL para o diretório local."""
        try:
            ext = Path(url).suffix or '.png'
            symbol_lower = symbol.lower()
            target_path = self.icons_dir / f"{symbol_lower}{ext}"
            
            # Verifica se já existe
            if target_path.exists():
                return True
            
            # Baixa o ícone
            headers = {'User-Agent': 'CryptoTracker/1.0'}
            request = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = response.read()
                with open(target_path, 'wb') as f:
                    f.write(data)
            
            print(f"[INFO] Downloaded icon for {symbol}: {target_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to download icon for {symbol}: {e}")
            return False


# Singleton
_icon_manager = None

def get_icon_manager() -> IconManager:
    """Retorna o singleton do IconManager."""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager
