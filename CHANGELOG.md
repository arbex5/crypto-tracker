# Changelog - Crypto Tracker

Todas as mudanças e melhorias feitas no projeto estão documentadas aqui.

## [Unreleased] - 2026-06-25

### ✨ Novas funcionalidades

#### Barra rolável de favoritos no modo Display
- Botões de troca de ativo no modo display agora usam uma área rolável
  horizontal (`Gtk.ScrolledWindow`)
- Mostra **todos os ativos favoritos** do usuário
- Navegação por setas `<` e `>` quando há mais ativos do que cabem na tela
- Botões alinhados à esquerda, com tamanho fixo de 64 px
- Rola até o último botão sem deixar espaço em branco
- Fallback para os 3 principais ativos (BTC, ETH, XRP etc.) quando não há favoritos

#### Redimensionamento do modo Display
- Mantida a decoração da janela (`set_decorated(True)`) para preservar as
  bordas de redimensionamento nativas do window manager
- Adicionado um grip de redimensionamento manual no canto inferior direito
  como alternativa
- Tamanho mínimo do modo display reduzido para aproximadamente 200x204

### 🔧 Correções de bugs

- Corrigido o redimensionamento que parava de funcionar quando a decoração
  era removida no modo display

### 📝 Documentação

- Atualizado `docs/WINDOW_RESIZE_NOTES.md` com a solução final de
  redimensionamento e a nova seção sobre o carrossel de favoritos

### 🗂️ Arquivos modificados

- `crypto_tracker/window.py` - Ajustes no modo display (decoração, grip,
  passagem de favoritos para o DisplayWidget)
- `crypto_tracker/widgets.py` - Novo `ResizeGrip`, `DisplayWidget` com
  `Adw.Carousel` e lógica de favoritos
- `crypto_tracker/main.py` - Ajuste no CSS dos botões de ativo
- `docs/WINDOW_RESIZE_NOTES.md` - Documentação atualizada
- `CHANGELOG.md` - Registro das mudanças

## [1.2.1] - 2026-06-25

### 🔧 Correções de bugs

- Corrigido redimensionamento no modo Display minimalista
  - O GTK4 não permite redimensionar janelas já visíveis via API
  - Reduzido o tamanho mínimo do conteúdo para permitir que o usuário
    redimensione manualmente para aproximadamente 357x285
- Melhorado modo Compacto
  - Layout simplificado: mantém a `HeaderBar` no `ToolbarView` e apenas
    esconde busca, status e cabeçalho da lista
  - A janela agora pode ser redimensionada para aproximadamente 400x400
- Protegido salvamento do tamanho da janela durante transições de modo
  - Adicionada flag `_block_size_save` para ignorar redimensionamentos
    provocados pela troca entre modos normal/compacto/display
  - Evita que valores transitórios (ex: 400x378) sejam salvos em
    `settings.json`

### 📝 Documentação

- Adicionado `docs/WINDOW_RESIZE_NOTES.md` com as descobertas técnicas
  sobre redimensionamento no GTK4 e as decisões de implementação

### 🗂️ Arquivos modificados

- `crypto_tracker/window.py` - Refatoração dos modos compacto/display e
  proteção do salvamento de tamanho
- `crypto_tracker/widgets.py` - Sparkline e DisplayWidget mais flexíveis
- `crypto_tracker/main.py` - Ajuste no CSS dos botões de ativo do display
- `docs/WINDOW_RESIZE_NOTES.md` - Nova documentação técnica

## [1.2.0] - 2026-06-17

### ✨ Novas funcionalidades

#### Modo Display Minimalista
- Novo modo display que substitui o antigo modo glass/transparente
- Layout dashboard mostrando um ativo principal por vez
- Exibe: ícone grande, nome, preço, variações 1h/24h/7d e gráfico dos últimos 7 dias
- Botões rápidos para trocar entre BTC, ETH, SOL e XRP
- Cada botão de ativo mostra preço atual e variação da última hora
- Botão discreto no canto superior direito para voltar ao modo completo
- Botão **Pin** para fixar a janela sempre por cima das outras
- Transparência configurável via slider (30% a 100%)
- Estado do ativo selecionado, transparência e pin são salvos

#### Favoritos
- Estrela de favorito em cada linha da lista
- Favoritos são salvos e reaplicados ao carregar dados
- Lista é reordenada colocando favoritos no topo
- Botão para limpar todos os favoritos nas preferências

#### Cotação USD/BRL
- USD/BRL aparece como item na **posição 0** da lista
- Mostra variações 1h, 24h, 7d e gráfico de 7 dias
- Dados históricos buscados da AwesomeAPI
- Cache da taxa USD/BRL por 30 minutos
- Opção para mostrar preço em BRL nas configurações

#### Outras melhorias
- Ícones SVG agora preenchem todo o círculo (crop centralizado)
- Tamanho da janela é salvo ao redimensionar e ao fechar
- Gráficos sparkline suaves e realistas (random walk com mean reversion)
- Sparklines sintéticos gerados como fallback quando CoinGecko não disponível
- Cache da taxa de câmbio e das criptomoedas

### 🔧 Correções de bugs

- Corrigido erro `NameError: name 'Path' is not defined` ao importar preferences
- Corrigido app não abrindo devido a instância anterior travada (single-instance)
- Corrigido erro `AttributeError: 'Settings' object has no attribute 'window_width'`
- Corrigido modo display não aplicando layout quando dados carregavam depois do clique
- Corrigido header/barra de busca/status aparecendo no modo display
- Reduzido timeout de chamadas secundárias para evitar carregamentos longos

### 🗂️ Arquivos modificados

- `crypto_tracker/main.py` - CSS customizado (asset-button)
- `crypto_tracker/models.py` - Campos `is_favorite`, `brl_price`
- `crypto_tracker/settings.py` - Favorites, show_brl_price, display_asset, display_opacity, display_pinned
- `crypto_tracker/cache.py` - Cache de exchange rate e novos campos
- `crypto_tracker/api.py` - Busca USD/BRL histórico, sparklines sintéticos, inserção USD/BRL na posição 0
- `crypto_tracker/widgets.py` - CryptoRow com estrela e BRL, DisplayWidget, SparklineWidget melhorado
- `crypto_tracker/window.py` - Modo display, ordenação de favoritos, salvamento de tamanho
- `crypto_tracker/preferences.py` - Página de Exibição com controles de BRL, favoritos, display
- `crypto_tracker/icons.py` - Ícones SVG preenchem círculo

## [1.1.0] - 2026-02-20

### Funcionalidades originais
- Top 50 criptomoedas por market cap
- Preços em tempo real em USD
- Variações 1h, 24h, 7d
- Gráficos sparkline de 7 dias
- Busca em tempo real
- Modo compacto
- Modo glass/transparente
- Cache local
- Suporte a CoinMarketCap API
- Fallback para CoinGecko
