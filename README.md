# Silence Cutter

GUI desktop para cortar silêncios de vídeos de forma automática. Usa o [auto-editor](https://auto-editor.com/) como engine de processamento e oferece uma interface visual simples para configurar, pré-visualizar e executar os cortes.

---

## Funcionalidades

- **Seleção de arquivo** — suporta `.mp4`, `.mkv`, `.mov`, `.avi` e `.webm`
- **Pré-visualização** — analisa o vídeo e estima a duração final sem processar o arquivo
- **Processamento** — executa o corte com progresso em tempo real
- **Cancelamento** — interrompe o processamento a qualquer momento
- **Parâmetros ajustáveis** — threshold de silêncio e margem de segurança
- **Log em tempo real** — exibe a saída do auto-editor durante o processamento
- **Modo escuro** — interface com tema dark-blue

---

## Pré-requisitos

- Python 3.10+
- `auto-editor.exe` v30.1.0 na pasta `silence-cutter/bin/`
  - Alternativamente, `auto-editor` disponível no PATH do sistema

---

## Instalação

```bash
# Clonar o repositório
git clone <url-do-repositorio>
cd "Edição de Vídeo"

# Instalar dependências Python
pip install -r silence-cutter/requirements.txt
```

Coloque o binário `auto-editor.exe` em:

```
silence-cutter/
└── bin/
    └── auto-editor.exe
```

---

## Uso

```bash
python silence-cutter/app.py
```

### Fluxo de uso

1. Clique em **Selecionar Arquivo** e escolha o vídeo
2. Ajuste os parâmetros na barra lateral (threshold e margem)
3. Clique em **Pré-visualizar** para estimar a duração do resultado
4. Clique em **Processar Vídeo** para executar o corte
5. O arquivo gerado é salvo no mesmo diretório do original com o sufixo `_cut`

**Exemplo:** `minha_aula.mp4` → `minha_aula_cut.mp4`

---

## Parâmetros

| Parâmetro | Padrão | Intervalo | Descrição |
|-----------|--------|-----------|-----------|
| **Threshold** | `-24 dB` | `-60` a `0 dB` | Volume abaixo do qual o áudio é tratado como silêncio. Valores mais baixos tornam o corte menos agressivo. |
| **Margem** | `0.20 s` | `0.0` a `2.0 s` | Tempo extra preservado antes e depois de cada trecho com áudio. Evita cortes abruptos. |

Os valores podem ser ajustados via slider ou digitados diretamente no campo ao lado.

---

## Arquitetura

```
silence-cutter/
├── app.py              # Entry point — inicializa a MainWindow
├── requirements.txt    # Dependências Python (customtkinter)
├── bin/
│   └── auto-editor.exe # Engine externa de processamento
├── core/
│   ├── analyzer.py     # SilenceCutterAnalyzer — pré-análise via --stats
│   └── processor.py    # SilenceCutterProcessor — execução do corte
└── gui/
    ├── main_window.py  # MainWindow — orquestração e layout principal
    ├── sidebar.py      # Sidebar — seleção de arquivo e sliders
    └── preview.py      # PreviewPanel — estatísticas, progresso e log
```

### Componentes principais

**`core/analyzer.py`** — Executa o `auto-editor --stats` para obter as durações original e estimada sem processar o vídeo. Faz parsing da saída com múltiplos padrões regex como fallback.

**`core/processor.py`** — Executa o corte real em um subprocess, lê a saída caractere a caractere para capturar progresso em tempo real (formato `machine` do auto-editor). Suporta cancelamento.

**`gui/main_window.py`** — Orquestra os callbacks entre Sidebar e PreviewPanel. Valida o arquivo de entrada e gerencia os estados dos botões. Despacha operações pesadas para threads separadas e retorna para a GUI via `widget.after()` (thread-safety do Tkinter).

**`gui/sidebar.py`** — Controles de entrada: seleção de arquivo, sliders sincronizados com campos de texto, botões de ação e cancelamento. Tooltips embutidos.

**`gui/preview.py`** — Painel direito com estatísticas de duração, barra de progresso, log colorido e resultado com caminho do arquivo gerado.

---

## Decisões técnicas

- **Threading** — Analyzer e Processor rodam em `threading.Thread` com `daemon=True` para não travar a GUI
- **Thread-safety** — Callbacks da thread para a GUI usam `widget.after(0, fn)` em vez de chamar widgets diretamente
- **Parsing robusto** — A saída do auto-editor varia entre versões; o parser usa múltiplos padrões regex com fallback progressivo
- **Cancelamento limpo** — Ao cancelar, o processo é terminado e o arquivo de saída parcial é removido
- **Resolução do binário** — Primeiro verifica `bin/auto-editor.exe`, depois procura no PATH via `shutil.which`

---

## Dependências

| Pacote | Versão mínima | Uso |
|--------|---------------|-----|
| `customtkinter` | 5.2.0 | Interface gráfica moderna sobre Tkinter |
| `auto-editor` | 30.1.0 | Engine externa de corte de silêncio (binário) |

---

## Documentação interna

- **Design spec:** `silence-cutter/docs/specs/2026-04-07-silence-cutter-design.md`
- **Plano de tarefas:** `silence-cutter/tasks/tasks01.md`
