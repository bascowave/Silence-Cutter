# Silence Cutter — Plano de Melhorias v2

## Contexto

O projeto Silence Cutter completou 6 sprints iniciais com a GUI funcional, mas a exploração do código revelou: (1) bugs críticos — parâmetros `--smooth` nunca são passados ao auto-editor apesar dos tasks 8-9 estarem marcados como concluídos, (2) fragilidades de robustez — parser frágil, I/O caractere-por-caractere, race conditions, (3) lacunas de UX — sem indicador de loading, sem drag-and-drop, sem persistência de configurações, e (4) oportunidades de novas funcionalidades — batch processing, presets, atalhos de teclado.

O objetivo deste plano é levar o app de "protótipo funcional" a "ferramenta confiável de produção".

---

## Sprint 7 — Correções Críticas e Bugs

### 24. Implementar parâmetros --smooth que faltam
- [ ] 24.1 Adicionar campos `min_cut: float = 0.2` e `min_clip: float = 0.1` ao dataclass `ProcessorSettings` em `core/processor.py`
- [ ] 24.2 Atualizar `_build_command()` em `core/processor.py` para incluir `--smooth {min_cut}s,{min_clip}s`
- [ ] 24.3 Atualizar `analyzer.analyze()` em `core/analyzer.py` para aceitar e passar `min_cut`/`min_clip` com `--smooth`
- [ ] 24.4 Implementar `_build_mincut_section()` na `Sidebar` — slider 0.0–2.0, padrão 0.2, step 0.05, sufixo "s"
- [ ] 24.5 Implementar `_build_minclip_section()` na `Sidebar` — slider 0.0–2.0, padrão 0.1, step 0.05, sufixo "s"
- [ ] 24.6 Adicionar propriedades `min_cut` e `min_clip` na `Sidebar`
- [ ] 24.7 Adicionar tooltips nos dois novos sliders
- [ ] 24.8 Atualizar `on_preview_click()` em `main_window.py` para passar `min_cut`/`min_clip` ao analyzer
- [ ] 24.9 Atualizar `on_process_click()` em `main_window.py` para popular `min_cut`/`min_clip` no `ProcessorSettings`
- [ ] 24.10 Verificar: comando gerado inclui `--smooth 0.20s,0.10s` no log

### 25. Corrigir fragilidade do parser de análise
- [ ] 25.1 Documentar formato exato da saída de `auto-editor --stats` v30.1.0
- [ ] 25.2 Reescrever `_parse_stats()` com regex preciso baseado na saída real
- [ ] 25.3 Adicionar log de warning quando parsing falha (em vez de retornar 0.0 silenciosamente)
- [ ] 25.4 Validação: se `original_duration == 0.0`, levantar exceção com saída bruta
- [ ] 25.5 Guardar saída bruta no `AnalysisResult` (novo campo `raw_output: str`)

### 26. Corrigir leitura caractere-por-caractere do processor
- [ ] 26.1 Substituir loop `read(1)` por leitura linha-a-linha com `iter(process.stdout.readline, '')`
- [ ] 26.2 Tratar linhas com `\r` sem `\n` (progresso) fazendo split por `\r`
- [ ] 26.3 Verificar que progresso atualiza corretamente com `--progress machine`
- [ ] 26.4 Adicionar timeout de 300s via `threading.Timer` que mata o processo

**Arquivos:** `core/processor.py`, `core/analyzer.py`, `gui/sidebar.py`, `gui/main_window.py`

---

## Sprint 8 — Robustez e Estabilidade

### 27. Máquina de estados para a UI
- [ ] 27.1 Criar enum `AppState` com: `IDLE`, `ANALYZING`, `PROCESSING`, `CANCELLING`
- [ ] 27.2 Adicionar `self._state` na `MainWindow`
- [ ] 27.3 Criar `_set_state(new_state)` que configura UI conforme estado
- [ ] 27.4 Guards em `on_preview_click()`, `on_process_click()`, `on_cancel_click()`
- [ ] 27.5 Transições: IDLE→ANALYZING, IDLE→PROCESSING, PROCESSING→CANCELLING, *→IDLE
- [ ] 27.6 Desabilitar "Selecionar Arquivo" durante ANALYZING e PROCESSING

