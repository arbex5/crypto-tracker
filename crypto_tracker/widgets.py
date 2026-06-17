"""Widgets customizados para o aplicativo."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from typing import Optional, List
from gi.repository import Gtk, Gdk, GObject, GLib
from .models import Crypto
from .icons import get_icon_manager
import math

# Importa cairo de forma segura
try:
    import cairo
except ImportError:
    cairo = None


class SparklineWidget(Gtk.DrawingArea):
    """Widget que desenha um gráfico sparkline."""
    
    def __init__(self, width: int = 100, height: int = 35):
        super().__init__()
        
        self.set_content_width(width)
        self.set_content_height(height)
        self._data: list = []
        self._is_positive: bool = True
        
        self.set_draw_func(self._draw_sparkline, None)
    
    def set_data(self, data: list, is_positive: bool = True):
        """Define os dados do sparkline."""
        # Limita a quantidade de pontos para performance
        if len(data) > 100:
            step = len(data) // 100
            data = data[::step][:100]
        
        self._data = data if data else []
        self._is_positive = is_positive
        self.queue_draw()
    
    def _draw_sparkline(self, area, ctx, width, height, user_data):
        """Desenha o gráfico."""
        if not self._data or len(self._data) < 2:
            return
        
        if not cairo:
            return
        
        # Configurações
        padding = 2
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        
        # Calcula min e max
        min_val = min(self._data)
        max_val = max(self._data)
        
        if max_val == min_val:
            max_val = min_val + 1
        
        # Cor baseada na tendência
        if self._is_positive:
            color = (0.15, 0.75, 0.45)  # Verde
        else:
            color = (0.92, 0.25, 0.30)  # Vermelho
        
        # Cria o caminho do gráfico
        ctx.set_line_width(2)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgb(*color)
        
        # Desenha a linha
        points = []
        for i, value in enumerate(self._data):
            # Normaliza para o espaço do gráfico
            x = padding + (i / (len(self._data) - 1)) * graph_width
            y = padding + graph_height - ((value - min_val) / (max_val - min_val)) * graph_height
            points.append((x, y))
            
            if i == 0:
                ctx.move_to(x, y)
            else:
                ctx.line_to(x, y)
        
        ctx.stroke()
        
        # Adiciona gradiente suave abaixo da linha
        if len(points) > 1:
            ctx.save()
            
            ctx.move_to(points[0][0], points[0][1])
            for x, y in points[1:]:
                ctx.line_to(x, y)
            
            # Fecha o caminho para o gradiente
            ctx.line_to(points[-1][0], padding + graph_height)
            ctx.line_to(points[0][0], padding + graph_height)
            ctx.close_path()
            
            # Gradiente transparente
            gradient = cairo.LinearGradient(0, padding, 0, padding + graph_height)
            gradient.add_color_stop_rgba(0, color[0], color[1], color[2], 0.25)
            gradient.add_color_stop_rgba(1, color[0], color[1], color[2], 0.0)
            
            ctx.set_source(gradient)
            ctx.fill()
            
            ctx.restore()


class CompactCryptoRow(Gtk.ListBoxRow):
    """Row compacta para modo glass/widget."""
    
    def __init__(self, crypto: Crypto, compact: bool = False):
        super().__init__()
        self.crypto = crypto
        self.set_activatable(True)
        self._build_ui(compact)
    
    def _build_ui(self, compact: bool):
        """Constrói a interface compacta."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Ícone
        icon_manager = get_icon_manager()
        icon_widget = icon_manager.create_icon_with_fallback(self.crypto.symbol, 24)
        box.append(icon_widget)
        
        # Nome e símbolo
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        name_box.set_hexpand(True)
        
        name_label = Gtk.Label(label=f"{self.crypto.name}")
        name_label.set_xalign(0)
        name_label.add_css_class("caption")
        name_label.set_ellipsize(3)  # Pango.EllipsizeMode.END
        name_box.append(name_label)
        
        symbol_label = Gtk.Label(label=self.crypto.symbol_upper)
        symbol_label.set_xalign(0)
        symbol_label.add_css_class("dim-label")
        symbol_label.add_css_class("caption")
        name_box.append(symbol_label)
        
        box.append(name_box)
        
        # Preço
        price_label = Gtk.Label(label=self.crypto.formatted_price)
        price_label.set_xalign(1)
        price_label.add_css_class("numeric")
        price_label.add_css_class("caption")
        box.append(price_label)
        
        # Variação 24h (apenas essa no modo compacto)
        change_label = Gtk.Label(label=f"{self.crypto.price_change_percentage_24h:+.2f}%")
        change_label.set_xalign(1)
        change_label.set_width_chars(8)
        change_label.add_css_class("numeric")
        change_label.add_css_class("caption")
        
        if self.crypto.is_positive_24h:
            change_label.add_css_class("success")
        else:
            change_label.add_css_class("error")
        
        box.append(change_label)
        
        self.set_child(box)


