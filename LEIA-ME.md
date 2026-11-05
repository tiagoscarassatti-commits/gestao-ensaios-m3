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

Na **primeira vez** que você abre o `iniciar_dashboard.bat`:

- ele cria o atalho **Gestao de Ensaios M3** na área de trabalho;
- abre a página do GitHub para gerar um token de leitura. Nela, em *Repository access*, escolha *Only select repositories* → `gestao-ensaios-m3`, confira *Contents = Read-only*, clique em *Generate token* e cole o token na janela preta.

Depois disso, cada vez que abrir pelo atalho, o painel busca sozinho a versão mais nova no GitHub. A pasta `dados/` nunca é tocada, e se estiver sem internet ele só abre a versão atual.

O token fica salvo em `token_github.txt`, só lê este repositório e não vai para o GitHub. Para refazer a configuração, apague esse arquivo. Para pular, tecle Enter sem colar nada.

## Abas

- **Progresso de semeadura:** situação por microrregião na data escolhida no topo, com indicadores, as últimas semeaduras e os locais que faltam semear.
- **Histórico na data:** safra atual (DES) comparada às anteriores no mesmo dia/mês, com gráfico da evolução acumulada.
- **Janelas de semeadura:** % de locais em Abertura, Intermediário e Fechamento, com filtro por área (Desenvolvimento/Pesquisa) e região, na data escolhida no topo.
- **Registrar semeadura:** registrar, corrigir ou desfazer a data de semeadura de cada local.
- **Análise de estande:** filtros por região, localidade, tipo (Filtro, Comercial, Concorrente, Lançamento, Linhagem), material e faixa de diferença de população, divididos em:
  - *Visão geral:* quantas parcelas estão na faixa escolhida, situação (ruim ≤ −15%, atenção, adequado), histograma em que clicar ou arrastar mostra os materiais da faixa, e localidades comparadas com o Filtro (NEO680);
  - *Ajuste de semeadura:* cultivares com −10% ou pior em várias localidades e o aumento de sementes sugerido, por região (exporta CSV);
  - *Piores e melhores cultivares:* ranking pela diferença média, incluindo a comparação com o Filtro (NEO680) do mesmo local;
  - *Mapa de calor:* cultivar × localidade;
  - *Parcelas:* tabela completa, ordenável, com exportação;
  - *Arquivos e importação:* inclui planilhas novas (arrastar e soltar), mostra o que foi lido e os nomes unificados.

Sem data escolhida, o painel mostra sempre o dia de hoje. Ele relê a planilha a cada 5 minutos e vira o dia sozinho à meia-noite.

A planilha precisa estar **fechada no Excel** na hora de registrar uma semeadura, porque o Windows bloqueia a gravação de arquivo aberto.

## Janelas de semeadura

| Janela | M301 | M302 ou M303 | M304 |
|---|---|---|---|
| Abertura | até 05/10 | até 15/10 | até 25/10 |
| Intermediário | 06/10 a 20/10 | 16/10 a 04/11 | 26/10 a 05/11 |
| Fechamento | a partir de 21/10 | a partir de 05/11 | a partir de 06/11 |

A regra está em `planilha.py` (função `janela`) e também na fórmula da coluna JANELA REAL da planilha.

## Planilhas de estande

Cada região pode ter o seu modelo. O painel acha sozinho as colunas de **material** e **diferença (%)**: "Diferença do real" (M301), "Dif" em fração (M303, aba Planilha1) ou "POP %" (M304). Se a diferença não estiver na planilha, ele calcula a partir da população recomendada e do estande.

A localidade sai do nome do arquivo (ex.: `Estande Inicial - Rio Verde_2.xlsx`) ou da coluna "Ensaio". Se você mandar duas planilhas da mesma localidade, vale a mais recente.

Os nomes dos materiais são unificados: maiúsculas/minúsculas, acentos, espaços, marca (BRASMAX, STINE, DAGMA/DAG), tecnologia (I2X, IPRO, CE) e "Pop 1/Pop 3" não diferenciam o material. Assim, `DAG 6525 I2X`, `6525 I2X` e `DAGMA 6525 I2X POP 3` contam como o mesmo, e `SBQ 268809` = `SBQ268809`. Para casos que escaparem, use `dados/apelidos_materiais.csv` (`grafia;nome padrão`).

## Corrigir a população de um material numa planilha de estande

1. Menu **Arquivos e importação** → **Abrir no Excel** na planilha.
2. Corrija a população recomendada (Pop. Rec. / Densidade Final / Dens. Final) dos materiais.
3. **Salve e feche** o Excel. A diferença (%) é recalculada pelas fórmulas da planilha.
4. Clique em **↻ Atualizar dados** no menu.

Também dá para corrigir a planilha em outro lugar e arrastar de novo em *Incluir avaliações*. Se o nome do arquivo for o mesmo, ela substitui a antiga.
