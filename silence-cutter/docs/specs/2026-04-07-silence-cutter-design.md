# Silence Cutter — Design Spec

## Objetivo

Aplicação desktop GUI que remove automaticamente silêncios de vídeos, gerando um arquivo pronto para edição no CapCut. Usa o auto-editor como engine de processamento.

## Fluxo do Usuário

1. Abre o app e seleciona um vídeo
2. Ajusta parâmetros (ou usa padrões)
3. Clica "Pré-visualizar" para ver estimativas (duração original, estimada, silêncio removido)
4. Clica "Processar Vídeo" — barra de progresso + log em tempo real
5. Ao finalizar — mensagem de sucesso + botão "Abrir Pasta"

## Arquitetura

- **GUI:** Python + CustomTkinter (dark theme nativo)
- **Engine:** auto-editor binário (`.exe`, baixado do GitHub releases v30.1.0)
- **Comunicação:** `subprocess` capturando stdout para progresso e log

## Estrutura de Arquivos

```
silence-cutter/
├── app.py              # Entry point
├── gui/
│   ├── main_window.py  # Janela principal com sidebar
│   ├── sidebar.py      # Painel de controles
│   └── preview.py      # Painel de preview + progresso
├── core/
│   ├── processor.py    # Chama auto-editor via subprocess
│   └── analyzer.py     # Roda --stats para pré-visualização
├── bin/
│   └── auto-editor.exe # Binário do auto-editor
└── requirements.txt
```

## Layout da GUI — Sidebar

Layout com sidebar à esquerda e área principal à direita.

### Sidebar (esquerda, ~200px)

- Botão "Selecionar Arquivo" + nome do arquivo selecionado
- Slider + input para Threshold (-60dB a 0dB, padrão -24dB)
- Slider + input para Margem (0s a 2s, padrão 0.2s)
- Slider + input para Corte Mínimo (0s a 2s, padrão 0.2s)
- Slider + input para Clipe Mínimo (0s a 2s, padrão 0.1s)
- Botão "Pré-visualizar" (roda `--stats`)
- Botão "Processar Vídeo" (destaque principal, cor #6c5ce7)

### Área Principal (direita)

- Painel de pré-visualização: duração original, estimada após corte, silêncio removido
- Barra de progresso durante processamento
- Log de status (mensagens do auto-editor em tempo real)
- Ao finalizar: caminho do arquivo de saída + botão "Abrir Pasta"

## Parâmetros e Mapeamento para auto-editor

| Parâmetro GUI     | Flag auto-editor              | Padrão  |
|-------------------|-------------------------------|---------|
| Threshold         | `--edit audio:{valor}dB`      | -24dB   |
| Margem            | `--margin {valor}s`           | 0.2s    |
| Corte Mínimo      | `--smooth {valor}s,{clipe}s`  | 0.2s    |
| Clipe Mínimo      | `--smooth {corte}s,{valor}s`  | 0.1s    |

## Saída

- Arquivo gerado no mesmo diretório do original com sufixo `_cut`
- Exemplo: `meu-video.mp4` → `meu-video_cut.mp4`
- Mesmo formato/codec do original (auto-editor preserva por padrão)

## Pré-visualização

- Executa `auto-editor input.mp4 --stats` com os parâmetros configurados
- Parseia a saída para extrair: duração original, duração estimada, tempo de silêncio
- Exibe na área principal sem processar o vídeo

## Tratamento de Erros

- **Arquivo inválido:** Mensagem na área principal se o formato não for suportado
- **auto-editor não encontrado:** Alerta pedindo para colocar o binário na pasta `bin/`
- **Falha no processamento:** Log do erro exibido na área de status
- **Cancelamento:** Botão "Cancelar" aparece durante processamento (mata o subprocess)

## Dependências

- Python 3.10+
- `customtkinter`
- auto-editor binário v30.1.0 na pasta `bin/`

## Testes

- Verificar comando montado para cada combinação de parâmetros
- Testar fluxo completo com vídeo curto (~30s)
- Testar cancelamento durante processamento
- Testar com arquivo inexistente e formato inválido