class CryptoRow(Gtk.ListBoxRow):
    """Row widget para exibir uma criptomoeda na lista - estilo CoinMarketCap."""
    
    def __init__(self, crypto: Crypto, compact: bool = False, show_brl_price: bool = False, on_favorite_toggle=None):
        super().__init__()
        self.crypto = crypto
        self.compact = compact
        self.show_brl_price = show_brl_price
        self.on_favorite_toggle = on_favorite_toggle
        self.set_activatable(True)
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da row."""
        if self.compact:
            return self._build_compact_ui()
        else:
            return self._build_full_ui()
    
    def _build_full_ui(self):
        """Interface completa no estilo CMC."""
        # Container principal - usa scroll horizontal se necessário
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        scroll.set_overlay_scrolling(True)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_size_request(800, -1)  # Largura mínima
        
        # Botão de favorito (estrela)
        favorite_button = Gtk.Button()
        favorite_button.set_icon_name(
            "starred-symbolic" if self.crypto.is_favorite else "non-starred-symbolic"
        )
        favorite_button.set_tooltip_text(
            "Remover dos favoritos" if self.crypto.is_favorite else "Adicionar aos favoritos"
        )
        favorite_button.add_css_class("flat")
        favorite_button.add_css_class("circular")
        if self.crypto.is_favorite:
            favorite_button.add_css_class("success")
        favorite_button.connect("clicked", self._on_favorite_clicked)
        box.append(favorite_button)
        
        # Rank
        rank_label = Gtk.Label(label=f"#{self.crypto.market_cap_rank}")
        rank_label.set_width_chars(3)
        rank_label.set_xalign(0.5)
        rank_label.add_css_class("dim-label")
        rank_label.add_css_class("caption")
        box.append(rank_label)
        
        # Ícone
        icon_manager = get_icon_manager()
        icon_widget = icon_manager.create_icon_with_fallback(self.crypto.symbol, 28)
        box.append(icon_widget)
        
        # Nome e símbolo
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        name_box.set_hexpand(False)
        name_box.set_size_request(150, -1)
        
        name_inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        name_label = Gtk.Label(label=self.crypto.name)
        name_label.set_xalign(0)
        name_label.add_css_class("caption-heading")
        name_label.set_ellipsize(3)
        name_inner.append(name_label)
        
        symbol_label = Gtk.Label(label=self.crypto.symbol_upper)
        symbol_label.set_xalign(0)
        symbol_label.add_css_class("dim-label")
        symbol_label.add_css_class("caption")
        name_inner.append(symbol_label)
        
        name_box.append(name_inner)
        box.append(name_box)
        
        # Preço (USD + BRL opcional)
        price_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        price_box.set_size_request(90, -1)
        
        if self.show_brl_price and self.crypto.brl_price:
            # BRL como preço principal (mais evidente)
            brl_label = Gtk.Label(label=self.crypto.formatted_brl_price)
            brl_label.set_xalign(1)
            brl_label.add_css_class("caption-heading")
            brl_label.add_css_class("numeric")
            brl_label.add_css_class("success")
            price_box.append(brl_label)
            
            usd_label = Gtk.Label(label=self.crypto.formatted_price)
            usd_label.set_xalign(1)
            usd_label.add_css_class("dim-label")
            usd_label.add_css_class("numeric")
            usd_label.add_css_class("caption")
            price_box.append(usd_label)
        else:
            price_label = Gtk.Label(label=self.crypto.formatted_price)
            price_label.set_width_chars(12)
            price_label.set_xalign(1)
            price_label.add_css_class("caption-heading")
            price_label.add_css_class("numeric")
            price_box.append(price_label)
        
        box.append(price_box)
        
        # Variação 1h
        change_1h = Gtk.Label(label=self.crypto.formatted_change_1h)
        change_1h.set_width_chars(9)
        change_1h.set_xalign(1)
        change_1h.add_css_class("numeric")
        change_1h.add_css_class("caption")
        
        if self.crypto.is_positive_1h:
            change_1h.add_css_class("success")
        else:
            change_1h.add_css_class("error")
        
        box.append(change_1h)
        
        # Variação 24h
        change_24h = Gtk.Label(label=self.crypto.formatted_change_24h)
        change_24h.set_width_chars(9)
        change_24h.set_xalign(1)
        change_24h.add_css_class("numeric")
        change_24h.add_css_class("caption")
        
        if self.crypto.is_positive_24h:
            change_24h.add_css_class("success")
        else:
            change_24h.add_css_class("error")
        
        box.append(change_24h)
        
        # Variação 7d
        change_7d = Gtk.Label(label=self.crypto.formatted_change_7d)
        change_7d.set_width_chars(9)
        change_7d.set_xalign(1)
        change_7d.add_css_class("numeric")
        change_7d.add_css_class("caption")
        
        if self.crypto.is_positive_7d:
            change_7d.add_css_class("success")
        else:
            change_7d.add_css_class("error")
        
        box.append(change_7d)
        
        # Sparkline
        if cairo and self.crypto.sparkline_7d and len(self.crypto.sparkline_7d) > 5:
            sparkline = SparklineWidget(width=90, height=32)
            sparkline.set_data(
                self.crypto.sparkline_7d,
                self.crypto.is_positive_7d
            )
            box.append(sparkline)
        else:
            # Espaço vazio
            spacer = Gtk.Box()
            spacer.set_size_request(90, -1)
            box.append(spacer)
        
        scroll.set_child(box)
        self.set_child(scroll)
    
    def _build_compact_ui(self):
        """Interface compacta."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Ícone
        icon_manager = get_icon_manager()
        icon_widget = icon_manager.create_icon_with_fallback(self.crypto.symbol, 24)
        box.append(icon_widget)
        
        # Nome
        name_label = Gtk.Label(label=f"{self.crypto.symbol_upper}")
        name_label.set_xalign(0)
        name_label.set_hexpand(True)
        name_label.add_css_class("caption-heading")
        box.append(name_label)
        
        # Preço
        price_label = Gtk.Label(label=self.crypto.formatted_price)
        price_label.set_xalign(1)
        price_label.add_css_class("numeric")
        price_label.add_css_class("caption")
        box.append(price_label)
        
        # Variação
        change_label = Gtk.Label(label=f"{self.crypto.price_change_percentage_24h:+.1f}%")
        change_label.set_xalign(1)
        change_label.set_width_chars(7)
        change_label.add_css_class("numeric")
        change_label.add_css_class("caption")
        
        if self.crypto.is_positive_24h:
            change_label.add_css_class("success")
        else:
            change_label.add_css_class("error")
        
        box.append(change_label)
        
        self.set_child(box)
    
    def _on_favorite_clicked(self, button):
        """Alterna o estado de favorito."""
        self.crypto.is_favorite = not self.crypto.is_favorite
        
        # Atualiza ícone
        button.set_icon_name(
            "starred-symbolic" if self.crypto.is_favorite else "non-starred-symbolic"
        )
        button.set_tooltip_text(
            "Remover dos favoritos" if self.crypto.is_favorite else "Adicionar aos favoritos"
        )
        
        # Atualiza classes CSS
        if self.crypto.is_favorite:
            button.add_css_class("success")
        else:
            button.remove_css_class("success")
        
        # Notifica a janela
        if self.on_favorite_toggle:
            self.on_favorite_toggle(self.crypto, self.crypto.is_favorite)


