"""Leitura das planilhas de estande inicial (uma por localidade).

Cada região manda um formato diferente; o leitor procura o cabeçalho certo em
qualquer aba e sempre extrai a diferença (%) entre o estande e a população
recomendada:

- M301 (modelo "Avaliações REDE"): Variedade | Pop. Rec. | Estande | Diferença do real
- M303 (export + "Planilha1"):     Nome Comercial | Densidade Final | POP Final | Dif (fração)
- M304 (Planaltina/Unaí):          Produto | (categoria) | Dens. Final | GERM | VIGOR | Plantas/ha | POP %

Os nomes dos materiais são unificados por uma chave (sem acento, sem espaço,
sem marca BRASMAX/STINE/DAGMA, sem tecnologia I2X/IPRO/CE e sem "Pop n"),
para que grafias diferentes contem como o mesmo material.
Para casos que a regra não pega, use dados/apelidos_materiais.csv.
"""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import re
import unicodedata

from openpyxl import load_workbook

UP = Path(__file__).parent / 'dados' / 'uploads'
APELIDOS = None  # definido pelo app.py
LOCAIS_REDE = []  # [(nome, micro)] definido pelo app.py a partir da planilha da rede

# localidades conhecidas caso a planilha da rede não tenha a localidade
LOCAIS_PADRAO = {
    'RIO VERDE': '301', 'JATAI': '301', 'MONTIVIDIU': '301',
    'ARAGUARI': '303', 'MONTE CARMELO': '303', 'UBERABA': '303', 'PATOS DE MINAS': '303', 'TUPACIGUARA': '303',
    'CABECEIRAS': '304', 'BURITIS': '304', 'PLANALTINA': '304', 'CRISTALINA': '304', 'UNAI': '304',
}
MARCAS = ('BRASMAX', 'STINE', 'DAGMA', 'DAG')
TECNOLOGIAS = {'I2X', 'IPRO', 'CE', 'RR', 'RR2', 'E3', 'XTD', 'XTEND', 'CONV', 'IPRO.'}
CATEGORIAS = {'FILTRO': 'Testemunha', 'CHECK': 'Testemunha', 'TESTEMUNHA': 'Testemunha',
              'COMERCIAL': 'Comercial', 'CONCORRENTE': 'Concorrente', 'CONCORRENTES': 'Concorrente',
              'LANCAMENTO': 'Lançamento', 'LINHAGEM': 'Linhagem', 'POPULACAO': None}


def plain(v):
    s = str(v if v is not None else '').strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s)


def num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(',', '.'))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- materiais
def carregar_apelidos():
    """dados/apelidos_materiais.csv:  variante;nome padrão  (uma por linha)."""
    m = {}
    if APELIDOS and Path(APELIDOS).exists():
        with open(APELIDOS, encoding='utf-8-sig') as fh:
            for linha in csv.reader(fh, delimiter=';'):
                if len(linha) >= 2 and linha[0].strip() and not linha[0].startswith('#'):
                    m[plain(linha[0])] = linha[1].strip()
    return m


def separar(nome_bruto, apelidos):
    """Retorna (nome de exibição, chave, variação de população, outra origem)."""
    s = re.sub(r'\s+', ' ', str(nome_bruto).strip().upper())
    s = re.sub(r'\s+', ' ', str(apelidos.get(plain(s), s)).strip().upper())
    pop = None
    m = re.search(r'\bPOP\.?\s*(\d)\b', s)
    if m:
        pop = 'Pop ' + m.group(1)
        s = (s[:m.start()] + s[m.end():]).strip()
    origem = None
    m = re.search(r'\(([^)]*)\)', s)
    if m:
        origem = m.group(1).strip().title()
        s = (s[:m.start()] + s[m.end():]).strip()
    s = re.sub(r'\s+', ' ', s).strip(' -')
    exibicao = s + (' (' + origem + ')' if origem else '')
    # chave
    tokens = [t for t in plain(s).split(' ') if t not in TECNOLOGIAS]
    k = ''.join(tokens)
    for marca in MARCAS:
        if k.startswith(marca) and len(k) > len(marca):
            k = k[len(marca):]
            break
    k = re.sub(r'(?<=\d)(I2X|IPRO|CE|RR)$', '', k)
    if origem:
        k += '#' + plain(origem)
    return exibicao, k, pop, origem


