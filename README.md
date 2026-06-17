# 💰 Crypto Tracker

**by Fernando Arbex**

Aplicativo GTK4 para Linux que mostra criptomoedas em tempo real usando as APIs CoinMarketCap e CoinGecko.

![GTK4](https://img.shields.io/badge/GTK-4.0-blue)
![Libadwaita](https://img.shields.io/badge/Libadwaita-1.0-purple)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Funcionalidades

- 📊 **Top 50 criptomoedas** por market cap
- 💵 **Preços em tempo real** em USD e BRL
- 📈 **Variações**: 1h %, 24h % e 7 dias %
- 📉 **Gráficos sparkline** dos últimos 7 dias
- 🇧🇷 **USD/BRL na posição 0** da lista, com gráfico e variações
- ⭐ **Favoritos** com estrela e ordenação automática no topo
- 🔍 **Busca em tempo real** por nome ou símbolo
- 🖼️ **Ícones de criptomoedas** (locais ou baixados)
- 📱 **Modo Compacto** - lista simplificada
- 🖥️ **Modo Display** - dashboard minimalista estilo ticker
- 🪟 **Transparência e Pin** - ajuste a opacidade e fixe a janela no topo
- 🔄 **Atualização manual**
- 💾 **Cache local** para economizar chamadas à API
- 🔑 **Suporte a CoinMarketCap API** (opcional)
- 🆓 **Fallback para CoinGecko** (gratuito)

## 📋 Requisitos

- Python 3.8+
- GTK 4.0
- Libadwaita
- PyGObject (python3-gi)
- python3-cairo (para gráficos sparkline)

## 🚀 Instalação

### Instalação rápida

```bash
# Clone o repositório
git clone https://github.com/fernandoarbex/crypto-tracker.git
cd crypto-tracker

# Execute o instalador
./install.sh
```

### Instalação manual

```bash
# Instale as dependências (exemplo para Debian/Ubuntu)
sudo apt install python3-gi python3-pip python3-cairo gir1.2-gtk-4.0 gir1.2-adw-1

# Copie os arquivos
mkdir -p ~/.local/share/crypto-tracker
cp -r crypto_tracker ~/.local/share/crypto-tracker/

# Crie o launcher
chmod +x ~/.local/share/crypto-tracker/crypto_tracker/main.py
ln -sf ~/.local/share/crypto-tracker/crypto_tracker/main.py ~/.local/bin/crypto-tracker
```

## 🎮 Uso

```bash
# Via terminal
crypto-tracker

# Ou procure "Crypto Tracker" no menu de aplicativos
```

### Modos de Visualização

| Modo | Descrição | Como ativar |
|------|-----------|-------------|
| **Normal** | Interface completa com todas as colunas | Padrão |
| **Compacto** | Apenas nome, preço e variação 24h | Botão 🗗 ou `Ctrl+T` |
| **Display** | Dashboard minimalista com gráfico grande | Botão 🌫️ |

### Modo Display

O modo Display mostra um ativo principal em destaque:

- Ícone grande, nome, preço e variações 1h/24h/7d
- Gráfico dos últimos 7 dias com valores mínimo e máximo
- Botões rápidos para trocar entre **BTC, ETH, SOL, XRP**
- Cada botão mostra o preço atual e a variação da última hora
- Botão **Pin** (📌) para fixar a janela no topo
- Botão discreto para voltar ao modo completo
- Transparência ajustável em Preferências → Exibição

### Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Ctrl+R` / `F5` | Atualizar dados |
| `Ctrl+F` | Buscar |
| `Ctrl+T` | Modo Compacto |
| `Ctrl+Comma` | Preferências |
| `Ctrl+Q` / `Ctrl+W` | Sair |

## ⚙️ Preferências

Acesse via **Menu → Preferências**:

- **API**: configurar CoinMarketCap, ver estatísticas de uso e limpar cache
- **Exibição**: mostrar preço em BRL, gerenciar favoritos, ajustar transparência e pin do modo Display
- **Ícones**: abrir pasta de ícones personalizados

## 🔑 Configurando CoinMarketCap API

1. **Obtenha uma API key gratuita** em [coinmarketcap.com/api](https://coinmarketcap.com/api)
   - Plano gratuito: 10.000 chamadas/mês

2. **Configure no aplicativo**:
   - Abra o Crypto Tracker
   - Menu → Preferências → API
   - Cole sua API key no campo "API Key"
   - Clique em "Testar" para verificar
   - Ative "Usar CoinMarketCap"

3. **Economize créditos**:
   - Cache de 5 minutos
   - Limite configurável (padrão: 300 chamadas/dia)
   - Fallback automático para CoinGecko se exceder

## 🖼️ Ícones de Criptomoedas

Para ter ícones visuais das moedas em vez de círculos coloridos:

1. **Abra a pasta de ícones**:
   ```
   Menu → Preferências → Ícones → Abrir Pasta
   # ou manualmente:
   ~/.local/share/crypto-tracker/icons/
   ```

2. **Adicione imagens**:
   - Formatos: PNG, SVG, JPG, WEBP
   - Nomeie com o **símbolo da moeda** em minúsculas:
     - `btc.png` (Bitcoin)
     - `eth.svg` (Ethereum)
     - `sol.png` (Solana)
     - `xrp.png` (XRP)
     - etc.

3. **Fontes de ícones**:
   - [cryptoicons.co](https://cryptoicons.co)
   - [CoinMarketCap](https://coinmarketcap.com)
   - GitHub: `spothq/cryptocurrency-icons`

### Moedas suportadas automaticamente

O app reconhece automaticamente os símbolos mais comuns:
BTC, ETH, USDT, BNB, SOL, XRP, USDC, ADA, DOGE, TRX, AVAX, LINK, etc.

Para outras moedas, o app gera um ícone circular colorido com a primeira letra do símbolo.

## 📁 Estrutura do Projeto

```
cryptoTracker/
├── crypto_tracker/
│   ├── __init__.py       # Inicialização
│   ├── main.py           # Aplicativo GTK4
│   ├── window.py         # Janela principal
│   ├── api.py            # APIs CMC, CoinGecko e AwesomeAPI
│   ├── models.py         # Modelos de dados
│   ├── cache.py          # Sistema de cache
│   ├── settings.py       # Configurações
│   ├── preferences.py    # Janela de preferências
│   ├── widgets.py        # Widgets customizados
│   └── icons.py          # Gerenciador de ícones
├── install.sh            # Script de instalação
├── README.md             # Este arquivo
└── CHANGELOG.md          # Histórico de mudanças
```

## 🔧 APIs Utilizadas

### CoinMarketCap (opcional)
- **Endpoint**: `pro-api.coinmarketcap.com`
- **Plano gratuito**: 10.000 chamadas/mês
- **Dados**: Variações 1h, 24h, 7d
- **Requer**: API Key

### CoinGecko (padrão)
- **Endpoint**: `api.coingecko.com`
- **Gratuito**: Sem chave necessária
- **Dados**: Variações + sparkline 7 dias
- **Limitações**: Rate limit mais restrito

### AwesomeAPI (USD/BRL)
- **Endpoint**: `economia.awesomeapi.com.br`
- **Gratuito**: Sem chave
- **Dados**: Cotação USD/BRL atual e histórico

## 🐛 Solução de Problemas

### CoinMarketCap API não funciona

1. **Verifique sua key**:
   ```
   Preferências → API → Testar
   ```

2. **Verifique o console** (execute via terminal):
   ```bash
   crypto-tracker
   # Olhe por mensagens de erro no terminal
   ```

3. **Problemas comuns**:
   - Key expirada ou inválida
   - Limite de chamadas excedido
   - Problemas de conexão

### Erro: "No module named 'gi'"

```bash
# Debian/Ubuntu
sudo apt install python3-gi

# Fedora
sudo dnf install python3-gobject

# Arch
sudo pacman -S python-gobject
```

### Erro: "No module named 'cairo'"

```bash
# Debian/Ubuntu
sudo apt install python3-cairo

# Fedora
sudo dnf install python3-cairo

# Arch
sudo pacman -S python-cairo
```

### Limpar cache e configurações

```bash
# Cache de dados
rm -rf ~/.cache/crypto-tracker

# Configurações (incluindo API key)
rm -rf ~/.config/crypto-tracker
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Abrir issues para bugs ou sugestões
2. Enviar pull requests
3. Melhorar a documentação

## 📝 Licença

Este projeto está licenciado sob a licença MIT.

## 🙏 Agradecimentos

- **Fernando Arbex** - Desenvolvedor
- [CoinMarketCap](https://www.coinmarketcap.com) - API de dados
- [CoinGecko](https://www.coingecko.com) - API gratuita
- [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas) - Cotação USD/BRL
- [GNOME](https://www.gnome.org) - GTK e Libadwaita

---

<p align="center">Desenvolvido com 💙 por <strong>Fernando Arbex</strong></p>