class DisplayWidget(Gtk.Box):
    """Widget de display minimalista estilo dashboard para modo glass."""
    
    def __init__(self, crypto: Crypto, available_cryptos: list = None, on_asset_change=None, on_back=None, on_pin_toggle=None, is_pinned: bool = False, pin_supported: bool = True):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.crypto = crypto
        self.available_cryptos = available_cryptos or []
        self.on_asset_change = on_asset_change
        self.on_back = on_back
        self.on_pin_toggle = on_pin_toggle
        self.is_pinned = is_pinned
        self.pin_supported = pin_supported
        
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_vexpand(True)
        
        self._build_ui()
    
    def _get_crypto_by_symbol(self, symbol: str) -> Optional[Crypto]:
        """Retorna crypto pelo símbolo."""
        target = symbol.lower()
        for c in self.available_cryptos:
            if c.symbol.lower() == target:
                return c
        return None
    
    def _build_ui(self):
        # Overlay container para botão discreto de voltar
        overlay = Gtk.Overlay()
        overlay.set_vexpand(True)
        
        # Conteúdo principal
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_vexpand(True)
        
        # Header com ícone/nome à esquerda, preço no centro e espaço à direita para o botão
        header = Gtk.CenterBox()
        header.set_margin_end(40)  # Espaço para o botão de modo completo no overlay
        
        # Ícone e nome à esquerda
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        icon_manager = get_icon_manager()
        icon_widget = icon_manager.create_icon_with_fallback(self.crypto.symbol, 56)
        left_box.append(icon_widget)
        
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        name_box.set_halign(Gtk.Align.START)
        
        name_label = Gtk.Label(label=self.crypto.name)
        name_label.set_xalign(0)
        name_label.add_css_class("title-2")
        name_box.append(name_label)
        
        symbol_label = Gtk.Label(label=self.crypto.symbol_upper)
        symbol_label.set_xalign(0)
        symbol_label.add_css_class("dim-label")
        symbol_label.add_css_class("caption")
        name_box.append(symbol_label)
        
        left_box.append(name_box)
        header.set_start_widget(left_box)
        
        # Preço com seta de tendência no centro
        price_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        price_box.set_halign(Gtk.Align.CENTER)
        price_box.set_valign(Gtk.Align.CENTER)
        
        trend_icon = Gtk.Label(label="▲" if self.crypto.is_positive_24h else "▼")
        trend_icon.add_css_class("success" if self.crypto.is_positive_24h else "error")
        trend_icon.add_css_class("title-1")
        price_box.append(trend_icon)
        
        price_label = Gtk.Label(label=self.crypto.formatted_price)
        price_label.add_css_class("title-1")
        price_label.add_css_class("numeric")
        price_box.append(price_label)
        
        header.set_center_widget(price_box)
        content.append(header)
        
        # Variações 1h / 24h / 7d
        changes_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        changes_box.set_halign(Gtk.Align.CENTER)
        changes_box.set_margin_top(4)
        changes_box.set_margin_bottom(4)
        
        for label, value, is_positive in [
            ("1h", self.crypto.price_change_percentage_1h, self.crypto.is_positive_1h),
            ("24h", self.crypto.price_change_percentage_24h, self.crypto.is_positive_24h),
            ("7d", self.crypto.price_change_percentage_7d, self.crypto.is_positive_7d),
        ]:
            change_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            change_box.set_halign(Gtk.Align.CENTER)
            
            period_label = Gtk.Label(label=label)
            period_label.add_css_class("caption")
            period_label.add_css_class("dim-label")
            change_box.append(period_label)
            
            value_label = Gtk.Label(label=f"{value:+.2f}%")
            value_label.add_css_class("caption-heading")
            value_label.add_css_class("numeric")
            value_label.add_css_class("success" if is_positive else "error")
            change_box.append(value_label)
            
            changes_box.append(change_box)
        
        content.append(changes_box)
        
        # Gráfico grande dos últimos 7 dias com min/max
        if cairo and self.crypto.sparkline_7d and len(self.crypto.sparkline_7d) > 5:
            min_val = min(self.crypto.sparkline_7d)
            max_val = max(self.crypto.sparkline_7d)
            
            chart_overlay = Gtk.Overlay()
            chart_overlay.set_vexpand(True)
            chart_overlay.set_valign(Gtk.Align.FILL)
            chart_overlay.set_margin_top(4)
            chart_overlay.set_margin_bottom(4)
            
            sparkline = SparklineWidget(width=300, height=180)
            sparkline.set_data(
                self.crypto.sparkline_7d,
                self.crypto.is_positive_7d
            )
            sparkline.set_vexpand(True)
            sparkline.set_valign(Gtk.Align.FILL)
            chart_overlay.set_child(sparkline)
            
            # Label do valor máximo (topo esquerda)
            max_label = Gtk.Label(label=f"${max_val:,.2f}")
            max_label.add_css_class("caption")
            max_label.add_css_class("numeric")
            max_label.add_css_class("dim-label")
            max_label.set_halign(Gtk.Align.START)
            max_label.set_valign(Gtk.Align.START)
            max_label.set_margin_start(4)
            max_label.set_margin_top(2)
            chart_overlay.add_overlay(max_label)
            
            # Label do valor mínimo (base esquerda)
            min_label = Gtk.Label(label=f"${min_val:,.2f}")
            min_label.add_css_class("caption")
            min_label.add_css_class("numeric")
            min_label.add_css_class("dim-label")
            min_label.set_halign(Gtk.Align.START)
            min_label.set_valign(Gtk.Align.END)
            min_label.set_margin_start(4)
            min_label.set_margin_bottom(2)
            chart_overlay.add_overlay(min_label)
            
            content.append(chart_overlay)
        
        # Botões de troca de ativo com preço e variação 1h
        assets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        assets_box.set_halign(Gtk.Align.CENTER)
        assets_box.set_margin_top(6)
        assets_box.set_valign(Gtk.Align.END)
        
        for symbol in ["BTC", "ETH", "SOL", "XRP"]:
            btn = self._create_asset_button(symbol)
            assets_box.append(btn)
        
        content.append(assets_box)
        
        overlay.set_child(content)
        
        # Container para botões do overlay (canto superior direito)
        overlay_buttons = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        overlay_buttons.set_halign(Gtk.Align.END)
        overlay_buttons.set_valign(Gtk.Align.START)
        overlay_buttons.set_margin_top(4)
        overlay_buttons.set_margin_end(4)
        
        # Botão Pin
        pin_btn = Gtk.Button()
        pin_btn.set_icon_name("pin-symbolic" if self.is_pinned else "pin-off-symbolic")
        if self.pin_supported:
            pin_btn.set_tooltip_text("Desafixar" if self.is_pinned else "Fixar no topo")
            pin_btn.connect("clicked", self._on_pin_clicked)
        else:
            pin_btn.set_tooltip_text("Fixar no topo não é suportado neste ambiente (Wayland)")
            pin_btn.set_sensitive(False)
        pin_btn.add_css_class("flat")
        pin_btn.add_css_class("circular")
        overlay_buttons.append(pin_btn)
        
        # Botão discreto para voltar ao modo completo
        back_btn = Gtk.Button()
        back_btn.set_icon_name("view-fullscreen-symbolic")
        back_btn.set_tooltip_text("Modo Completo")
        back_btn.add_css_class("flat")
        back_btn.add_css_class("circular")
        back_btn.connect("clicked", self._on_back_clicked)
        overlay_buttons.append(back_btn)
        
        overlay.add_overlay(overlay_buttons)
        
        self.append(overlay)
    
    def _on_pin_clicked(self, button):
        """Alterna o estado de pin."""
        self.is_pinned = not self.is_pinned
        button.set_icon_name("pin-symbolic" if self.is_pinned else "pin-off-symbolic")
        button.set_tooltip_text("Desafixar" if self.is_pinned else "Fixar no topo")
        if self.on_pin_toggle:
            self.on_pin_toggle(self.is_pinned)
    
    def _create_asset_button(self, symbol: str) -> Gtk.Button:
        """Cria botão de ativo mostrando preço e variação 1h."""
        crypto = self._get_crypto_by_symbol(symbol)
        is_current = symbol.lower() == self.crypto.symbol.lower()
        
        # Container vertical para o conteúdo do botão
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_start(6)
        box.set_margin_end(6)
        
        # Símbolo
        symbol_label = Gtk.Label(label=symbol)
        symbol_label.add_css_class("caption-heading")
        box.append(symbol_label)
        
        if crypto:
            # Preço
            price_label = Gtk.Label(label=crypto.formatted_price)
            price_label.add_css_class("caption")
            price_label.add_css_class("numeric")
            box.append(price_label)
            
            # Variação 1h
            change_label = Gtk.Label(label=f"{crypto.price_change_percentage_1h:+.2f}%")
            change_label.add_css_class("caption")
            change_label.add_css_class("numeric")
            change_label.add_css_class("success" if crypto.is_positive_1h else "error")
            box.append(change_label)
        else:
            # Sem dados
            na_label = Gtk.Label(label="—")
            na_label.add_css_class("caption")
            na_label.add_css_class("dim-label")
            box.append(na_label)
        
        btn = Gtk.Button()
        btn.set_child(box)
        btn.add_css_class("asset-button")
        if is_current:
            btn.add_css_class("suggested-action")
        btn.connect("clicked", self._on_asset_button_clicked, symbol.lower())
        
        return btn
    
    def _on_asset_button_clicked(self, button, symbol):
        if self.on_asset_change:
            self.on_asset_change(symbol)
    
    def _on_back_clicked(self, button):
        if self.on_back:
            self.on_back()


