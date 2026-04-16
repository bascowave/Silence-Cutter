# Silence Cutter — Plano de Melhorias v2

## Contexto

O projeto Silence Cutter completou 6 sprints iniciais com a GUI funcional, mas a exploração do código revelou: (1) fragilidades de robustez — parser frágil, I/O caractere-por-caractere, race conditions, (2) lacunas de UX — sem indicador de loading, sem drag-and-drop, sem persistência de configurações, e (3) oportunidades de novas funcionalidades — batch processing, presets, atalhos de teclado.

O objetivo deste plano é levar o app de "protótipo funcional" a "ferramenta confiável de produção".

---

## Sprint 7 — Correções Críticas e Bugs

### 24. Corrigir fragilidade do parser de análise
- [x] 25.1 Documentar formato exato da saída de `auto-editor --stats` v30.1.0
- [x] 25.2 Reescrever `_parse_stats()` com regex preciso baseado na saída real
- [x] 25.3 Adicionar log de warning quando parsing falha (em vez de retornar 0.0 silenciosamente)
- [x] 25.4 Validação: se `original_duration == 0.0`, levantar exceção com saída bruta
- [x] 25.5 Guardar saída bruta no `AnalysisResult` (novo campo `raw_output: str`)

### 25. Corrigir leitura caractere-por-caractere do processor
- [x] 26.1 Substituir loop `read(1)` por leitura linha-a-linha com `iter(process.stdout.readline, '')`
- [x] 26.2 Tratar linhas com `\r` sem `\n` (progresso) fazendo split por `\r`
- [x] 26.3 Verificar que progresso atualiza corretamente com `--progress machine`
- [x] 26.4 Adicionar timeout de 300s via `threading.Timer` que mata o processo

**Arquivos:** `core/processor.py`, `core/analyzer.py`, `gui/sidebar.py`, `gui/main_window.py`

---

## Sprint 8 — Robustez e Estabilidade

### 27. Máquina de estados para a UI
- [x] 27.1 Criar enum `AppState` com: `IDLE`, `ANALYZING`, `PROCESSING`, `CANCELLING`
- [x] 27.2 Adicionar `self._state` na `MainWindow`
- [x] 27.3 Criar `_set_state(new_state)` que configura UI conforme estado
- [x] 27.4 Guards em `on_preview_click()`, `on_process_click()`, `on_cancel_click()`
- [x] 27.5 Transições: IDLE→ANALYZING, IDLE→PROCESSING, PROCESSING→CANCELLING, *→IDLE
- [x] 27.6 Desabilitar "Selecionar Arquivo" durante ANALYZING e PROCESSING

### 28. Sistema de fila de eventos (queue)
- [x] 28.1 Criar `queue.Queue` na `MainWindow`
- [x] 28.2 Criar `_poll_queue()` — processa mensagens a cada 50ms via `self.after()`
- [x] 28.3 Definir dataclasses: `LogMessage`, `ProgressMessage`, `CompleteMessage`, `ErrorMessage`
- [x] 28.4 Substituir todos os callbacks `self.after(0, lambda: ...)` por `queue.put()`
- [x] 28.5 Iniciar polling no `__init__`

### 29. Gerenciamento de threads
- [x] 29.1 Armazenar referência da thread ativa em `self._worker_thread`
- [x] 29.2 Verificar thread viva antes de criar nova (protegido pela máquina de estados)
- [x] 29.3 No `cancel()`: `terminate()` → `wait(timeout=5)` → `kill()` se ainda ativo
- [x] 29.4 Adicionar `threading.Event` (`_cancel_event`) para cancelamento cooperativo
- [x] 29.5 Limpar referência de thread ao completar

### 30. Resolução única do binário
- [x] 30.1 Resolver `binary_path` uma vez no `__init__` da `MainWindow`
- [x] 30.2 Passar como parâmetro ao `Processor` e `Analyzer`
- [x] 30.3 Warning imediato + desabilitar botões se não encontrado
- [x] 30.4 Remover `_resolve_binary_path()` de dentro de `_build_command()`

**Arquivos:** `gui/main_window.py`, `core/processor.py`, `core/analyzer.py`

---

## Sprint 9 — Melhorias de UX

### 31. Indicador de loading durante análise
- [x] 31.1 Adicionar `CTkProgressBar` indeterminado no `PreviewPanel`
- [x] 31.2 Criar `show_loading()` / `hide_loading()`
- [x] 31.3 Chamar `show_loading()` antes da análise, `hide_loading()` ao terminar
- [x] 31.4 Texto "Analisando..." visível durante loading

### 32. Informações do arquivo de vídeo
- [x] 32.1 Criar `get_video_info(path)` em `core/analyzer.py` — tamanho e formato via `os.path.getsize()` + extensão
- [x] 32.2 Seção "INFO" no `PreviewPanel`: nome, tamanho (MB/GB), formato
- [x] 32.3 Atualizar ao selecionar novo arquivo
- [x] 32.4 Formatar tamanho apropriadamente

### 33. Drag-and-drop
- [x] 33.1 Instalar `tkinterdnd2` e adicionar ao `requirements.txt`
- [x] 33.2 Registrar `MainWindow` como drop target
- [x] 33.3 Validar extensão do arquivo dropado
- [x] 33.4 Chamar `on_file_selected()` no drop
- [x] 33.5 Feedback visual: borda tracejada muda de cor ao arrastar
- [x] 33.6 Fallback: funcionar sem drag-and-drop se `tkinterdnd2` não disponível

