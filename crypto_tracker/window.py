"""Janela principal do aplicativo."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from typing import List, Optional
import threading
from .models import Crypto
from .api import CryptoAPI, APIWorker
from .widgets import CryptoRow, HeaderRow, DisplayWidget
from .preferences import PreferencesWindow
from .settings import Settings


class CryptoWindow(Adw.ApplicationWindow):
    """Janela principal do aplicativo Crypto Tracker."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.api = CryptoAPI()
        self.settings = Settings()
        self.cryptos: List[Crypto] = []
        self.filtered_cryptos: List[Crypto] = []
        self.current_worker: Optional[APIWorker] = None
        self._brl_worker: Optional[threading.Thread] = None
        self.compact_mode = False
        self.glass_mode = False
        self.display_widget = None
        self.display_asset = self.settings.display_asset
        self._glass_css_provider = None
        self._normal_size = (self.settings.window_width, self.settings.window_height)
        self._in_special_mode = False
        self._block_size_save = False
        self._window_presented = False
        self._supports_keep_above = hasattr(Gtk.Window, 'set_keep_above')
        self._refresh_timer_id = None
        self._has_initial_data = False
        self._normal_title_widget = None
        
        self._build_ui()
        self._load_data()
        self._setup_auto_refresh()
    
    def _build_ui(self):
        """Constrói a interface do usuário."""
        # Tamanho inicial - usa o salvo ou o padrão
        width = max(400, self.settings.window_width)
        height = max(300, self.settings.window_height)
        self.set_default_size(width, height)
        self.set_title("Crypto Tracker")
        
        # Permite redimensionar para tamanhos menores
        self.set_resizable(True)
        
        # Salva o tamanho quando a janela for redimensionada ou fechada
        self.connect("notify::default-width", self._on_window_size_changed)
        self.connect("notify::default-height", self._on_window_size_changed)
        self.connect("close-request", self._on_close_request)
        self.connect("realize", self._on_window_realized)
        
        # Header bar
        self.main_header = Adw.HeaderBar()
        self.main_header.set_show_end_title_buttons(True)
        header = self.main_header
        
        title_label = Gtk.Label(label="💰 Crypto Tracker")
        title_label.add_css_class("title")
        header.set_title_widget(title_label)
        
        # Botão modo compacto/glass
        self.compact_button = Gtk.ToggleButton()
        self.compact_button.set_icon_name("view-reveal-symbolic")
        self.compact_button.set_tooltip_text("Modo Compacto/Widget (Ctrl+T)")
        self.compact_button.connect("toggled", self._on_compact_toggled)
        header.pack_start(self.compact_button)
        
        # Botão modo display
        self.glass_button = Gtk.ToggleButton()
        self.glass_button.set_icon_name("weather-fog-symbolic")
        self.glass_button.set_tooltip_text("Modo Display Minimalista")
        self.glass_button.connect("toggled", self._on_glass_toggled)
        header.pack_start(self.glass_button)
        
        # Menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menu")
        
        menu = Gio.Menu.new()
        menu.append("Preferências", "app.preferences")
        menu.append("Sobre", "app.about")
        
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)
        
        # Botão de atualizar
        self.refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        self.refresh_button.set_tooltip_text("Atualizar dados (Ctrl+R)")
        self.refresh_button.connect("clicked", self._on_refresh_clicked)
        header.pack_end(self.refresh_button)
        
        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Barra de busca
        self.search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.search_box.set_margin_top(12)
        self.search_box.set_margin_bottom(8)
        self.search_box.set_margin_start(12)
        self.search_box.set_margin_end(12)
        
        self.search_entry = Gtk.SearchEntry()
        # Compatibilidade: versões novas do GTK expõem set_placeholder_text
        if hasattr(self.search_entry, "set_placeholder_text"):
            self.search_entry.set_placeholder_text("Buscar...")
        else:
            self.search_entry.set_property("placeholder-text", "Buscar...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self._on_search_changed)
        
        self.search_box.append(self.search_entry)
        
        # Status bar
        self.status_label = Gtk.Label()
        self.status_label.add_css_class("dim-label")
        self.status_label.add_css_class("caption")
        
        self.status_spinner = Gtk.Spinner()
        self.status_spinner.set_margin_start(8)
        self.status_spinner.set_visible(False)
        
        self.status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.status_box.set_halign(Gtk.Align.CENTER)
        self.status_box.set_margin_bottom(6)
        self.status_box.append(self.status_label)
        self.status_box.append(self.status_spinner)
        
        # Cabeçalho da lista
        self.header_row = HeaderRow(compact=False)
        
        # Lista de criptomoedas
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.set_margin_start(12)
        self.listbox.set_margin_end(12)
        self.listbox.set_margin_bottom(12)
        
        # Container com header + lista
        self.list_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.list_container.append(self.header_row)
        self.list_container.append(self.listbox)

        # Scrolled window para a lista
        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.set_vexpand(True)
        self._scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._scrolled.set_propagate_natural_width(False)
        self._scrolled.set_propagate_natural_height(False)
        self._scrolled.set_child(self.list_container)
        
        # Loading spinner
        self.spinner = Gtk.Spinner()
        self.spinner.set_margin_top(20)
        self.spinner.set_margin_bottom(20)
        
        self._spinner_center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._spinner_center.set_vexpand(True)
        self._spinner_center.set_valign(Gtk.Align.CENTER)
        self._spinner_center.set_halign(Gtk.Align.CENTER)
        self._spinner_center.append(self.spinner)
        
        loading_label = Gtk.Label(label="Carregando...")
        loading_label.add_css_class("dim-label")
        loading_label.set_margin_top(8)
        self._spinner_center.append(loading_label)
        
        self.stack = Gtk.Stack()
        self.stack.add_named(self._scrolled, "list")
        self.stack.add_named(self._spinner_center, "loading")
        
        # Container para o modo display (preenchido depois)
        self.display_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.display_container.set_vexpand(True)
        self.stack.add_named(self.display_container, "display")
        
        self.stack.set_visible_child_name("loading")
        
        # Monta a interface
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._content.append(self.search_box)
        self._content.append(self.status_box)
        self._content.append(self.stack)
        
        # Layout principal (ToolbarView em versões novas, Box em versões antigas)
        if hasattr(Adw, "ToolbarView"):
            self._main_layout = Adw.ToolbarView()
            self._main_layout.add_top_bar(header)
            self._main_layout.set_content(self._content)
        else:
            self._main_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self._main_layout.append(header)
            self._main_layout.append(self._content)

        # Toast overlay para notificações
        self.toast_overlay = Adw.ToastOverlay()
        self.toast_overlay.set_child(self._main_layout)
        self.set_content(self.toast_overlay)
    
    def _setup_auto_refresh(self):
        """Configura o timer de atualização automática periódica."""
        # Remove timer anterior se existir
        if self._refresh_timer_id is not None:
            GLib.source_remove(self._refresh_timer_id)
            self._refresh_timer_id = None

        interval_minutes = self.settings.auto_refresh_interval
        if interval_minutes <= 0:
            return

        interval_seconds = interval_minutes * 60
        self._refresh_timer_id = GLib.timeout_add_seconds(
            interval_seconds,
            self._on_auto_refresh_timeout
        )
        print(f"[DEBUG] Auto refresh enabled every {interval_minutes} min(s)", flush=True)

    def _on_auto_refresh_timeout(self):
        """Callback do timer de atualização automática."""
        print("[DEBUG] Auto refresh triggered", flush=True)
        self._load_data(force_refresh=False)
        return True  # Mantém o timer ativo

    def _load_data(self, force_refresh: bool = False):
        """Carrega os dados das criptomoedas em uma thread separada."""
        # Cancela worker anterior se existir
        if self.current_worker and self.current_worker.is_alive():
            self.current_worker.cancel()

        # Mostra spinner discreto na status bar
        self.status_spinner.set_visible(True)
        self.status_spinner.start()
        self.status_label.set_text("Atualizando...")

        # Só mostra tela de loading em tela cheia se nunca tivermos carregado dados
        if not self._has_initial_data:
            self.spinner.start()
            self.stack.set_visible_child_name("loading")

        # Cria e inicia o worker
        self.current_worker = APIWorker(
            self.api,
            self._on_data_loaded,
            limit=50,
            force_refresh=force_refresh
        )
        self.current_worker.start()
    
    def _on_data_loaded(self, cryptos: List[Crypto]):
        """Callback chamado quando os dados são carregados."""
        self._has_initial_data = True

        # Para spinner discreto
        self.status_spinner.stop()
        self.status_spinner.set_visible(False)
        self.spinner.stop()

        # Aplica estado de favorito dos dados salvos
        for crypto in cryptos:
            crypto.is_favorite = self.settings.is_favorite(crypto.id)

        # Ordena: favoritos primeiro, depois por ranking
        self.cryptos = self._sort_cryptos(cryptos)

        # Reaplica busca ativa, se houver
        query = self.search_entry.get_text().strip()
        if query:
            self.filtered_cryptos = self.api.search_cryptos(query, self.cryptos)
        else:
            self.filtered_cryptos = self.cryptos

        self._update_list()
        self._update_display()

        # Mantém a página atual visível (não troca para loading)
        if self.glass_mode:
            self._apply_display_layout()
        else:
            self._apply_full_layout()
        
        # Atualiza status
        stats = self.api.usage_stats
        if self.api.last_error:
            self.status_label.set_text(
                f"⚠️ {self.api.last_error} | "
                f"Chamadas: {stats['calls_today']}"
            )
            self._show_toast(f"Erro: {self.api.last_error}", "warning")
        else:
            source = "CMC" if self.settings.can_use_cmc() else "CoinGecko"
            self.status_label.set_text(
                f"✅ {len(cryptos)} cryptos via {source} | "
                f"Calls: {stats['calls_today']}"
            )
        
        # Busca taxa BRL em segundo plano se necessário
        if self.settings.show_brl_price and not self.api.usd_brl_rate:
            self._fetch_brl_rate_async()
        
        return False
    
    def _fetch_brl_rate_async(self):
        """Busca taxa USD/BRL em segundo plano e atualiza a UI."""
        if self._brl_worker and self._brl_worker.is_alive():
            return
        
        def fetch():
            try:
                rate = self.api.fetch_usd_brl_rate()
                if rate:
                    GLib.idle_add(self._on_brl_rate_ready)
            except Exception as e:
                print(f"[DEBUG] Async BRL fetch error: {e}")
        
        self._brl_worker = threading.Thread(target=fetch, daemon=True)
        self._brl_worker.start()
    
    def _on_brl_rate_ready(self):
        """Callback quando a taxa BRL está disponível."""
        self.api._apply_usd_brl_rate(self.cryptos)
        self.api._apply_usd_brl_rate(self.filtered_cryptos)
        self._update_list()
        self._show_toast("Cotação USD/BRL atualizada", "info")
        return False
    
    def _sort_cryptos(self, cryptos: List[Crypto]) -> List[Crypto]:
        """Ordena criptomoedas: favoritos primeiro, depois por ranking."""
        return sorted(
            cryptos,
            key=lambda c: (
                not c.is_favorite,  # Favoritos primeiro (False < True)
                c.market_cap_rank   # Depois por ranking
            )
        )
    
    def _on_favorite_toggle(self, crypto: Crypto, is_favorite: bool):
        """Callback quando o usuário alterna o favorito."""
        if is_favorite:
            self.settings.add_favorite(crypto.id)
        else:
            self.settings.remove_favorite(crypto.id)
        
        # Reordena e atualiza a lista
        self.cryptos = self._sort_cryptos(self.cryptos)
        
        # Aplica filtro de busca se houver
        query = self.search_entry.get_text().strip()
        if query:
            self.filtered_cryptos = self._sort_cryptos(
                self.api.search_cryptos(query, self.cryptos)
            )
        else:
            self.filtered_cryptos = self.cryptos
        
        self._update_list()
    
    def _update_list(self):
        """Atualiza a lista de criptomoedas."""
        # Remove widgets antigos
        while True:
            child = self.listbox.get_first_child()
            if child is None:
                break
            self.listbox.remove(child)
        
        # Adiciona novos itens
        max_items = 5 if self.compact_mode else len(self.filtered_cryptos)
        for i, crypto in enumerate(self.filtered_cryptos):
            if i >= max_items:
                break
            row = CryptoRow(
                crypto,
                compact=self.compact_mode,
                show_brl_price=self.settings.show_brl_price,
                on_favorite_toggle=self._on_favorite_toggle
            )
            self.listbox.append(row)
    
    def _get_display_crypto(self) -> Optional[Crypto]:
        """Retorna a criptomoeda selecionada para o modo display."""
        target = self.display_asset.lower()
        
        for crypto in self.cryptos:
            if crypto.symbol.lower() == target or crypto.id.lower() == target:
                return crypto
        
        # Fallback para BTC ou primeira crypto
        for crypto in self.cryptos:
            if crypto.symbol.lower() == "btc":
                return crypto
        
        return self.cryptos[0] if self.cryptos else None
    
    def _update_display(self):
        """Atualiza o widget do modo display."""
        crypto = self._get_display_crypto()
        if not crypto:
            return
        
        # Limpa container
        while True:
            child = self.display_container.get_first_child()
            if child is None:
                break
            self.display_container.remove(child)
        
        # Cria novo widget
        self.display_widget = DisplayWidget(
            crypto,
            available_cryptos=self.cryptos,
            on_asset_change=self._on_display_asset_changed,
            on_back=self._on_display_back,
            on_pin_toggle=self._on_display_pin_toggled,
            on_quick_assets_reordered=self._on_quick_assets_reordered,
            is_pinned=self.settings.display_pinned,
            pin_supported=self._supports_keep_above,
            quick_assets=self.settings.display_quick_assets
        )
        self.display_container.append(self.display_widget)
    
    def _on_display_asset_changed(self, symbol: str):
        """Troca o ativo do modo display."""
        self.display_asset = symbol
        self.settings.display_asset = symbol
        self._update_display()

    def _on_quick_assets_reordered(self, quick_assets: list):
        """Salva a nova ordem dos ativos de acesso rápido."""
        self.settings.display_quick_assets = quick_assets
    
    def _on_display_back(self):
        """Volta ao modo completo."""
        self.glass_button.set_active(False)
    
    def _on_display_pin_toggled(self, is_pinned: bool):
        """Alterna o pin no topo do modo display."""
        print(f"[DEBUG] _on_display_pin_toggled is_pinned={is_pinned}", flush=True)
        self.settings.display_pinned = is_pinned
        self._set_keep_above_safe(is_pinned)
        status = "fixada" if is_pinned else "desfixada"
        self._show_toast(f"Janela {status}", "info")
    
    def _on_search_changed(self, entry: Gtk.SearchEntry):
        """Filtra a lista quando o texto de busca muda."""
        query = entry.get_text().strip()
        
        if not query:
            self.filtered_cryptos = self.cryptos
        else:
            self.filtered_cryptos = self.api.search_cryptos(query, self.cryptos)
        
        self._update_list()
        
        # Atualiza contador
        count = len(self.filtered_cryptos)
        total = len(self.cryptos)
        if query:
            self.status_label.set_text(f"🔍 {count} de {total} cryptos")
        else:
            source = "CMC" if self.settings.can_use_cmc() else "CoinGecko"
            self.status_label.set_text(f"✅ {count} cryptos via {source}")
    
    def _on_refresh_clicked(self, button: Gtk.Button):
        """Atualiza os dados quando o botão é clicado."""
        self._load_data(force_refresh=True)
        self._show_toast("Atualizando...", "info")
    
    def _on_compact_toggled(self, button):
        """Alterna modo compacto."""
        active = button.get_active()
        print(f"[DEBUG] _on_compact_toggled active={active}, glass_mode={self.glass_mode}", flush=True)

        # Se estiver ativando compacto e display estiver ativo, sai do display
        if active and self.glass_mode:
            self.glass_button.set_active(False)

        self.compact_mode = active

        # Atualiza header da lista
        parent = self.header_row.get_parent()
        if parent:
            parent.remove(self.header_row)

        self.header_row = HeaderRow(compact=self.compact_mode)
        self.list_container.prepend(self.header_row)

        # Atualiza lista
        self._update_list()

        # Ajusta layout e tamanho
        if self.compact_mode:
            self._enter_special_mode()
            # Remove o título da header bar para liberar espaço horizontal
            self._normal_title_widget = self.main_header.get_title_widget()
            self.main_header.set_title_widget(None)
            # Aplica layout compacto simplificado
            self._apply_compact_layout()
            self._show_toast("Modo Compacto ativado", "info")
        else:
            self._leave_special_mode()
            # Restaura o título da header bar
            if self._normal_title_widget is not None:
                self.main_header.set_title_widget(self._normal_title_widget)
                self._normal_title_widget = None
            # Restaura layout completo
            self._apply_full_layout()
            self._restore_normal_size()
            self._show_toast("Modo Normal", "info")

        GLib.idle_add(self._debug_sizes)
    
    def _on_glass_toggled(self, button):
        """Alterna modo display minimalista / modo completo."""
        active = button.get_active()
        print(f"[DEBUG] _on_glass_toggled active={active}, compact_mode={self.compact_mode}", flush=True)

        # Se estiver ativando display e compacto estiver ativo, desativa compacto
        if active and self.compact_mode:
            self.compact_button.set_active(False)

        self.glass_mode = active

        if self.glass_mode:
            self._enable_glass_mode()
            self._show_toast("Modo Display ativado", "info")
        else:
            self._disable_glass_mode()
            self._show_toast("Modo Completo", "info")

        GLib.idle_add(self._debug_sizes)

    def _enable_glass_mode(self):
        """Ativa modo display minimalista."""
        print(f"[DEBUG] _enable_glass_mode pinned={self.settings.display_pinned}", flush=True)
        self._enter_special_mode()

        # Aplica transparência configurada
        self.set_opacity(self.settings.display_opacity)

        # Aplica pin (sempre por cima)
        self._set_keep_above_safe(self.settings.display_pinned)

        # Adiciona classe CSS para glass effect
        self._add_glass_css()

        # Remove decoração
        self.set_decorated(False)

        # Aplica layout do display
        self._apply_display_layout()

        # GTK4 não permite redimensionar uma janela já visível via API.
        # Reduzimos o size-request do conteúdo para que o WM permita que o
        # usuário redimensione manualmente para baixo.
        self.display_container.set_size_request(280, 240)

    def _disable_glass_mode(self):
        """Desativa modo display e volta ao modo completo."""
        print("[DEBUG] _disable_glass_mode", flush=True)
        self.set_opacity(1.0)
        self._set_keep_above_safe(False)
        self.set_decorated(True)

        # Remove CSS personalizado
        self._remove_glass_css()

        # Limpa restrição de tamanho do display
        self.display_container.set_size_request(-1, -1)

        self._leave_special_mode()

        # Restaura layout completo
        self._apply_full_layout()
    
    def _set_keep_above_safe(self, keep_above: bool):
        """Define keep_above se a API do GTK suportar (nem sempre disponível no GTK4/Wayland)."""
        if self._supports_keep_above and hasattr(self, 'set_keep_above'):
            try:
                self.set_keep_above(keep_above)
            except Exception as e:
                print(f"[DEBUG] set_keep_above failed: {e}", flush=True)
        else:
            print(f"[DEBUG] keep_above not supported by this GTK/window manager", flush=True)

    def _on_window_realized(self, window):
        """Marca que a janela já foi apresentada ao window manager."""
        self._window_presented = True

    def _block_size_saving(self):
        """Bloqueia salvamento de tamanho por um curto período."""
        self._block_size_save = True
        GLib.timeout_add(500, self._unblock_size_save)

    def _unblock_size_save(self):
        """Desbloqueia salvamento de tamanho."""
        self._block_size_save = False
        return False

    def _enter_special_mode(self):
        """Salva o tamanho atual antes de entrar em modo display/compacto."""
        if not self._in_special_mode:
            try:
                width = self.get_width()
                height = self.get_height()
                if width > 0 and height > 0:
                    self._normal_size = (width, height)
            except Exception:
                pass
        self._in_special_mode = True
        self._block_size_saving()

    def _leave_special_mode(self):
        """Marca que saiu do modo display/compacto."""
        self._in_special_mode = False
        self._block_size_saving()

    def _restore_normal_size(self):
        """Restaura o tamanho normal salvo nas configurações."""
        width, height = self._normal_size
        width = max(400, width)
        height = max(300, height)
        self.set_default_size(width, height)

    def _add_glass_css(self):
        """Adiciona CSS do modo glass."""
        self._remove_glass_css()

        self._glass_css_provider = Gtk.CssProvider()
        css_data = """
            window {
                background-color: alpha(@window_bg_color, 0.88);
            }
            .boxed-list {
                background-color: alpha(@card_bg_color, 0.75);
            }
        """
        if hasattr(self._glass_css_provider, "load_from_string"):
            self._glass_css_provider.load_from_string(css_data)
        else:
            self._glass_css_provider.load_from_data(css_data.encode("utf-8"))

        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self._glass_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
    
    def _remove_glass_css(self):
        """Remove CSS do modo glass."""
        if self._glass_css_provider:
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.remove_provider_for_display(
                    display,
                    self._glass_css_provider
                )
            self._glass_css_provider = None
    
    def _apply_compact_layout(self):
        """Aplica layout compacto (apenas header + lista)."""
        print("[DEBUG] _apply_compact_layout", flush=True)
        # Garante que estamos no layout principal
        self._restore_main_layout()

        # Esconde container do display para não impor tamanho mínimo
        self.display_container.set_visible(False)

        # Esconde elementos não essenciais
        self.search_box.set_visible(False)
        self.status_box.set_visible(False)
        self.glass_button.set_visible(False)
        self.refresh_button.set_visible(False)

        # Garante que a lista está visível
        self.stack.set_visible_child_name("list")

        # Permite que a lista encolha no modo compacto
        self.listbox.set_size_request(260, 180)
        self._scrolled.set_size_request(260, 180)

    def _apply_display_layout(self):
        """Aplica layout do modo display (esconde header, busca, status)."""
        print("[DEBUG] _apply_display_layout", flush=True)
        # Restaura layout principal se estiver no compacto
        if self.toast_overlay.get_child() != self._main_layout:
            self._restore_main_layout()

        # Esconde header, busca e status
        self.main_header.set_visible(False)
        self.search_box.set_visible(False)
        self.status_box.set_visible(False)

        # Limpa restrições de tamanho do modo compacto
        self.listbox.set_size_request(-1, -1)
        self._scrolled.set_size_request(-1, -1)

        # Mostra container do display
        self.display_container.set_visible(True)

        # Mostra display se já tiver dados
        if self.cryptos:
            self._update_display()
            self.stack.set_visible_child_name("display")
        else:
            self.stack.set_visible_child_name("loading")

    def _restore_main_layout(self):
        """Restaura a header bar e o layout principal no toast overlay."""
        # Garante que a header bar está no layout principal
        if self.main_header.get_parent() is None:
            if hasattr(self._main_layout, 'add_top_bar'):
                self._main_layout.add_top_bar(self.main_header)
            else:
                self._main_layout.prepend(self.main_header)

        # Garante que o scrolled está no stack
        if self._scrolled.get_parent() is None:
            self.stack.add_named(self._scrolled, "list")

        # Mostra botões da header bar novamente
        self.glass_button.set_visible(True)
        self.refresh_button.set_visible(True)

        # Restaura layout principal no toast overlay
        self.toast_overlay.set_child(self._main_layout)

    def _apply_full_layout(self):
        """Aplica layout completo (mostra header, busca, status)."""
        print("[DEBUG] _apply_full_layout", flush=True)
        # Restaura layout principal
        self._restore_main_layout()

        # Mostra header, busca e status
        self.main_header.set_visible(True)
        self.search_box.set_visible(True)
        self.status_box.set_visible(True)

        # Esconde container do display para não impor tamanho mínimo
        self.display_container.set_visible(False)

        # Limpa restrições de tamanho do modo compacto
        self.listbox.set_size_request(-1, -1)
        self._scrolled.set_size_request(-1, -1)

        # Volta para lista
        self.stack.set_visible_child_name("list")
    
    def show_preferences(self):
        """Mostra a janela de preferências."""
        prefs = PreferencesWindow(parent_window=self)
        prefs.present()
    
    def _on_about_clicked(self, button=None):
        """Mostra o diálogo sobre."""
        dialog = Adw.AboutWindow(
            transient_for=self,
            application_name="Crypto Tracker",
            developer_name="Fernando Arbex",
            version="1.2.0",
            comments="Acompanhe criptomoedas em tempo real com dados da CoinMarketCap e CoinGecko",
            website="https://github.com/crypto-tracker",
            issue_url="https://github.com/crypto-tracker/issues",
            license_type=Gtk.License.MIT_X11,
            copyright="© 2024 Fernando Arbex"
        )
        
        dialog.add_credit_section("Desenvolvido por", ["Fernando Arbex"])
        dialog.add_credit_section("Dados", ["CoinMarketCap API", "CoinGecko API"])
        dialog.add_credit_section("Tecnologias", ["GTK4", "Libadwaita", "Python 3"])
        
        dialog.present()
    
    def _on_window_size_changed(self, window, param):
        """Salva o tamanho da janela quando redimensionada."""
        # Não salva em modos especiais (display/compacto) ou durante transições
        if self._in_special_mode or self._block_size_save:
            return

        try:
            width = self.get_width()
            height = self.get_height()

            if width > 0 and height > 0:
                self.settings.window_width = width
                self.settings.window_height = height
                self._normal_size = (width, height)
                print(f"[DEBUG] size saved {width}x{height}", flush=True)
        except Exception:
            pass

    def _on_close_request(self, window):
        """Salva o tamanho da janela ao fechar."""
        # Não salva em modos especiais (display/compacto)
        if not self._in_special_mode:
            try:
                width = self.get_width()
                height = self.get_height()

                if width > 0 and height > 0:
                    self.settings.window_width = width
                    self.settings.window_height = height
            except Exception:
                pass

        return False  # Permite o fechamento
    
    def _debug_sizes(self):
        """Imprime tamanhos dos widgets para diagnóstico."""
        def measure(widget, name):
            try:
                min_w, nat_w, _, _ = widget.measure(Gtk.Orientation.HORIZONTAL, -1)
                min_h, nat_h, _, _ = widget.measure(Gtk.Orientation.VERTICAL, -1)
                print(f"[DEBUG SIZE] {name}: min={min_w}x{min_h} nat={nat_w}x{nat_h}", flush=True)
            except Exception as e:
                print(f"[DEBUG SIZE] {name}: error {e}", flush=True)

        measure(self, "Window")
        measure(self.toast_overlay, "ToastOverlay")
        measure(self.main_header, "HeaderBar")
        measure(self._content, "Content")
        measure(self.stack, "Stack")
        measure(self._scrolled, "Scrolled")
        measure(self._spinner_center, "SpinnerCenter")
        measure(self.display_container, "DisplayContainer")
        measure(self.list_container, "ListContainer")
        measure(self.header_row, "HeaderRow")
        measure(self.listbox, "ListBox")

    def _show_toast(self, message: str, toast_type: str = "info"):
        """Mostra uma notificação toast."""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        
        if toast_type == "warning":
            toast.set_priority(Adw.ToastPriority.HIGH)
        
        self.toast_overlay.add_toast(toast)
