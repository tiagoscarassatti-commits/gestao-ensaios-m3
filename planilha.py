"""Leitura e gravação da planilha da rede (Rede complementar *.xlsx).

A gravação é feita direto no XML da aba "Resumo", mexendo só nas células
PLANTIO REAL, JANELA REAL e Semeado da linha escolhida. Assim o Excel mantém
fórmulas, comentários, filtros e validações exatamente como estavam
(o openpyxl, ao salvar, perderia os comentários modernos da planilha).
"""
from datetime import date, datetime
from pathlib import Path
import os
import re
import shutil
import tempfile
import zipfile

ABA = 'Resumo'
NS_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


class PlanilhaAberta(Exception):
    """A planilha está aberta no Excel (Windows bloqueia a gravação)."""


def janela(micro, d):
    """Mesma regra da fórmula da coluna JANELA REAL."""
    if not d:
        return ''
    m = int(str(micro).replace('M', '').replace('.0', ''))
    limites = {301: ((10, 5), (10, 25)), 302: ((10, 15), (11, 11)),
               303: ((10, 15), (11, 11)), 304: ((10, 30), (11, 14))}
    if m not in limites:
        return '—'
    (am, ad), (im, idd) = limites[m]
    if d <= date(d.year, am, ad):
        return 'Abertura'
    if d <= date(d.year, im, idd):
        return 'Intermediário'
    return 'Fechamento'


def _serial(d, base1904):
    base = date(1904, 1, 1) if base1904 else date(1899, 12, 30)
    return (d - base).days


def _caminho_aba(z):
    wb = z.read('xl/workbook.xml').decode('utf-8')
    m = re.search(r'<sheet\b[^>]*\bname="%s"[^>]*>' % re.escape(ABA), wb)
    if not m:
        raise ValueError('Aba "%s" não encontrada na planilha.' % ABA)
    rid = re.search(r'\br:id="([^"]+)"', m.group(0)).group(1)
    rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
    for rel in re.findall(r'<Relationship\b[^>]*>', rels):
        if re.search(r'\bId="%s"' % re.escape(rid), rel):
            alvo = re.search(r'\bTarget="([^"]+)"', rel).group(1)
            alvo = alvo.lstrip('/')
            return alvo if alvo.startswith('xl/') else 'xl/' + alvo
    raise ValueError('Não foi possível localizar a aba "%s".' % ABA)


_ATTRS = r'(?:\s+[\w:]+="[^"]*")*'


def _celula(xml_linha, ref):
    """Retorna o match da célula `ref` dentro do XML da linha (ou None)."""
    return re.search(r'<c r="%s"(%s)\s*(?:/>|>(.*?)</c>)' % (ref, _ATTRS), xml_linha, re.S)


def _col_idx(col):
    n = 0
    for ch in col:
        n = n * 26 + ord(ch) - 64
    return n


def _definir_valor(xml_linha, ref, novo_conteudo, tipo=None):
    """Troca o valor da célula, mantendo estilo (s) e fórmula (<f>) se houver."""
    m = _celula(xml_linha, ref)
    if m:
        attrs = re.sub(r'\s+r="[^"]*"', '', m.group(1))
        attrs = re.sub(r'\s+t="[^"]*"', '', attrs)
        dentro = m.group(2) or ''
        formula = re.search(r'<f\b.*?(?:/>|</f>)', dentro, re.S)
        corpo = (formula.group(0) if formula else '') + novo_conteudo
        t = ' t="%s"' % tipo if tipo else ''
        nova = '<c r="%s"%s%s>%s</c>' % (ref, attrs, t, corpo) if corpo else '<c r="%s"%s%s/>' % (ref, attrs, t)
        return xml_linha[:m.start()] + nova + xml_linha[m.end():]
    if not novo_conteudo:
        return xml_linha
    # célula não existe: insere na posição certa da linha
    col = re.match(r'[A-Z]+', ref).group(0)
    t = ' t="%s"' % tipo if tipo else ''
    nova = '<c r="%s"%s>%s</c>' % (ref, t, novo_conteudo)
    for c in re.finditer(r'<c r="([A-Z]+)\d+"', xml_linha):
        if _col_idx(c.group(1)) > _col_idx(col):
            return xml_linha[:c.start()] + nova + xml_linha[c.start():]
    fim = xml_linha.rfind('</row>')
    if fim < 0:  # <row .../> vazia
        return xml_linha[:-2] + '>' + nova + '</row>'
    return xml_linha[:fim] + nova + xml_linha[fim:]


def _col_letra(cabecalho, nome):
    alvo = nome.strip().lower()
    for i, h in enumerate(cabecalho):
        if str(h or '').strip().lower() == alvo:
            n, s = i + 1, ''
            while n:
                n, r = divmod(n - 1, 26)
                s = chr(65 + r) + s
            return s
    raise ValueError('Coluna "%s" não encontrada na aba %s.' % (nome, ABA))


def gravar_semeadura(arquivo, linha, micro, cabecalho, data_semeadura, pasta_backup):
    """Grava (ou apaga, se data_semeadura=None) a data de semeadura de uma linha."""
    arquivo = Path(arquivo)
    cP = _col_letra(cabecalho, 'PLANTIO REAL')
    cQ = _col_letra(cabecalho, 'JANELA REAL')
    cR = _col_letra(cabecalho, 'Semeado')

    with zipfile.ZipFile(arquivo) as z:
        aba = _caminho_aba(z)
        xml = z.read(aba).decode('utf-8')
        base1904 = 'date1904="1"' in z.read('xl/workbook.xml').decode('utf-8') or \
                   "date1904=\"true\"" in z.read('xl/workbook.xml').decode('utf-8')
        itens = [(i, z.read(i.filename)) for i in z.infolist()]

    m = re.search(r'<row r="%d"%s\s*(?:/>|>.*?</row>)' % (linha, _ATTRS), xml, re.S)
    if not m:
        raise ValueError('Linha %d não encontrada na planilha.' % linha)
    xr = m.group(0)
    if data_semeadura:
        xr = _definir_valor(xr, '%s%d' % (cP, linha), '<v>%d</v>' % _serial(data_semeadura, base1904))
        xr = _definir_valor(xr, '%s%d' % (cQ, linha), '<v>%s</v>' % janela(micro, data_semeadura), 'str')
        xr = _definir_valor(xr, '%s%d' % (cR, linha), '<v>Sim</v>', 'str')
    else:
        xr = _definir_valor(xr, '%s%d' % (cP, linha), '')
        xr = _definir_valor(xr, '%s%d' % (cQ, linha), '<v/>', 'str')
        xr = _definir_valor(xr, '%s%d' % (cR, linha), '<v>Não</v>', 'str')
    novo_xml = xml[:m.start()] + xr + xml[m.end():]

    # cópia de segurança antes de gravar (mantém as 40 mais recentes)
    pasta_backup = Path(pasta_backup)
    pasta_backup.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy2(arquivo, pasta_backup / ('%s_%s%s' % (arquivo.stem, carimbo, arquivo.suffix)))
    antigos = sorted(pasta_backup.glob(arquivo.stem + '_*' + arquivo.suffix))
    for velho in antigos[:-40]:
        velho.unlink(missing_ok=True)

    fd, tmp = tempfile.mkstemp(suffix='.xlsx', dir=arquivo.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, 'w') as out:
            for info, dados in itens:
                if info.filename == aba:
                    dados = novo_xml.encode('utf-8')
                out.writestr(info, dados, compress_type=zipfile.ZIP_DEFLATED)
        try:
            os.replace(tmp, arquivo)
        except PermissionError:
            raise PlanilhaAberta()
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