### 34. Persistência de configurações
- [x] 34.1 Criar `core/settings.py` com classe `AppSettings` (JSON)
- [x] 34.2 Caminho: `%APPDATA%/SilenceCutter/settings.json`
- [x] 34.3 Campos: `threshold_db`, `margin`, `last_directory`
- [x] 34.4 `load()` com fallback para defaults
- [x] 34.5 `save()` grava JSON
- [x] 34.6 Carregar no init e aplicar nos sliders
- [x] 34.7 Salvar ao fechar janela (`WM_DELETE_WINDOW`)
- [x] 34.8 Salvar a cada mudança de parâmetro
- [x] 34.9 Usar `last_directory` no file dialog

### 35. Melhorias visuais
- [x] 35.1 Stats com "0:00" em vez de "—" após selecionar arquivo
- [x] 35.2 Tooltip com nome completo do arquivo na sidebar

**Arquivos:** `gui/preview.py`, `gui/sidebar.py`, `gui/main_window.py`, `core/settings.py` (novo), `core/analyzer.py`

---

## Sprint 10 — Funcionalidades Novas

### 36. Processamento em lote (batch)
- [x] 36.1 Botão "Adicionar Arquivos" na sidebar (`filedialog.askopenfilenames`)
- [x] 36.2 Widget `FileListPanel` — lista scrollable com botão X para remover
- [x] 36.3 Botão "Limpar Lista"
- [x] 36.4 `on_process_click()` itera sobre lista em sequência
- [x] 36.5 Progresso geral: "Arquivo 2/5"
- [x] 36.6 Barra de progresso dupla (geral + individual)
- [x] 36.7 Cancelar lote inteiro
- [x] 36.8 Resumo ao finalizar: sucessos, falhas, tempo total
- [x] 36.9 Compatibilidade: 1 arquivo = comportamento atual

### 37. Perfis de preset
- [x] 37.1 Seção "PRESET" na sidebar com `CTkOptionMenu`
- [x] 37.2 Opções: Personalizado, Podcast (-30dB/0.3s), Vlog (-24dB/0.2s), Short (-20dB/0.1s)
- [x] 37.3 Ao selecionar: atualizar todos os sliders
- [x] 37.4 Ao mover slider: mudar para "Personalizado"
- [x] 37.5 Persistir último preset no `settings.json`

### 38. Seleção de formato de saída
- [x] 38.1 Seção "FORMATO DE SAÍDA" na sidebar com dropdown
- [x] 38.2 Opções: Mesmo do original, MP4, MKV, MOV
- [x] 38.3 Atualizar `_build_output_path()` com extensão selecionada
- [x] 38.4 Persistir no `settings.json`

### 39. Atalhos de teclado
- [x] 39.1 `Ctrl+O` → Selecionar Arquivo
- [x] 39.2 `Ctrl+Enter` → Processar Vídeo
- [x] 39.3 `Escape` → Cancelar
- [x] 39.4 `Ctrl+P` → Pré-visualizar
- [x] 39.5 Texto dos atalhos nos tooltips
- [x] 39.6 Respeitar máquina de estados

**Arquivos:** `gui/sidebar.py`, `gui/main_window.py`, `gui/preview.py`, `core/processor.py`, `core/settings.py`

---

## Sprint 11 — Qualidade de Código

### 40. Dividir PreviewPanel em componentes
- [x] 40.1 Extrair `gui/stats_panel.py` — StatsPanel
- [x] 40.2 Extrair `gui/progress_panel.py` — ProgressPanel
- [x] 40.3 Extrair `gui/log_panel.py` — LogPanel
- [x] 40.4 Extrair `gui/result_panel.py` — ResultPanel
- [x] 40.5 PreviewPanel vira container orquestrando os 4 sub-painéis
- [x] 40.6 Manter API pública inalterada (delegação)

### 41. Hierarquia de exceções
- [x] 41.1 Criar `core/errors.py` com `SilenceCutterError` base
- [x] 41.2 Subclasses: `BinaryNotFoundError`, `ProcessingError`, `AnalysisError`, `InvalidInputError`
- [x] 41.3 Usar tipos específicos em vez de exceções genéricas
- [x] 41.4 Tratamento centralizado no `_poll_queue()`

### 42. Lint e formatação
- [x] 42.1 `pyproject.toml` com configuração ruff (line-length=100, Python 3.10)
- [x] 42.2 Executar ruff e corrigir warnings
- [x] 42.3 `.editorconfig` para consistência

**Arquivos:** `gui/preview.py` → split em 4, `core/errors.py` (novo), `pyproject.toml` (novo)

---

## Verificação

Para cada sprint:
1. Executar `python silence-cutter/app.py` e verificar que a GUI inicia sem erros
2. Testar fluxo completo: selecionar vídeo → pré-visualizar → processar → abrir pasta
3. Verificar log: comando gerado deve incluir todos os parâmetros
4. Testar cancelamento durante processamento
5. Testar com arquivo inválido e sem binário
6. Após Sprint 11: executar `ruff check silence-cutter/` sem warnings