### 28. Sistema de fila de eventos (queue)
- [ ] 28.1 Criar `queue.Queue` na `MainWindow`
- [ ] 28.2 Criar `_poll_queue()` — processa mensagens a cada 50ms via `self.after()`
- [ ] 28.3 Definir dataclasses: `LogMessage`, `ProgressMessage`, `CompleteMessage`, `ErrorMessage`
- [ ] 28.4 Substituir todos os callbacks `self.after(0, lambda: ...)` por `queue.put()`
- [ ] 28.5 Iniciar polling no `__init__`

### 29. Gerenciamento de threads
- [ ] 29.1 Armazenar referência da thread ativa em `self._worker_thread`
- [ ] 29.2 Verificar thread viva antes de criar nova (protegido pela máquina de estados)
- [ ] 29.3 No `cancel()`: `terminate()` → `wait(timeout=5)` → `kill()` se ainda ativo
- [ ] 29.4 Adicionar `threading.Event` (`_cancel_event`) para cancelamento cooperativo
- [ ] 29.5 Limpar referência de thread ao completar

### 30. Resolução única do binário
- [ ] 30.1 Resolver `binary_path` uma vez no `__init__` da `MainWindow`
- [ ] 30.2 Passar como parâmetro ao `Processor` e `Analyzer`
- [ ] 30.3 Warning imediato + desabilitar botões se não encontrado
- [ ] 30.4 Remover `_resolve_binary_path()` de dentro de `_build_command()`

**Arquivos:** `gui/main_window.py`, `core/processor.py`, `core/analyzer.py`

---

## Sprint 9 — Melhorias de UX

### 31. Indicador de loading durante análise
- [ ] 31.1 Adicionar `CTkProgressBar` indeterminado no `PreviewPanel`
- [ ] 31.2 Criar `show_loading()` / `hide_loading()`
- [ ] 31.3 Chamar `show_loading()` antes da análise, `hide_loading()` ao terminar
- [ ] 31.4 Texto "Analisando..." visível durante loading

### 32. Informações do arquivo de vídeo
- [ ] 32.1 Criar `get_video_info(path)` em `core/analyzer.py` — tamanho e formato via `os.path.getsize()` + extensão
- [ ] 32.2 Seção "INFO" no `PreviewPanel`: nome, tamanho (MB/GB), formato
- [ ] 32.3 Atualizar ao selecionar novo arquivo
- [ ] 32.4 Formatar tamanho apropriadamente

### 33. Drag-and-drop
- [ ] 33.1 Instalar `tkinterdnd2` e adicionar ao `requirements.txt`
- [ ] 33.2 Registrar `MainWindow` como drop target
- [ ] 33.3 Validar extensão do arquivo dropado
- [ ] 33.4 Chamar `on_file_selected()` no drop
- [ ] 33.5 Feedback visual: borda tracejada muda de cor ao arrastar
- [ ] 33.6 Fallback: funcionar sem drag-and-drop se `tkinterdnd2` não disponível

### 34. Persistência de configurações
- [ ] 34.1 Criar `core/settings.py` com classe `AppSettings` (JSON)
- [ ] 34.2 Caminho: `%APPDATA%/SilenceCutter/settings.json`
- [ ] 34.3 Campos: `threshold_db`, `margin`, `min_cut`, `min_clip`, `last_directory`
- [ ] 34.4 `load()` com fallback para defaults
- [ ] 34.5 `save()` grava JSON
- [ ] 34.6 Carregar no init e aplicar nos sliders
- [ ] 34.7 Salvar ao fechar janela (`WM_DELETE_WINDOW`)
- [ ] 34.8 Salvar a cada mudança de parâmetro
- [ ] 34.9 Usar `last_directory` no file dialog

### 35. Melhorias visuais
- [ ] 35.1 Stats com "0:00" em vez de "—" após selecionar arquivo
- [ ] 35.2 Tooltip com nome completo do arquivo na sidebar

**Arquivos:** `gui/preview.py`, `gui/sidebar.py`, `gui/main_window.py`, `core/settings.py` (novo), `core/analyzer.py`

---

## Sprint 10 — Funcionalidades Novas

