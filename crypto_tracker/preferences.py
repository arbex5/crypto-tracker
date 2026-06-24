"""Diálogo de preferências/configurações."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib
from pathlib import Path
from .settings import Settings
from .icons import get_icon_manager


class PreferencesWindow(Adw.PreferencesWindow):
    """Janela de preferências do aplicativo."""

    def __init__(self, parent_window=None, **kwargs):
        super().__init__(
            transient_for=parent_window,
            modal=True,
            **kwargs
        )

        self.settings = Settings()
        self.parent_window = parent_window

        self.set_default_size(600, 550)
        self.set_title("Preferências")

        self._build_ui()

    def _build_ui(self):
        """Constrói a interface de preferências."""
        # Página de API
        api_page = Adw.PreferencesPage.new()
        api_page.set_title("API")
        api_page.set_icon_name("network-workgroup-symbolic")

        # Grupo CMC
        cmc_group = Adw.PreferencesGroup.new()
        cmc_group.set_title("CoinMarketCap API")
        cmc_group.set_description(
            "Insira sua API key do CoinMarketCap para dados premium. "
            "Sem a key, o app usa CoinGecko (gratuito)."
        )

        # API Key row (compatível: Entry dentro de ActionRow)
        self.api_key_row, self.api_key_entry = self._create_entry_row(
            title="API Key",
            text=self.settings.cmc_api_key,
            on_apply=self._on_api_key_apply,
        )
        self.api_key_entry.set_width_chars(35)
        self.api_key_row.add_suffix(self._create_test_button())
        cmc_group.add(self.api_key_row)

        # Toggle para usar CMC (compatível: Switch dentro de ActionRow)
        self.use_cmc_row, self.use_cmc_switch = self._create_switch_row(
            title="Usar CoinMarketCap",
            subtitle="Prioriza CMC quando disponível",
            active=self.settings.use_cmc,
            on_changed=self._on_use_cmc_changed,
        )
        cmc_group.add(self.use_cmc_row)

        api_page.add(cmc_group)

        # Grupo de estatísticas
        stats_group = Adw.PreferencesGroup.new()
        stats_group.set_title("Estatísticas de Uso")

        if self.parent_window and hasattr(self.parent_window, 'api'):
            stats = self.parent_window.api.usage_stats

            calls_row = Adw.ActionRow.new()
            calls_row.set_title("Chamadas hoje")
            calls_row.set_subtitle(f"{stats['calls_today']} / {self.settings.max_daily_calls}")
            stats_group.add(calls_row)

            remaining_row = Adw.ActionRow.new()
            remaining_row.set_title("Créditos restantes hoje")
            remaining_label = Gtk.Label(label=str(stats['remaining_today']))
            remaining_label.add_css_class("numeric")
            if stats['remaining_today'] < 50:
                remaining_label.add_css_class("error")
            remaining_row.add_suffix(remaining_label)
            stats_group.add(remaining_row)

            month_row = Adw.ActionRow.new()
            month_row.set_title("Chamadas este mês")
            month_row.set_subtitle(str(stats['total_month']))
            stats_group.add(month_row)

        api_page.add(stats_group)

        # Grupo de Cache
        cache_group = Adw.PreferencesGroup.new()
        cache_group.set_title("Cache")
        cache_group.set_description(
            "Os dados são cacheados localmente para economizar chamadas à API."
        )

        cache_row = Adw.ActionRow.new()
        cache_row.set_title("Duração do cache")
        cache_row.set_subtitle(f"{self.settings.cache_duration} minutos")
        cache_group.add(cache_row)

        clear_cache_button = Gtk.Button(label="Limpar Cache")
        clear_cache_button.add_css_class("destructive-action")
        clear_cache_button.connect("clicked", self._on_clear_cache)
        clear_cache_button.set_valign(Gtk.Align.CENTER)
        cache_row.add_suffix(clear_cache_button)

        api_page.add(cache_group)

        self.add(api_page)

        # Página de Exibição
        display_page = Adw.PreferencesPage.new()
        display_page.set_title("Exibição")
        display_page.set_icon_name("preferences-desktop-display-symbolic")

        display_group = Adw.PreferencesGroup.new()
        display_group.set_title("Opções de Visualização")
        display_group.set_description(
            "Personalize como os preços e favoritos são exibidos na lista."
        )

        # Switch para mostrar preço em BRL
        self.show_brl_row, self.show_brl_switch = self._create_switch_row(
            title="Mostrar preço em BRL",
            subtitle="Exibe o valor convertido para Reais abaixo do preço em USD",
            active=self.settings.show_brl_price,
            on_changed=self._on_show_brl_changed,
        )
        display_group.add(self.show_brl_row)

        # Botão para limpar favoritos
        favorites_row = Adw.ActionRow.new()
        favorites_row.set_title("Favoritos")
        favorites_row.set_subtitle(
            f"{len(self.settings.favorites)} moeda(s) favorita(s)"
        )

        clear_favorites_button = Gtk.Button(label="Limpar Favoritos")
        clear_favorites_button.add_css_class("destructive-action")
        clear_favorites_button.connect("clicked", self._on_clear_favorites)
        clear_favorites_button.set_valign(Gtk.Align.CENTER)
        favorites_row.add_suffix(clear_favorites_button)
        display_group.add(favorites_row)

        display_page.add(display_group)

        # Grupo de Atualização Automática
        refresh_group = Adw.PreferencesGroup.new()
        refresh_group.set_title("Atualização Automática")
        refresh_group.set_description(
            "Atualiza os dados periodicamente. Chamadas à API só acontecem "
            "quando o cache expira (padrão: 5 minutos), economizando créditos."
        )

        refresh_row = Adw.ActionRow.new()
        refresh_row.set_title("Intervalo de atualização")
        refresh_row.set_subtitle("Atualizar automaticamente a cada")

        refresh_options = [
            (0, "Desativado"),
            (1, "1 minuto"),
            (5, "5 minutos"),
            (15, "15 minutos"),
            (30, "30 minutos"),
            (60, "1 hora"),
        ]
        self._refresh_options = refresh_options

        refresh_dropdown = Gtk.DropDown.new_from_strings([label for _, label in refresh_options])
        current_interval = self.settings.auto_refresh_interval
        selected_index = 0
        for i, (value, _) in enumerate(refresh_options):
            if value == current_interval:
                selected_index = i
                break
        refresh_dropdown.set_selected(selected_index)
        refresh_dropdown.connect("notify::selected", self._on_refresh_interval_changed)
        refresh_dropdown.set_valign(Gtk.Align.CENTER)
        refresh_row.add_suffix(refresh_dropdown)
        refresh_group.add(refresh_row)

        display_page.add(refresh_group)

        # Grupo do Modo Display
        display_mode_group = Adw.PreferencesGroup.new()
        display_mode_group.set_title("Modo Display")
        display_mode_group.set_description(
            "Personalize o comportamento do modo display minimalista."
        )

        # Slider de transparência
        opacity_row = Adw.ActionRow.new()
        opacity_row.set_title("Transparência")
        opacity_row.set_subtitle(f"{int(self.settings.display_opacity * 100)}%")

        opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 30, 100, 5)
        opacity_scale.set_value(self.settings.display_opacity * 100)
        opacity_scale.set_draw_value(True)
        opacity_scale.set_value_pos(Gtk.PositionType.RIGHT)
        opacity_scale.set_size_request(150, -1)
        opacity_scale.connect("value-changed", self._on_opacity_changed, opacity_row)
        opacity_scale.set_valign(Gtk.Align.CENTER)
        opacity_row.add_suffix(opacity_scale)
        display_mode_group.add(opacity_row)

        # Switch para pin no topo
        pin_supported = hasattr(Gtk.Window, 'set_keep_above')
        pin_subtitle = (
            "Fixa a janela do modo display sobre as outras janelas"
            if pin_supported
            else "Indisponível neste ambiente gráfico (Wayland)"
        )
        self.pin_row, self.pin_switch = self._create_switch_row(
            title="Manter no topo",
            subtitle=pin_subtitle,
            active=self.settings.display_pinned and pin_supported,
            on_changed=self._on_pin_changed,
        )
        if not pin_supported:
            self.pin_switch.set_sensitive(False)
        display_mode_group.add(self.pin_row)

        display_page.add(display_mode_group)
        self.add(display_page)

        # Página de Ícones
        icons_page = Adw.PreferencesPage.new()
        icons_page.set_title("Ícones")
        icons_page.set_icon_name("applications-graphics-symbolic")

        icons_group = Adw.PreferencesGroup.new()
        icons_group.set_title("Ícones de Criptomoedas")
        icons_group.set_description(
            "Coloque imagens PNG/SVG das moedas no diretório abaixo. "
            "Nomeie com o símbolo da moeda (ex: btc.png, eth.svg)."
        )

        # Diretório de ícones
        icon_manager = get_icon_manager()
        icons_dir = icon_manager.get_icons_directory()

        dir_row = Adw.ActionRow.new()
        dir_row.set_title("Diretório de ícones")
        dir_row.set_subtitle(str(icons_dir))

        open_dir_button = Gtk.Button(label="Abrir Pasta")
        open_dir_button.connect("clicked", lambda x: self._open_icon_folder(icons_dir))
        open_dir_button.set_valign(Gtk.Align.CENTER)
        dir_row.add_suffix(open_dir_button)

        icons_group.add(dir_row)

        # Ícones disponíveis
        available_icons = icon_manager.list_supported_icons()
        if available_icons:
            icons_list_row = Adw.ActionRow.new()
            icons_list_row.set_title(f"Ícones disponíveis ({len(available_icons)})")
            icons_list_row.set_subtitle(", ".join(available_icons[:10]) +
                ("..." if len(available_icons) > 10 else ""))
            icons_group.add(icons_list_row)

        # Botão para criar pasta
        create_dir_row = Adw.ActionRow.new()
        create_dir_row.set_title("Criar pasta de ícones")
        create_dir_row.set_subtitle("Cria a pasta se não existir")

        create_button = Gtk.Button(label="Criar")
        create_button.connect("clicked", lambda x: self._create_icon_folder(icons_dir))
        create_button.set_valign(Gtk.Align.CENTER)
        create_dir_row.add_suffix(create_button)

        icons_group.add(create_dir_row)

        icons_page.add(icons_group)
        self.add(icons_page)

        # Página Sobre
        about_page = Adw.PreferencesPage.new()
        about_page.set_title("Sobre")
        about_page.set_icon_name("help-about-symbolic")

        about_group = Adw.PreferencesGroup.new()

        # Informações do app
        app_row = Adw.ActionRow.new()
        app_row.set_title("Crypto Tracker")
        app_row.set_subtitle("by Fernando Arbex")

        version_label = Gtk.Label(label="1.2.0")
        version_label.add_css_class("dim-label")
        app_row.add_suffix(version_label)

        about_group.add(app_row)

        # Descrição
        desc_row = Adw.ActionRow.new()
        desc_row.set_title("Descrição")
        desc_row.set_subtitle(
            "Aplicativo para acompanhar criptomoedas em tempo real. "
            "Dados fornecidos por CoinMarketCap e CoinGecko APIs."
        )
        about_group.add(desc_row)

        # Links
        links_group = Adw.PreferencesGroup.new()
        links_group.set_title("Links")

        cmc_link = Adw.ActionRow.new()
        cmc_link.set_title("CoinMarketCap API")
        cmc_link.set_subtitle("Obtenha sua API key gratuita")
        cmc_link.set_activatable(True)
        cmc_link.connect("activated", lambda x: self._open_url("https://coinmarketcap.com/api"))
        links_group.add(cmc_link)

        coingecko_link = Adw.ActionRow.new()
        coingecko_link.set_title("CoinGecko")
        coingecko_link.set_subtitle("API gratuita de criptomoedas")
        coingecko_link.set_activatable(True)
        coingecko_link.connect("activated", lambda x: self._open_url("https://coingecko.com"))
        links_group.add(coingecko_link)

        about_page.add(about_group)
        about_page.add(links_group)

        self.add(about_page)

    def _create_entry_row(
        self,
        title: str,
        text: str,
        on_apply,
    ):
        """Cria uma ActionRow com Gtk.Entry (compatível com versões antigas do Adw)."""
        row = Adw.ActionRow.new()
        row.set_title(title)

        entry = Gtk.Entry()
        entry.set_text(text)
        entry.set_valign(Gtk.Align.CENTER)
        entry.connect("activate", on_apply)

        row.add_suffix(entry)
        return row, entry

    def _create_switch_row(
        self,
        title: str,
        subtitle: str,
        active: bool,
        on_changed,
    ):
        """Cria uma ActionRow com Gtk.Switch (compatível com versões antigas do Adw)."""
        row = Adw.ActionRow.new()
        row.set_title(title)
        row.set_subtitle(subtitle)

        switch = Gtk.Switch()
        switch.set_active(active)
        switch.set_valign(Gtk.Align.CENTER)
        switch.connect("notify::active", on_changed)

        row.add_suffix(switch)
        return row, switch

    def _create_test_button(self) -> Gtk.Button:
        """Cria botão de teste de API."""
        button = Gtk.Button(label="Testar")
        button.set_tooltip_text("Testa a conexão com a API")
        button.connect("clicked", self._on_test_api)
        button.set_valign(Gtk.Align.CENTER)
        return button

    def _on_test_api(self, button):
        """Testa a conexão com a API CMC."""
        key = self.api_key_entry.get_text().strip()
        if not key:
            self._show_toast("Digite uma API key primeiro!")
            return

        self._show_toast("Testando API...")

        # Testa em thread separada
        import threading
        def test():
            try:
                import urllib.request
                url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=1"
                headers = {'X-CMC_PRO_API_KEY': key}
                request = urllib.request.Request(url, headers=headers)

                with urllib.request.urlopen(request, timeout=10) as response:
                    data = response.read()
                    result = data.decode('utf-8')
                    GLib.idle_add(lambda: self._show_toast("✅ API funcionando!"))

            except Exception as e:
                GLib.idle_add(lambda: self._show_toast(f"❌ Erro: {str(e)[:50]}"))

        thread = threading.Thread(target=test, daemon=True)
        thread.start()

    def _on_api_key_apply(self, entry):
        """Salva a API key quando aplicado."""
        key = entry.get_text().strip()
        self.settings.cmc_api_key = key

        if key:
            self._show_toast("API Key salva!")
        else:
            self._show_toast("API Key removida")
            self.use_cmc_switch.set_active(False)

    def _on_use_cmc_changed(self, switch, param):
        """Ativa/desativa uso do CMC."""
        active = switch.get_active()

        if active and not self.settings.cmc_api_key:
            switch.set_active(False)
            self._show_toast("Configure uma API Key primeiro!")
            return

        self.settings.use_cmc = active
        status = "ativado" if active else "desativado"
        self._show_toast(f"CMC {status}")

    def _on_show_brl_changed(self, switch, param):
        """Ativa/desativa exibição do preço em BRL."""
        active = switch.get_active()
        self.settings.show_brl_price = active

        # Atualiza a janela principal se estiver aberta
        if self.parent_window:
            self.parent_window._load_data(force_refresh=True)

        status = "ativado" if active else "desativado"
        self._show_toast(f"Preço em BRL {status}")

    def _on_clear_favorites(self, button):
        """Limpa todos os favoritos."""
        self.settings.favorites = []

        if self.parent_window:
            self.parent_window._load_data(force_refresh=True)

        self._show_toast("Favoritos limpos!")

    def _on_opacity_changed(self, scale, row):
        """Atualiza a transparência do modo display."""
        value = scale.get_value() / 100.0
        self.settings.display_opacity = value
        row.set_subtitle(f"{int(value * 100)}%")

        # Aplica em tempo real se estiver no modo display
        if self.parent_window and self.parent_window.glass_mode:
            self.parent_window.set_opacity(value)

    def _on_refresh_interval_changed(self, dropdown, param):
        """Altera o intervalo de atualização automática."""
        selected = dropdown.get_selected()
        if 0 <= selected < len(self._refresh_options):
            value, label = self._refresh_options[selected]
            self.settings.auto_refresh_interval = value
            if self.parent_window:
                self.parent_window._setup_auto_refresh()
            self._show_toast(f"Atualização automática: {label}")

    def _on_pin_changed(self, switch, param):
        """Ativa/desativa pin no topo."""
        active = switch.get_active()
        self.settings.display_pinned = active

        # Aplica em tempo real se estiver no modo display
        if self.parent_window and self.parent_window.glass_mode:
            self.parent_window._set_keep_above_safe(active)

        status = "fixada" if active else "desfixada"
        self._show_toast(f"Janela {status}")

    def _on_clear_cache(self, button):
        """Limpa o cache."""
        from .cache import CacheManager
        cache = CacheManager()
        cache.clear()
        self._show_toast("Cache limpo!")

    def _open_icon_folder(self, path: Path):
        """Abre a pasta de ícones."""
        import subprocess
        try:
            subprocess.run(["xdg-open", str(path)], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._show_toast("Crie a pasta primeiro!")

    def _create_icon_folder(self, path: Path):
        """Cria a pasta de ícones."""
        path.mkdir(parents=True, exist_ok=True)
        self._show_toast(f"Pasta criada: {path}")
        self._open_icon_folder(path)

    def _open_url(self, url: str):
        """Abre uma URL no navegador."""
        import subprocess
        try:
            subprocess.run(["xdg-open", url], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._show_toast("Não foi possível abrir o navegador")

    def _show_toast(self, message: str):
        """Mostra um toast na janela de preferências."""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.add_toast(toast)