# ---------------------------------------------------------------- localidade
def _base_num(s):
    s = plain(s).replace('_', ' ')
    s = re.sub(r'\(\d+\)', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def titulo(s):
    return ' '.join(w.lower() if w in ('DE', 'DA', 'DO', 'DOS', 'DAS') else w.title() for w in s.split(' '))


def localizar(texto):
    """Acha localidade e micro a partir do nome do arquivo ou da coluna Ensaio."""
    t = _base_num(texto)
    t = re.sub(r'^ESTANDE( INICIAL)?( -)? ', '', t)
    candidatos = defaultdict(dict)  # base -> {numero: (nome, micro)}
    for nome, micro, cond in LOCAIS_REDE:
        b = _base_num(nome)
        m = re.match(r'^(.*?)[ ]?(\d+)$', b)
        base, n = (m.group(1).strip(), m.group(2)) if m else (b, '1')
        atual = candidatos[base].get(n)
        if not atual or cond == 'DES':  # na dúvida, vale a localidade de Desenvolvimento
            candidatos[base][n] = (titulo(base) + '_' + n, str(micro))
    for base, micro in LOCAIS_PADRAO.items():
        candidatos[base].setdefault('1', (titulo(base) + '_1', micro))
    for base in sorted(candidatos, key=len, reverse=True):
        if re.search(r'(^|\s)' + re.escape(base) + r'(\s|$|\d)', t):
            resto = t[t.find(base) + len(base):]
            m = re.match(r'\s*(\d)(?!\d)', resto)
            nums = candidatos[base]
            n = m.group(1) if m else ('1' if '1' in nums or len(nums) != 1 else next(iter(nums)))
            if n in nums:
                return nums[n]
            micro = next(iter(nums.values()))[1]
            return titulo(base) + '_' + n, micro
    return Path(str(texto)).stem, '?'


# ---------------------------------------------------------------- leitura
NOMES = ('VARIEDADE', 'NOME COMERCIAL', 'PRODUTO', 'MATERIAL NAME', 'CULTIVAR', 'MATERIAL')
DIFS = ('DIFERENCA DO REAL', 'DIF', 'DIF %', 'DIF.', 'POP %', 'DIFERENCA', 'DIF POP', 'DIF. POP')
ALVOS = ('POP. REC.', 'POP REC', 'POP. REC', 'POP RECOMENDADA', 'DENSIDADE FINAL', 'DENS. FINAL', 'DENS FINAL', 'POPULACAO')
ESTANDES = ('ESTANDE', 'POP FINAL', 'PLANTAS/HA', 'ESTANDE INICIAL')


def _col(h, opcoes):
    for o in opcoes:
        if o in h:
            return h.index(o)
    return None


def _ler_aba(ws):
    linhas = list(ws.iter_rows(values_only=True))
    for i, r in enumerate(linhas[:25]):
        h = [plain(x) for x in r]
        cn, cd = _col(h, NOMES), _col(h, DIFS)
        ca, ce = _col(h, ALVOS), _col(h, ESTANDES)
        if cn is None or (cd is None and (ca is None or ce is None)):
            continue
        cg, cv = _col(h, ('GERM. (%)', 'GERM (%)', 'GERM', '% GERM', 'GERMINACAO')), _col(h, ('VIGOR (%)', 'VIGOR'))
        cp = _col(h, ('PCL', 'PARCELA', 'Nº PARCELA', 'N PARCELA'))
        cl = _col(h, ('ENSAIO',))
        corpo = [x for x in linhas[i + 1:] if cn < len(x) and x[cn] not in (None, '')]
        # coluna de categoria (sem cabeçalho no modelo M304): procura valores conhecidos
        ccat = None
        for j in range(len(h)):
            vals = [plain(x[j]) for x in corpo[:40] if j < len(x) and x[j]]
            if vals and sum(v in CATEGORIAS for v in vals) >= max(3, len(vals) // 2):
                ccat = j
                break
        # escala da diferença: "Dif" em fração (-0,12) vira % (-12)
        fracao = False
        if cd is not None and h[cd] in ('DIF', 'DIF.'):
            vs = [abs(num(x[cd])) for x in corpo if cd < len(x) and num(x[cd]) is not None]
            fracao = bool(vs) and max(vs) <= 2
        regs = []
        for x in corpo:
            g = lambda c: x[c] if c is not None and c < len(x) else None
            nome = str(g(cn)).strip()
            if plain(nome).startswith(('PREENCHIMENTO', 'FILL', 'BORDADURA', 'TOTAL', 'MEDIA')):
                continue
            alvo, est, dif = num(g(ca)), num(g(ce)), num(g(cd))
            if dif is not None and fracao:
                dif *= 100
            if dif is None and alvo and est:
                dif = (est / alvo - 1) * 100
            if dif is None or abs(dif) > 300:
                continue
            if est is None and alvo:
                est = alvo * (1 + dif / 100)
            regs.append({'raw': nome, 'alvo': alvo, 'estande': est, 'dif': round(dif, 2),
                         'germ': num(g(cg)), 'vigor': num(g(cv)),
                         'pcl': None if g(cp) is None else str(g(cp)).replace('.0', ''),
                         'cat': CATEGORIAS.get(plain(g(ccat))) if ccat is not None else None,
                         'ensaio': g(cl)})
        if regs:
            formato = {'DIFERENCA DO REAL': 'Modelo M301', 'POP %': 'Modelo M304'}.get(h[cd] if cd is not None else '', 'Modelo M303' if fracao else 'Genérico')
            return regs, formato
    return None, None


def ler_arquivo(p, apelidos):
    wb = load_workbook(p, data_only=True, read_only=True)
    try:
        for ws in wb.worksheets:
            regs, formato = _ler_aba(ws)
            if regs:
                break
        else:
            raise ValueError('Não encontrei as colunas de material e diferença (%) em nenhuma aba.')
    finally:
        wb.close()
    ens = next((r['ensaio'] for r in regs if r['ensaio']), None)
    local, micro = localizar(ens) if ens else localizar(p.stem)
    if micro == '?' and ens:
        local, micro = localizar(p.stem)
    for r in regs:
        r['grafia'] = re.sub(r'\s+', ' ', r['raw'].strip())
        nome, chave, pop, origem = separar(r.pop('raw'), apelidos)
        r.pop('ensaio')
        r.update({'nome': nome, 'k': chave, 'pop': pop, 'origem': origem, 'local': local,
                  'micro': 'M' + micro if micro != '?' else '?', 'arquivo': p.name})
    return regs, formato, local, micro


def scan():
    apelidos = carregar_apelidos()
    arquivos, por_local = [], defaultdict(list)
    for p in sorted(UP.glob('*.xlsx')):
        if p.name.startswith('~$'):
            continue
        try:
            regs, formato, local, micro = ler_arquivo(p, apelidos)
            por_local[local].append((p.stat().st_mtime, p, regs))
            arquivos.append({'arquivo': p.name, 'ok': True, 'formato': formato, 'local': local,
                             'micro': 'M' + micro if micro != '?' else '?', 'parcelas': len(regs),
                             'materiais': len({r['k'] for r in regs})})
        except Exception as e:  # noqa: BLE001 - mostra o erro no painel
            arquivos.append({'arquivo': p.name, 'ok': False, 'erro': str(e)})
    parcelas = []
    for local, lista in por_local.items():
        lista.sort(key=lambda t: t[0], reverse=True)
        parcelas += lista[0][2]
        for _, p, _ in lista[1:]:  # mesma localidade em dois arquivos: vale o mais recente
            for a in arquivos:
                if a['arquivo'] == p.name:
                    a['ignorado'] = 'Mesma localidade de ' + lista[0][1].name + ' (vale o arquivo mais recente)'
    # nome de exibição e tipo únicos por material
    nomes, cats, variantes = defaultdict(Counter), defaultdict(Counter), defaultdict(set)
    for r in parcelas:
        nomes[r['k']][r['nome']] += 1
        variantes[r['k']].add(r['grafia'])
        if r['cat']:
            cats[r['k']][r['cat']] += 1
    for r in parcelas:
        r['nome'] = max(nomes[r['k']].items(), key=lambda kv: (kv[1], len(kv[0])))[0]
        if r['k'].startswith('SB'):
            r['tipo'] = 'Linhagem'
        elif cats[r['k']]:
            r['tipo'] = cats[r['k']].most_common(1)[0][0]
        else:
            r['tipo'] = 'Sem classificação'
        del r['cat'], r['grafia']
    unificados = [{'nome': max(nomes[k].items(), key=lambda kv: (kv[1], len(kv[0])))[0], 'variantes': sorted(v)}
                  for k, v in variantes.items() if len(v) > 1]
    unificados.sort(key=lambda u: u['nome'])
    return {'parcelas': parcelas, 'arquivos': arquivos, 'unificados': unificados}
