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

## Atualização automática (sem baixar ZIP)

Configure uma vez e o `iniciar_dashboard.bat` passa a buscar sozinho a versão mais nova no GitHub toda vez que você abre o painel. A pasta `dados/` nunca é tocada. Se estiver sem internet, ele só abre a versão atual.

1. No GitHub: foto do perfil → **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. Dê um nome (ex.: `painel-m3`) e uma validade (ex.: 1 ano).
3. Em **Repository access**, escolha *Only select repositories* → `gestao-ensaios-m3`.
4. Em **Permissions → Repository permissions → Contents**, escolha **Read-only**.
5. Gere o token, copie e salve num arquivo chamado `token_github.txt` aqui na pasta do painel, só com o token dentro.

O token só dá permissão de leitura neste repositório e não vai para o GitHub (está no `.gitignore`).

Dica: clique com o botão direito no `iniciar_dashboard.bat` → *Enviar para → Área de trabalho (criar atalho)* para abrir com um clique.

Sem o token, dá para atualizar à mão: *Code → Download ZIP* no GitHub e extrair por cima da pasta. A pasta `dados/` não está no ZIP, então seus registros ficam intactos.

## Abas

- **Progresso de semeadura:** situação por microrregião na data escolhida no topo, com indicadores, as últimas semeaduras e os locais que faltam semear.
- **Histórico na data:** safra atual (DES) comparada às anteriores no mesmo dia/mês, com gráfico da evolução acumulada.
- **Janelas de semeadura:** % de locais em Abertura, Intermediário e Fechamento, com filtro por área (Desenvolvimento/Pesquisa) e região, na data escolhida no topo.
- **Registrar semeadura:** registrar, corrigir ou desfazer a data de semeadura de cada local.
- **Análise de estande:** versão anterior, sem alterações (será refeita).

Sem data escolhida, o painel mostra sempre o dia de hoje. Ele relê a planilha a cada 5 minutos e vira o dia sozinho à meia-noite.

A planilha precisa estar **fechada no Excel** na hora de registrar uma semeadura, porque o Windows bloqueia a gravação de arquivo aberto.

## Janelas de semeadura

| Janela | M301 | M302 ou M303 | M304 |
|---|---|---|---|
| Abertura | até 05/10 | até 15/10 | até 25/10 |
| Intermediário | 06/10 a 20/10 | 16/10 a 04/11 | 26/10 a 05/11 |
| Fechamento | a partir de 21/10 | a partir de 05/11 | a partir de 06/11 |

A regra está em `planilha.py` (função `janela`) e também na fórmula da coluna JANELA REAL da planilha.
