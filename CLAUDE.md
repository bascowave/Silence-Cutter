# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

**Silence Cutter** — GUI desktop (CustomTkinter) para cortar silêncios de vídeos usando `auto-editor` como engine externa.

## Comandos

```bash
# Instalar dependências
pip install -r silence-cutter/requirements.txt

# Executar a aplicação
python silence-cutter/app.py
```

Não há testes, lint ou CI configurados. O binário `auto-editor.exe` (v30.1.0) deve estar em `silence-cutter/bin/`.

## Arquitetura

```
silence-cutter/
├── app.py              # Entry point
├── core/
│   ├── analyzer.py     # SilenceCutterAnalyzer — pré-análise via --stats (subprocess)
│   └── processor.py    # SilenceCutterProcessor — execução do corte (subprocess)
└── gui/
    ├── main_window.py  # MainWindow — orquestração, validação, grid layout
    ├── sidebar.py      # Sidebar — seleção de arquivo, sliders de parâmetros
    └── preview.py      # PreviewPanel — estatísticas, progresso, log, resultados
```

**Fluxo principal:**
1. Sidebar: usuário seleciona arquivo e ajusta parâmetros (threshold, margin, min-cut, min-clip)
2. Preview: `Analyzer.analyze()` → parsing de stats com regex → exibe duração original/estimada/removida
3. Process: `Processor.process()` → progresso em tempo real + log → resultado final

**Padrões críticos:**
- Analyzer e Processor rodam em `threading.Thread` para não travar a GUI
- Callbacks da thread para GUI usam `widget.after()` (thread-safety do Tkinter)
- Parsing de saída do auto-editor usa múltiplos padrões regex como fallback
- Validação de entrada e disponibilidade do binário antes de qualquer operação
- Output: `{nome}_cut{ext}` no mesmo diretório do original

## Documentação

- **Design spec:** `silence-cutter/docs/specs/2026-04-07-silence-cutter-design.md`
- **Plano de tarefas:** `silence-cutter/tasks/tasks01.md` (6 sprints)