class HeaderRow(Gtk.Box):
    """Row de cabeçalho para a lista."""
    
    def __init__(self, compact: bool = False):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.compact = compact
        
        if compact:
            self._build_compact()
        else:
            self._build_full()
    
    def _build_full(self):
        """Cabeçalho completo."""
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_size_request(800, -1)
        
        # Espaço para estrela de favorito
        fav_spacer = Gtk.Box()
        fav_spacer.set_size_request(28, -1)
        self.append(fav_spacer)
        
        # Rank
        rank = Gtk.Label(label="#")
        rank.set_width_chars(3)
        rank.set_xalign(0.5)
        rank.add_css_class("dim-label")
        rank.add_css_class("caption")
        self.append(rank)
        
        # Espaço para ícone
        spacer = Gtk.Box()
        spacer.set_size_request(28, -1)
        self.append(spacer)
        
        # Nome
        name = Gtk.Label(label="Nome")
        name.set_xalign(0)
        name.set_hexpand(False)
        name.set_size_request(150, -1)
        name.add_css_class("dim-label")
        name.add_css_class("caption")
        self.append(name)
        
        # Preço
        price = Gtk.Label(label="Preço")
        price.set_width_chars(12)
        price.set_xalign(1)
        price.add_css_class("dim-label")
        price.add_css_class("caption")
        self.append(price)
        
        # 1h
        h1 = Gtk.Label(label="1h")
        h1.set_width_chars(9)
        h1.set_xalign(1)
        h1.add_css_class("dim-label")
        h1.add_css_class("caption")
        self.append(h1)
        
        # 24h
        h24 = Gtk.Label(label="24h")
        h24.set_width_chars(9)
        h24.set_xalign(1)
        h24.add_css_class("dim-label")
        h24.add_css_class("caption")
        self.append(h24)
        
        # 7d
        d7 = Gtk.Label(label="7d")
        d7.set_width_chars(9)
        d7.set_xalign(1)
        d7.add_css_class("dim-label")
        d7.add_css_class("caption")
        self.append(d7)
        
        # 7 dias (sparkline)
        spark = Gtk.Label(label="7 dias")
        spark.set_width_chars(10)
        spark.set_xalign(0.5)
        spark.add_css_class("dim-label")
        spark.add_css_class("caption")
        self.append(spark)
    
    def _build_compact(self):
        """Cabeçalho compacto."""
        self.set_margin_top(4)
        self.set_margin_bottom(4)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Espaço ícone
        spacer = Gtk.Box()
        spacer.set_size_request(24, -1)
        self.append(spacer)
        
        # Nome
        name = Gtk.Label(label="Moeda")
        name.set_xalign(0)
        name.set_hexpand(True)
        name.add_css_class("dim-label")
        name.add_css_class("caption")
        self.append(name)
        
        # Preço
        price = Gtk.Label(label="Preço")
        price.set_xalign(1)
        price.add_css_class("dim-label")
        price.add_css_class("caption")
        self.append(price)
        
        # 24h
        h24 = Gtk.Label(label="24h")
        h24.set_xalign(1)
        h24.set_width_chars(7)
        h24.add_css_class("dim-label")
        h24.add_css_class("caption")
        self.append(h24)