### 36. Processamento em lote (batch)
- [ ] 36.1 Botão "Adicionar Arquivos" na sidebar (`filedialog.askopenfilenames`)
- [ ] 36.2 Widget `FileListPanel` — lista scrollable com botão X para remover
- [ ] 36.3 Botão "Limpar Lista"
- [ ] 36.4 `on_process_click()` itera sobre lista em sequência
- [ ] 36.5 Progresso geral: "Arquivo 2/5"
- [ ] 36.6 Barra de progresso dupla (geral + individual)
- [ ] 36.7 Cancelar lote inteiro
- [ ] 36.8 Resumo ao finalizar: sucessos, falhas, tempo total
- [ ] 36.9 Compatibilidade: 1 arquivo = comportamento atual

### 37. Perfis de preset
- [ ] 37.1 Seção "PRESET" na sidebar com `CTkOptionMenu`
- [ ] 37.2 Opções: Personalizado, Podcast (-30dB/0.3s/0.5s/0.2s), Vlog (-24dB/0.2s/0.2s/0.1s), Short (-20dB/0.1s/0.1s/0.05s)
- [ ] 37.3 Ao selecionar: atualizar todos os sliders
- [ ] 37.4 Ao mover slider: mudar para "Personalizado"
- [ ] 37.5 Persistir último preset no `settings.json`

### 38. Seleção de formato de saída
- [ ] 38.1 Seção "FORMATO DE SAÍDA" na sidebar com dropdown
- [ ] 38.2 Opções: Mesmo do original, MP4, MKV, MOV
- [ ] 38.3 Atualizar `_build_output_path()` com extensão selecionada
- [ ] 38.4 Persistir no `settings.json`

### 39. Atalhos de teclado
- [ ] 39.1 `Ctrl+O` → Selecionar Arquivo
- [ ] 39.2 `Ctrl+Enter` → Processar Vídeo
- [ ] 39.3 `Escape` → Cancelar
- [ ] 39.4 `Ctrl+P` → Pré-visualizar
- [ ] 39.5 Texto dos atalhos nos tooltips
- [ ] 39.6 Respeitar máquina de estados

**Arquivos:** `gui/sidebar.py`, `gui/main_window.py`, `gui/preview.py`, `core/processor.py`, `core/settings.py`

---

## Sprint 11 — Qualidade de Código

### 40. Dividir PreviewPanel em componentes
- [ ] 40.1 Extrair `gui/stats_panel.py` — StatsPanel
- [ ] 40.2 Extrair `gui/progress_panel.py` — ProgressPanel
- [ ] 40.3 Extrair `gui/log_panel.py` — LogPanel
- [ ] 40.4 Extrair `gui/result_panel.py` — ResultPanel
- [ ] 40.5 PreviewPanel vira container orquestrando os 4 sub-painéis
- [ ] 40.6 Manter API pública inalterada (delegação)

### 41. Hierarquia de exceções
- [ ] 41.1 Criar `core/errors.py` com `SilenceCutterError` base
- [ ] 41.2 Subclasses: `BinaryNotFoundError`, `ProcessingError`, `AnalysisError`, `InvalidInputError`
- [ ] 41.3 Usar tipos específicos em vez de exceções genéricas
- [ ] 41.4 Tratamento centralizado no `_poll_queue()`

### 42. Lint e formatação
- [ ] 42.1 `pyproject.toml` com configuração ruff (line-length=100, Python 3.10)
- [ ] 42.2 Executar ruff e corrigir warnings
- [ ] 42.3 `.editorconfig` para consistência

**Arquivos:** `gui/preview.py` → split em 4, `core/errors.py` (novo), `pyproject.toml` (novo)

---

## Verificação

Para cada sprint:
1. Executar `python silence-cutter/app.py` e verificar que a GUI inicia sem erros
2. Testar fluxo completo: selecionar vídeo → pré-visualizar → processar → abrir pasta
3. Verificar log: comando gerado deve incluir todos os parâmetros (`--smooth`, etc.)
4. Testar cancelamento durante processamento
5. Testar com arquivo inválido e sem binário
6. Após Sprint 11: executar `ruff check silence-cutter/` sem warnings
