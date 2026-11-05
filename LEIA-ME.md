# Gestão de Ensaios M3

Painel local de progresso de semeadura, histórico na data e análise de estande.

## Como abrir

1. Dê dois cliques em `iniciar_dashboard.bat`.
2. O navegador abre em **http://localhost:8110**. Deixe a janela preta aberta enquanto usa o painel.

Requer Python com `openpyxl`. O `.bat` instala o `openpyxl` sozinho se faltar.

## Onde ficam os dados

- `dados/`: planilhas usadas pelo painel. É aqui que o painel grava as semeaduras.
  - `Rede complementar 2026.xlsx`: locais da safra atual. O painel grava na coluna **PLANTIO REAL**, e as colunas *JANELA REAL* e *Semeado* continuam com as fórmulas.
  - `M3_plantio_historico.xlsx`: histórico das safras anteriores (aba BASE).
  - `uploads/`: planilhas de estande.
  - `backups/`: cópia automática da planilha antes de cada gravação (guarda as 40 últimas).
  - `registro_semeaduras.csv`: log de tudo que foi registrado ou removido pelo painel.
- `dados_iniciais/`: cópia de partida. Só é usada na primeira execução, quando `dados/` ainda não existe.

A pasta `dados/` **não vai para o GitHub** e nunca é sobrescrita quando você baixa uma versão nova do painel.

Para trocar de safra, coloque a nova `Rede complementar AAAA.xlsx` em `dados/`. O painel usa a de nome mais recente.

## Atualizar o painel

- **Com git:** `git pull` dentro da pasta.
- **Sem git:** no GitHub, *Code → Download ZIP*, e extraia por cima da pasta atual. Como a pasta `dados/` não está no ZIP, seus registros ficam intactos.

## Abas

- **Progresso de semeadura:** situação por microrregião na data escolhida no topo, com indicadores, as últimas semeaduras e os locais que faltam semear.
- **Histórico na data:** safra atual (DES) comparada às anteriores no mesmo dia/mês, com gráfico da evolução acumulada.
- **Registrar semeadura:** registrar, corrigir ou desfazer a data de semeadura de cada local.
- **Análise de estande:** versão anterior, sem alterações (será refeita).

Sem data escolhida, o painel mostra sempre o dia de hoje. Ele relê a planilha a cada 5 minutos e vira o dia sozinho à meia-noite.

A planilha precisa estar **fechada no Excel** na hora de registrar uma semeadura, porque o Windows bloqueia a gravação de arquivo aberto.
