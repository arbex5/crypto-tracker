#!/bin/bash
#
# Script de instalação do Crypto Tracker by Fernando Arbex
# Instala o aplicativo GTK4 no sistema Linux
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de utilidade
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Detecta o gerenciador de pacotes
detect_package_manager() {
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        PKG_INSTALL="sudo apt install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        PKG_INSTALL="sudo pacman -S --noconfirm"
    elif command -v zypper &> /dev/null; then
        PKG_MANAGER="zypper"
        PKG_INSTALL="sudo zypper install -y"
    else
        print_error "Gerenciador de pacotes não suportado. Instale manualmente:"
        print_info "  - python3-gi (PyGObject)"
        print_info "  - libadwaita"
        print_info "  - python3-cairo (opcional, para gráficos)"
        return 1
    fi
    
    print_info "Gerenciador de pacotes detectado: $PKG_MANAGER"
    return 0
}

# Verifica dependências
check_dependencies() {
    print_info "Verificando dependências..."
    
    local missing_deps=()
    
    # Verifica Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Verifica pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("python3-pip")
    fi
    
    # Verifica PyGObject (gtk4)
    if ! python3 -c "import gi; gi.require_version('Gtk', '4.0')" 2>/dev/null; then
        case $PKG_MANAGER in
            apt)
                missing_deps+=("python3-gi" "gir1.2-gtk-4.0" "gir1.2-adw-1")
                ;;
            dnf)
                missing_deps+=("python3-gobject" "gtk4" "libadwaita")
                ;;
            pacman)
                missing_deps+=("python-gobject" "gtk4" "libadwaita")
                ;;
            zypper)
                missing_deps+=("python3-gobject" "gtk4" "libadwaita")
                ;;
        esac
    fi
    
    # Verifica Cairo (para gráficos sparkline)
    if ! python3 -c "import cairo" 2>/dev/null; then
        case $PKG_MANAGER in
            apt)
                missing_deps+=("python3-cairo")
                ;;
            dnf)
                missing_deps+=("python3-cairo")
                ;;
            pacman)
                missing_deps+=("python-cairo")
                ;;
            zypper)
                missing_deps+=("python3-cairo")
                ;;
        esac
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_warning "Dependências faltando: ${missing_deps[*]}"
        print_info "Instalando dependências..."
        
        if ! detect_package_manager; then
            exit 1
        fi
        
        $PKG_INSTALL "${missing_deps[@]}" || {
            print_error "Falha ao instalar dependências"
            exit 1
        }
    else
        print_success "Todas as dependências estão instaladas"
    fi
}

