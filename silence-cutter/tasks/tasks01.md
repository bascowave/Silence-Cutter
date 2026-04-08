# Silence Cutter — Plano de Implementação

> Referência: `docs/superpowers/specs/2026-04-07-silence-cutter-design.md`

---

## Sprint 1 — Fundação (Estrutura do projeto + Core)

### 1. Scaffold do projeto
- [X] 1.1 Criar estrutura de diretórios (`silence-cutter/`, `gui/`, `core/`, `bin/`)
- [X] 1.2 Criar `requirements.txt` com `customtkinter` como dependência
- [X] 1.3 Criar `app.py` com entry point mínimo (importa e inicia `MainWindow`)
- [X] 1.4 Criar arquivos `__init__.py` nos pacotes `gui/` e `core/`
- [X] 1.5 Adicionar `.gitignore` para Python (venv, __pycache__, bin/*.exe)

### 2. Integração com auto-editor — Processor
- [X] 2.1 Criar `core/processor.py` com classe `SilenceCutterProcessor`
- [X] 2.2 Implementar método `_build_command()` que monta o comando auto-editor a partir dos parâmetros (threshold, margin, smooth_mincut, smooth_minclip, input_path, output_path)
- [X] 2.3 Implementar método `_resolve_binary_path()` que localiza o `auto-editor.exe` na pasta `bin/` relativa ao app
- [X] 2.4 Implementar método `process()` que executa o comando via `subprocess.Popen` com `stdout=PIPE` e `stderr=PIPE`
- [X] 2.5 Implementar callback `on_output(line: str)` para enviar linhas de log em tempo real para a GUI
- [X] 2.6 Implementar callback `on_progress(percent: float)` para parsear progresso da saída do auto-editor
- [X] 2.7 Implementar callback `on_complete(success: bool, output_path: str)` para notificar término
- [X] 2.8 Implementar método `cancel()` que mata o subprocess em execução
- [X] 2.9 Implementar geração do output path com sufixo `_cut` no mesmo diretório do input

### 3. Integração com auto-editor — Analyzer
- [X] 3.1 Criar `core/analyzer.py` com classe `SilenceCutterAnalyzer`
- [X] 3.2 Implementar método `analyze()` que executa `auto-editor <input> --stats` com os parâmetros configurados
- [X] 3.3 Implementar parsing da saída do `--stats` para extrair duração original e estimativa de cortes
- [X] 3.4 Implementar cálculo de silêncio removido (original - estimado)
- [X] 3.5 Retornar dados como dataclass `AnalysisResult(original_duration, estimated_duration, silence_removed)`

---

## Sprint 2 — GUI Base (Janela principal + Sidebar)

### 4. Janela principal
- [X] 4.1 Criar `gui/main_window.py` com classe `MainWindow(ctk.CTk)`
- [X] 4.2 Configurar janela: título "Silence Cutter", tamanho mínimo 800x500, dark theme
- [X] 4.3 Criar layout com `grid`: sidebar na coluna 0 (peso 0, largura fixa 240px), área principal na coluna 1 (peso 1, expansível)
- [X] 4.4 Instanciar `Sidebar` e `PreviewPanel` como frames filhos
- [X] 4.5 Implementar método `on_file_selected(path: str)` que atualiza estado global
- [X] 4.6 Implementar método `on_settings_changed()` que coleta parâmetros da sidebar

### 5. Sidebar — Seleção de arquivo
- [X] 5.1 Criar `gui/sidebar.py` com classe `Sidebar(ctk.CTkFrame)`
- [X] 5.2 Configurar frame com background escuro e padding interno
- [X] 5.3 Adicionar label de seção "ARQUIVO" (uppercase, cor cinza, font pequena)
- [X] 5.4 Adicionar botão "Selecionar Arquivo" com estilo primário (#6c5ce7)
- [X] 5.5 Implementar `filedialog.askopenfilename` com filtros para formatos de vídeo (mp4, mkv, mov, avi, webm)
- [X] 5.6 Adicionar label que exibe o nome do arquivo selecionado (truncado se muito longo)
- [X] 5.7 Atualizar estado quando arquivo for selecionado

### 6. Sidebar — Controle de Threshold
- [X] 6.1 Adicionar label de seção "THRESHOLD"
- [X] 6.2 Adicionar `CTkSlider` com range -60 a 0, padrão -24, step 1
- [X] 6.3 Adicionar `CTkEntry` ao lado do slider mostrando valor atual com sufixo "dB"
- [X] 6.4 Sincronizar slider → entry: ao mover o slider, atualiza o campo de texto
- [X] 6.5 Sincronizar entry → slider: ao digitar valor, atualiza posição do slider (com validação numérica)

### 7. Sidebar — Controle de Margem
- [X] 7.1 Adicionar label de seção "MARGEM"
- [X] 7.2 Adicionar `CTkSlider` com range 0.0 a 2.0, padrão 0.2, step 0.05
- [X] 7.3 Adicionar `CTkEntry` mostrando valor com sufixo "s"
- [X] 7.4 Sincronizar slider ↔ entry (mesma lógica da task 6)

### 8. Sidebar — Controle de Corte Mínimo
- [X] 8.1 Adicionar label de seção "CORTE MÍNIMO"
- [X] 8.2 Adicionar `CTkSlider` com range 0.0 a 2.0, padrão 0.2, step 0.05
- [X] 8.3 Adicionar `CTkEntry` mostrando valor com sufixo "s"
- [X] 8.4 Sincronizar slider ↔ entry

### 9. Sidebar — Controle de Clipe Mínimo
- [X] 9.1 Adicionar label de seção "CLIPE MÍNIMO"
- [X] 9.2 Adicionar `CTkSlider` com range 0.0 a 2.0, padrão 0.1, step 0.05
- [X] 9.3 Adicionar `CTkEntry` mostrando valor com sufixo "s"
- [X] 9.4 Sincronizar slider ↔ entry

### 10. Sidebar — Botões de ação
- [X] 10.1 Adicionar botão "Pré-visualizar" com estilo outline (#6c5ce7 borda, fundo transparente)
- [X] 10.2 Adicionar botão "Processar Vídeo" com estilo sólido (#6c5ce7 fundo, texto branco, bold)
- [X] 10.3 Posicionar botões na parte inferior da sidebar com `pack(side="bottom")`
- [X] 10.4 Desabilitar ambos os botões quando nenhum arquivo está selecionado
- [X] 10.5 Conectar botão "Pré-visualizar" ao método `on_preview_click()`
- [X] 10.6 Conectar botão "Processar Vídeo" ao método `on_process_click()`

---

## Sprint 3 — GUI Área Principal (Preview + Progresso + Log)

### 11. Painel de pré-visualização
- [X] 11.1 Criar `gui/preview.py` com classe `PreviewPanel(ctk.CTkFrame)`
- [X] 11.2 Criar frame de stats com 3 colunas: "Original", "Após corte", "Silêncio removido"
- [X] 11.3 Cada coluna com valor grande (font 24, bold) e label pequeno embaixo
- [X] 11.4 Cor do valor: branco para original, #6c5ce7 para após corte, #e74c3c para silêncio
- [X] 11.5 Implementar método `update_stats(original, estimated, removed)` que atualiza os valores
- [X] 11.6 Estado inicial: mostrar "—" nos três campos até a primeira análise

### 12. Barra de progresso
- [X] 12.1 Adicionar frame de progresso abaixo dos stats
- [X] 12.2 Adicionar `CTkProgressBar` com cor gradiente (#6c5ce7)
- [X] 12.3 Adicionar label de porcentagem abaixo da barra ("0% — Aguardando...")
- [X] 12.4 Implementar método `update_progress(percent, message)` que atualiza barra e label
- [X] 12.5 Implementar método `reset_progress()` que volta ao estado inicial

### 13. Área de log
- [X] 13.1 Adicionar `CTkTextbox` com fundo escuro (#0d0d1a), somente leitura, fonte monospace
- [X] 13.2 Implementar método `append_log(line, level)` que adiciona linha com cor por nível (INFO=#6c5ce7, WARN=#e8a838, ERROR=#e74c3c)
- [X] 13.3 Implementar auto-scroll: sempre rolar para a última linha adicionada
- [X] 13.4 Implementar método `clear_log()` para limpar antes de novo processamento

### 14. Painel de resultado
- [X] 14.1 Criar frame de resultado (inicialmente oculto)
- [X] 14.2 Estilizar com fundo verde escuro (#1a3a1a), borda verde (#2d6b2d)
- [X] 14.3 Mostrar texto "Concluído!" + caminho do arquivo de saída
- [X] 14.4 Adicionar botão "Abrir Pasta" que executa `os.startfile()` no diretório do output
- [X] 14.5 Implementar método `show_result(output_path)` que exibe o frame
- [X] 14.6 Implementar método `hide_result()` que oculta ao iniciar novo processamento

---

## Sprint 4 — Integração (Conectar GUI ↔ Core)

### 15. Fluxo de pré-visualização
- [X] 15.1 No `on_preview_click()`: coletar parâmetros da sidebar
- [X] 15.2 Desabilitar botões durante análise, mostrar indicador de loading
- [X] 15.3 Executar `Analyzer.analyze()` em thread separada (evitar congelar a GUI)
- [X] 15.4 No callback de conclusão: atualizar stats no `PreviewPanel` via `after()` (thread-safe)
- [X] 15.5 Reabilitar botões após conclusão
- [X] 15.6 Exibir erro no log se a análise falhar

### 16. Fluxo de processamento
- [X] 16.1 No `on_process_click()`: coletar parâmetros da sidebar
- [X] 16.2 Ocultar resultado anterior, limpar log, resetar progresso
- [X] 16.3 Desabilitar botão "Processar", mostrar botão "Cancelar" no lugar
- [X] 16.4 Executar `Processor.process()` em thread separada
- [X] 16.5 Conectar `on_output` → `PreviewPanel.append_log()` via `after()`
- [X] 16.6 Conectar `on_progress` → `PreviewPanel.update_progress()` via `after()`
- [X] 16.7 No `on_complete`: exibir resultado se sucesso, erro no log se falha
- [X] 16.8 Restaurar botão "Processar" e reabilitar controles

### 17. Fluxo de cancelamento
- [X] 17.1 No clique do botão "Cancelar": chamar `Processor.cancel()`
- [X] 17.2 Adicionar log "Processamento cancelado pelo usuário"
- [X] 17.3 Resetar barra de progresso e restaurar botão "Processar"
- [X] 17.4 Limpar arquivo de saída parcial se existir

---

## Sprint 5 — Validações e Tratamento de Erros

### 18. Validação de entrada
- [X] 18.1 Verificar se o arquivo selecionado existe antes de processar
- [X] 18.2 Verificar se o formato é suportado (extensão em lista permitida)
- [X] 18.3 Exibir mensagem de erro clara no log se validação falhar

### 19. Validação do auto-editor
- [X] 19.1 Na inicialização do app: verificar se `bin/auto-editor.exe` existe
- [X] 19.2 Se não encontrado: exibir alerta com instruções de como baixar e onde colocar
- [X] 19.3 Desabilitar botões de ação se o binário não foi encontrado

### 20. Tratamento de erros do processamento
- [X] 20.1 Capturar stderr do subprocess e exibir no log com nível ERROR
- [X] 20.2 Tratar exit code != 0 como falha e exibir mensagem amigável
- [X] 20.3 Tratar exceções de I/O (disco cheio, permissão negada) com mensagem clara

---

## Sprint 6 — Polimento e Entrega

### 21. Polimento visual
- [X] 21.1 Ajustar espaçamentos e alinhamentos para consistência visual
- [X] 21.2 Adicionar tooltips nos sliders explicando cada parâmetro
- [ ] 21.3 Adicionar ícone da janela (favicon) — pendente: necessário fornecer arquivo .ico
- [X] 21.4 Testar redimensionamento da janela — garantir que a área principal expande corretamente

### 22. Testes manuais
- [ ] 22.1 Testar fluxo completo com vídeo curto (~30s): selecionar → pré-visualizar → processar → abrir pasta
- [ ] 22.2 Testar cancelamento no meio do processamento
- [ ] 22.3 Testar com arquivo inexistente
- [ ] 22.4 Testar com formato não suportado
- [ ] 22.5 Testar sem auto-editor.exe na pasta bin/
- [ ] 22.6 Testar variação dos parâmetros (threshold extremos, margem 0)
- [ ] 22.7 Verificar que o vídeo gerado abre corretamente no CapCut

### 23. Documentação mínima
- [X] 23.1 Criar seção no tasks01.md com resultado da revisão final
- [X] 23.2 Verificar que todos os itens acima estão marcados

---

## Revisão Final

- **Resultado:** Implementação completa das Sprints 1–6 (código). Testes manuais pendentes (Task 22).
- **Verificações executadas:**
  - Importação de todos os módulos sem erro
  - App inicia corretamente (MainWindow + Sidebar + PreviewPanel)
  - Grid layout com redimensionamento funcional
  - Validação de entrada (arquivo existe + formato suportado)
  - Verificação do binário auto-editor na inicialização
  - Tooltips nos 4 sliders
  - Fluxos de preview, processamento e cancelamento integrados via threads
- **Observações:**
  - Task 21.3 (ícone): pendente — necessário fornecer arquivo `.ico`
  - Task 22 (testes manuais): requer auto-editor.exe na pasta `bin/` e um vídeo de teste
  - O processador já trata stderr, exit codes e exceções de I/O com mensagens no log
