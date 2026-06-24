#!/usr/bin/env python3
"""
Crypto Tracker - Aplicativo GTK4 para acompanhar criptomoedas em tempo real.

Um aplicativo moderno para Linux usando GTK4 e Libadwaita que exibe
os preços das principais criptomoedas usando APIs da CoinMarketCap e CoinGecko.

Desenvolvido por: Fernando Arbex
"""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gio, Gdk
from .window import CryptoWindow


# Compatibilidade com diferentes versões do GTK4/Libadwaita
APPLICATION_FLAGS = getattr(
    Gio.ApplicationFlags, "DEFAULT_FLAGS", Gio.ApplicationFlags.FLAGS_NONE
)


class CryptoApp(Adw.Application):
    """Aplicativo principal Crypto Tracker by Fernando Arbex."""

    def __init__(self):
        super().__init__(
            application_id="com.fernandoarbex.CryptoTracker",
            flags=APPLICATION_FLAGS
        )
        
        self.window = None
        
        # Ações do aplicativo
        self._setup_actions()
    
    def _setup_actions(self):
        """Configura as ações do aplicativo."""
        # Ação de sair
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit)
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Control>q", "<Control>w"])
        
        # Ação de atualizar
        refresh_action = Gio.SimpleAction.new("refresh", None)
        refresh_action.connect("activate", self._on_refresh)
        self.add_action(refresh_action)
        self.set_accels_for_action("app.refresh", ["<Control>r", "F5"])
        
        # Ação de busca
        search_action = Gio.SimpleAction.new("search", None)
        search_action.connect("activate", self._on_search)
        self.add_action(search_action)
        self.set_accels_for_action("app.search", ["<Control>f"])
        
        # Ação de modo compacto
        compact_action = Gio.SimpleAction.new("compact", None)
        compact_action.connect("activate", self._on_compact)
        self.add_action(compact_action)
        self.set_accels_for_action("app.compact", ["<Control>t"])
        
        # Ação de preferências
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self._on_preferences)
        self.add_action(prefs_action)
        self.set_accels_for_action("app.preferences", ["<Control>comma"])
        
        # Ação sobre
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)
    
    def do_activate(self):
        """Ativa o aplicativo."""
        # Cria a janela se não existir
        if not self.window:
            self.window = CryptoWindow(application=self)
        
        # Apresenta a janela
        self.window.present()
    
    def _on_quit(self, action, param):
        """Callback para ação de sair."""
        self.quit()
    
    def _on_refresh(self, action, param):
        """Callback para ação de atualizar."""
        if self.window:
            self.window._load_data(force_refresh=True)
    
    def _on_search(self, action, param):
        """Callback para ação de busca."""
        if self.window and self.window.search_entry:
            self.window.search_entry.grab_focus()
    
    def _on_compact(self, action, param):
        """Callback para modo compacto."""
        if self.window and self.window.compact_button:
            self.window.compact_button.set_active(
                not self.window.compact_button.get_active()
            )
    
    def _on_preferences(self, action, param):
        """Callback para ação de preferências."""
        if self.window:
            self.window.show_preferences()
    
    def _on_about(self, action, param):
        """Callback para ação sobre."""
        if self.window:
            self.window._on_about_clicked()


def setup_css():
    """Configura o CSS customizado do aplicativo."""
    css_provider = Gtk.CssProvider()
    css_data = """
        .success {
            color: #26a17b;
            font-weight: 600;
        }

        .error {
            color: #ea3943;
            font-weight: 600;
        }

        .numeric {
            font-feature-settings: "tnum";
            font-variant-numeric: tabular-nums;
        }

        .crypto-row {
            transition: background-color 0.2s;
        }

        .crypto-row:hover {
            background-color: alpha(@theme_fg_color, 0.05);
        }

        /* Estilo para sparkline */
        .sparkline-positive {
            color: #26a17b;
        }

        .sparkline-negative {
            color: #ea3943;
        }

        /* Compact mode adjustments */
        .compact-row {
            padding: 4px 8px;
        }

        /* Botões de ativo no modo display */
        .asset-button {
            border-radius: 8px;
            padding: 4px 8px;
            min-width: 70px;
        }

        .asset-button.suggested-action {
            background-color: alpha(@accent_bg_color, 0.85);
            color: @accent_fg_color;
        }
    """

    # Compatibilidade: versões novas usam load_from_string, antigas load_from_data
    if hasattr(css_provider, "load_from_string"):
        css_provider.load_from_string(css_data)
    else:
        css_provider.load_from_data(css_data.encode("utf-8"))

    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def main():
    """Ponto de entrada do aplicativo."""
    # Configura CSS
    setup_css()
    
    # Cria e executa o aplicativo
    app = CryptoApp()
    
    return app.run(sys.argv)


def run():
    """Função de conveniência para executar o aplicativo."""
    return main()


if __name__ == "__main__":
    sys.exit(main())
