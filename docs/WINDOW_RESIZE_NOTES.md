# Notas de Debug: Redimensionamento de Janela no GTK4

> Arquivo de referência para não perder o contexto ao retomar trabalhos no modo
> compacto/display do Crypto Tracker.
>
> Última atualização: 2026-06-25

## Problema em resumo

O usuário não consegue redimensionar a janela no **modo minimalista/display** e
o **modo compacto** não ficava realmente pequeno. Além disso, o tamanho salvo
em `settings.json` estava sendo corrompido com valores estranhos (ex: `400x378`
em vez do tamanho normal da janela).

## Descobertas técnicas

### 1. GTK4 não permite redimensionar uma janela já visível

Testamos a API de `Gdk.Toplevel`:

```python
from gi.repository import Gdk
dir(Gdk.Toplevel)
# ['begin_move', 'begin_resize', 'focus', 'get_state', ...]
```

Não existe método do tipo `set_size()` ou `resize()` para janelas já
apresentadas. O GTK4 deixa o controle de geometria para o window manager (WM).

### 2. `set_default_size()` só funciona antes de `present()`

Chamar `self.set_default_size(360, 520)` depois que a janela já está visível
**não tem efeito**. Ele é apenas uma dica inicial para o WM.

### 3. O conteúdo impõe o tamanho mínimo da janela

Mesmo que definamos um tamanho pequeno, o WM só pode encolher a janela até o
*tamanho natural mínimo* do conteúdo visível. No modo display, o
`DisplayWidget` com sparkline de `300x180` e margens estava impondo aproximadamente
`522x500`. No modo compacto, a `HeaderBar` completa e a lista de muitas colunas
impunham `~402x369`.

### 4. `set_size_request()` no conteúdo é a alavanca disponível

Para permitir que o usuário redimensione para baixo, devemos reduzir o
`size-request` dos widgets que estão visíveis. Exemplo:

```python
self.display_container.set_size_request(300, 280)
```

Isso não define o tamanho da janela, mas diz ao GTK/WM que o conteúdo *pode*
ter aquele tamanho mínimo.

### 5. `notify::default-width/height` dispara durante transições de layout

Conectamos:

```python
self.connect("notify::default-width", self._on_window_size_changed)
self.connect("notify::default-height", self._on_window_size_changed)
```

Durante a troca para modo compacto/display, o GTK realoca a janela e esses
sinais disparam. Se salvamos o tamanho nesse momento, gravamos o tamanho de
transição (ex: `400x378`) em vez do tamanho normal do usuário.

### 6. Solução para salvar tamanho corretamente

- Marcar `_in_special_mode = True` **antes** de qualquer mudança visual.
- Adicionar uma flag `_block_size_save` que impede salvamento por alguns
  milissegundos após entrar/sair de modo especial.
- Só salvar quando a janela estiver no modo normal e o redimensionamento for
  realmente do usuário.

## Decisões de implementação

### Modo display/minimalista

- **Não usar** `set_default_size()` após a janela estar visível.
- Definir `set_size_request()` menor no container do display para que o WM
  permita que o usuário redimensione manualmente.
- Tornar o `DisplayWidget` mais flexível (sparkline com `hexpand`/`vexpand` e
  tamanhos de conteúdo menores) para não impor largura excessiva.
- Continuar permitindo `set_resizable(True)`.

### Modo compacto

- **Simplificar drasticamente**: em vez de remover a `HeaderBar` do
  `ToolbarView` e reconstruir o layout em um `_compact_layout` separado, apenas
  esconder `search_box`, `status_box` e o cabeçalho da lista (`header_row`).
- Manter a `HeaderBar` principal no `ToolbarView` (evita perder comportamento de
  scroll e decoração).
- Mostrar no máximo 5 itens na lista (`max_items = 5`).
- Esconder botões não essenciais da header (`glass_button`, `refresh_button`).
- Reduzir `size_request` da lista para permitir janela pequena.

### Persistência de tamanho

- Guardar `_normal_size` ao entrar em modo especial.
- Restaurar `_normal_size` ao voltar ao modo normal.
- Sempre ignorar salvamento quando `_in_special_mode` ou `_block_size_save`.

## Comandos úteis para diagnóstico

```bash
# Tamanho atual da janela
python3 - <<'PY'
import json
with open(Path.home()/'.config/crypto-tracker/settings.json') as f:
    d = json.load(f)
print(d.get('window_width'), d.get('window_height'))
PY

# Medir widgets
# (ver _debug_sizes() em window.py)

# Forçar tamanho mínimo manualmente
python3 - <<'PY'
import gi; gi.require_version('Gtk','4.0')
from gi.repository import Gtk
# Gtk.Window não tem resize() no GTK4
PY
```

## Referências

- GTK4 `Gdk.Toplevel` docs: não expõe `set_size`/`resize`.
- `Gtk.Window.set_default_size`: hint inicial, ignorado após `present()`.
- `Gtk.Widget.set_size_request`: define tamanho mínimo do widget.