# Instala o aplicativo
install_app() {
    print_info "Instalando Crypto Tracker by Fernando Arbex..."
    
    # Diretório de instalação
    INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/share/crypto-tracker}"
    
    # Cria diretórios
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/.local/share/applications"
    mkdir -p "$HOME/.local/share/crypto-tracker/icons"
    
    # Copia arquivos do aplicativo
    print_info "Copiando arquivos para $INSTALL_DIR..."
    cp -r crypto_tracker "$INSTALL_DIR/"
    
    # Copia ícones padrão (se existirem no projeto)
    if [ -d "icons" ] && [ "$(ls -A icons 2>/dev/null)" ]; then
        cp -r icons/* "$HOME/.local/share/crypto-tracker/icons/" 2>/dev/null || true
        print_info "Ícones padrão copiados"
    fi
    
    # Instala o ícone do aplicativo
    ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
    mkdir -p "$ICON_DIR"
    if [ -f "icons/crypto-tracker.svg" ]; then
        cp "icons/crypto-tracker.svg" "$ICON_DIR/crypto-tracker.svg"
        gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
        print_info "Ícone do aplicativo instalado"
    fi
    
    # Cria o script de execução
    cat > "$HOME/.local/bin/crypto-tracker" << 'EOF'
#!/bin/bash
# Crypto Tracker - by Fernando Arbex
# Launcher script for Crypto Tracker

# Adiciona o diretório da aplicação ao PYTHONPATH
export PYTHONPATH="${HOME}/.local/share/crypto-tracker:${PYTHONPATH}"

# Executa o aplicativo
python3 -m crypto_tracker.main "$@"
EOF
    
    chmod +x "$HOME/.local/bin/crypto-tracker"
    
    # Cria o arquivo .desktop
    cat > "$HOME/.local/share/applications/crypto-tracker.desktop" << EOF
[Desktop Entry]
Name=Crypto Tracker
Comment=Acompanhe criptomoedas em tempo real by Fernando Arbex
Exec=$HOME/.local/bin/crypto-tracker
Type=Application
Terminal=false
Icon=crypto-tracker
Categories=Office;Finance;Network;
Keywords=crypto;bitcoin;ethereum;criptomoedas;preço;coinmarketcap;coingecko;
StartupNotify=true
X-GNOME-SingleWindow=true
EOF
    
    # Atualiza o cache de aplicações
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi
    
    print_success "Crypto Tracker instalado com sucesso!"
}

# Instalação do sistema (requer root)
install_system() {
    print_info "Instalando Crypto Tracker no sistema..."
    
    INSTALL_DIR="/usr/local/share/crypto-tracker"
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo cp -r crypto_tracker "$INSTALL_DIR/"
    sudo mkdir -p "$INSTALL_DIR/icons"
    
    # Copia ícones padrão (se existirem no projeto)
    if [ -d "icons" ] && [ "$(ls -A icons 2>/dev/null)" ]; then
        sudo cp -r icons/* "$INSTALL_DIR/icons/" 2>/dev/null || true
        print_info "Ícones padrão copiados"
    fi
    
    # Instala o ícone do aplicativo
    if [ -f "icons/crypto-tracker.svg" ]; then
        sudo mkdir -p "/usr/local/share/icons/hicolor/scalable/apps"
        sudo cp "icons/crypto-tracker.svg" "/usr/local/share/icons/hicolor/scalable/apps/crypto-tracker.svg"
        sudo gtk-update-icon-cache -f /usr/local/share/icons/hicolor 2>/dev/null || true
        print_info "Ícone do aplicativo instalado"
    fi
    
    # Script de execução
    sudo tee /usr/local/bin/crypto-tracker > /dev/null << 'EOF'
#!/bin/bash
# Crypto Tracker - by Fernando Arbex
export PYTHONPATH="/usr/local/share/crypto-tracker:${PYTHONPATH}"
python3 -m crypto_tracker.main "$@"
EOF
    
    sudo chmod +x /usr/local/bin/crypto-tracker
    
    # Arquivo .desktop
    sudo tee /usr/local/share/applications/crypto-tracker.desktop > /dev/null << 'EOF'
[Desktop Entry]
Name=Crypto Tracker
Comment=Acompanhe criptomoedas em tempo real by Fernando Arbex
Exec=crypto-tracker
Type=Application
Terminal=false
Icon=crypto-tracker
Categories=Office;Finance;Network;
Keywords=crypto;bitcoin;ethereum;criptomoedas;preço;coinmarketcap;coingecko;
StartupNotify=true
X-GNOME-SingleWindow=true
EOF
    
    sudo update-desktop-database 2>/dev/null || true
    
    print_success "Crypto Tracker instalado no sistema!"
}

# Desinstala o aplicativo
uninstall() {
    print_info "Desinstalando Crypto Tracker..."
    
    # Remove arquivos locais
    rm -rf "$HOME/.local/share/crypto-tracker"
    rm -f "$HOME/.local/bin/crypto-tracker"
    rm -f "$HOME/.local/share/applications/crypto-tracker.desktop"
    
    # Remove cache e configurações
    rm -rf "$HOME/.cache/crypto-tracker"
    rm -rf "$HOME/.config/crypto-tracker"
    
    # Remove arquivos do sistema (se existirem)
    if [ -f "/usr/local/bin/crypto-tracker" ]; then
        sudo rm -rf "/usr/local/share/crypto-tracker"
        sudo rm -f "/usr/local/bin/crypto-tracker"
        sudo rm -f "/usr/local/share/applications/crypto-tracker.desktop"
    fi
    
    # Atualiza cache
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    
    print_success "Crypto Tracker desinstalado!"
}

# Mostra ajuda
show_help() {
    echo "Uso: $0 [OPÇÃO]"
    echo ""
    echo "Crypto Tracker by Fernando Arbex"
    echo ""
    echo "Opções:"
    echo "  install      Instala o aplicativo localmente (padrão)"
    echo "  system       Instala no sistema (requer root/sudo)"
    echo "  uninstall    Remove o aplicativo"
    echo "  help         Mostra esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0                    # Instalação local"
    echo "  $0 install            # Instalação local"
    echo "  sudo $0 system        # Instalação no sistema"
    echo "  $0 uninstall          # Desinstala"
    echo ""
    echo "Configuração da API:"
    echo "  Para usar CoinMarketCap, configure sua API key em:"
    echo "  Menu > Preferências > API"
    echo ""
    echo "Ícones de criptomoedas:"
    echo "  Coloque imagens PNG/SVG em: ~/.local/share/crypto-tracker/icons/"
    echo "  Nomeie com o símbolo da moeda (ex: btc.png, eth.svg)"
    echo ""
    echo "Suporte:"
    echo "  coinmarketcap.com/api"
    echo "  coingecko.com"
}

# Main
main() {
    echo "========================================="
    echo "     Crypto Tracker by Fernando Arbex"
    echo "========================================="
    echo ""
    
    case "${1:-install}" in
        install)
            check_dependencies
            install_app
            echo ""
            print_success "Instalação concluída!"
            echo ""
            print_info "Para executar:"
            print_info "  - Via terminal: crypto-tracker"
            print_info "  - Via menu: procure por 'Crypto Tracker'"
            echo ""
            print_info "Modos de visualização:"
            print_info "  - Modo Compacto: ícone de 'reveal' na header bar"
            print_info "  - Modo Glass: ícone de 'fog' na header bar (transparente/sticky)"
            echo ""
            print_info "Para configurar CoinMarketCap API:"
            print_info "  1. Obtenha key gratuita em: coinmarketcap.com/api"
            print_info "  2. Abra o app e vá em: Menu > Preferências > API"
            print_info "  3. Cole sua API key, ative e teste"
            echo ""
            print_info "Para adicionar ícones:"
            print_info "  - Menu > Preferências > Ícones > Abrir Pasta"
            print_info "  - Coloque imagens .png/.svg com nome do símbolo (btc.png)"
            echo ""
            print_info "Atalhos de teclado:"
            print_info "  Ctrl+R / F5      - Atualizar dados"
            print_info "  Ctrl+F           - Buscar"
            print_info "  Ctrl+T           - Modo Compacto"
            print_info "  Ctrl+Comma       - Preferências"
            print_info "  Ctrl+Q / Ctrl+W  - Sair"
            ;;
        system)
            if [ "$EUID" -ne 0 ]; then
                print_error "Instalação do sistema requer root. Use: sudo $0 system"
                exit 1
            fi
            check_dependencies
            install_system
            ;;
        uninstall|remove)
            uninstall
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Opção desconhecida: $1"
            show_help
            exit 1
            ;;
    esac
}

# Executa o main
main "$@"
