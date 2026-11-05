"""Gestão de Ensaios M3 — servidor local (http://localhost:8110)."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from datetime import date, datetime
import csv
import json
import shutil
import threading
import webbrowser

from openpyxl import load_workbook

import estande_module as E
import planilha as P

PORTA = 8110
RAIZ = Path(__file__).parent
DADOS = RAIZ / 'dados'
INICIAIS = RAIZ / 'dados_iniciais'
GRUPOS = ['M301 + M302', 'M303', 'M304']
TRAVA = threading.Lock()


def preparar_dados():
    """Na primeira execução copia as planilhas iniciais para a pasta dados/.
    A pasta dados/ nunca é sobrescrita por atualizações do painel."""
    DADOS.mkdir(exist_ok=True)
    if not any(DADOS.glob('Rede complementar*.xlsx')):
        for f in INICIAIS.glob('Rede complementar*.xlsx'):
            shutil.copy2(f, DADOS / f.name)
    if not any(DADOS.glob('M3_*hist*.xlsx')):
        for f in INICIAIS.glob('M3_*hist*.xlsx'):
            shutil.copy2(f, DADOS / f.name)
    up = DADOS / 'uploads'
    if not up.exists():
        shutil.copytree(INICIAIS / 'uploads', up)
    E.UP = up


def arq_rede():
    fs = sorted(DADOS.glob('Rede complementar*.xlsx'))
    if not fs:
        raise FileNotFoundError('Coloque a planilha "Rede complementar AAAA.xlsx" na pasta dados.')
    return fs[-1]


def arq_hist():
    fs = sorted(DADOS.glob('M3_*hist*.xlsx'))
    if not fs:
        raise FileNotFoundError('Coloque a planilha de histórico (M3_plantio_historico.xlsx) na pasta dados.')
    return fs[-1]


def grupo(v):
    s = str(v).replace('.0', '').replace('M', '').strip()
    return {'301': 'M301 + M302', '302': 'M301 + M302', '303': 'M303', '304': 'M304'}.get(s, 'Outros')


def como_data(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return None


def iso(d):
    return d.isoformat() if d else None


def ler_rede():
    f = arq_rede()
    wb = load_workbook(f, data_only=True, read_only=True)
    ws = wb[P.ABA]
    linhas = ws.iter_rows(values_only=True)
    cab = [c for c in next(linhas)]
    idx = {str(h or '').strip().upper(): i for i, h in enumerate(cab)}

    def pega(r, nome):
        i = idx.get(nome)
        return r[i] if i is not None and i < len(r) else None

    cur, safra = [], None
    for n, r in enumerate(linhas, start=2):
        loc = pega(r, 'LOCALIDADE')
        if not loc:
            continue
        safra = safra or str(pega(r, 'SAFRA') or '')
        micro = str(pega(r, 'MICRO') or '').replace('.0', '')
        real = como_data(pega(r, 'PLANTIO REAL'))
        cur.append({
            'row': n,
            'loc': str(loc).strip(),
            'micro': micro,
            'g': grupo(micro),
            'c': str(pega(r, 'CONDUÇÃO') or '').strip().upper(),
            'resp': str(pega(r, 'RESPONSAVEL') or '').strip().title(),
            'tipo': str(pega(r, 'TIPO ENSAIO') or '').strip(),
            'real': iso(real),
            'janReal': P.janela(micro, real) if real else '',
        })
    wb.close()
    return f, cab, cur, safra


def ler_hist():
    wb = load_workbook(arq_hist(), data_only=True, read_only=True)
    ws = wb['BASE']
    linhas = ws.iter_rows(values_only=True)
    cab = [str(c or '').strip() for c in next(linhas)]
    hist = []
    for r in linhas:
        d = dict(zip(cab, r))
        dt = como_data(d.get('Data plantio'))
        if dt and d.get('CAMPANA'):
            hist.append({'sf': str(d.get('CAMPANA')).strip(), 'g': grupo(d.get('Micro')), 'dt': iso(dt)})
    wb.close()
    return hist


def m3data():
    f, _, cur, safra = ler_rede()
    try:
        ini = 2000 + int(safra.split('/')[0])
    except (ValueError, AttributeError, IndexError):
        ini = date.today().year
    return {
        'today': date.today().isoformat(),
        'safra': safra,
        'inicioSafra': ini,
        'arquivo': f.name,
        'lidoEm': datetime.now().strftime('%H:%M'),
        'cur': cur,
        'hist': ler_hist(),
        'grupos': GRUPOS,
    }


def registrar(corpo):
    linha = int(corpo['row'])
    loc = str(corpo.get('loc', ''))
    d = corpo.get('data')
    d = date.fromisoformat(d) if d else None
    if d and d > date.today():
        raise ValueError('A data de semeadura não pode ser futura.')
    with TRAVA:
        f, cab, cur, _ = ler_rede()
        item = next((x for x in cur if x['row'] == linha), None)
        if not item or item['loc'] != loc:
            raise ValueError('A planilha mudou desde a última leitura. Atualize a página e tente de novo.')
        P.gravar_semeadura(f, linha, item['micro'], cab, d, DADOS / 'backups')
        log = DADOS / 'registro_semeaduras.csv'
        novo = not log.exists()
        with open(log, 'a', newline='', encoding='utf-8-sig') as fh:
            w = csv.writer(fh, delimiter=';')
            if novo:
                w.writerow(['registrado em', 'localidade', 'micro', 'condução', 'ação', 'data semeadura', 'data anterior'])
            w.writerow([datetime.now().strftime('%d/%m/%Y %H:%M'), loc, item['micro'], item['c'],
                        'registro' if d else 'remoção', d.strftime('%d/%m/%Y') if d else '',
                        item['real'] or ''])
    return m3data()


class H(SimpleHTTPRequestHandler):
    def translate_path(self, p):
        caminho = urlparse(p).path.lstrip('/') or 'index.html'
        if caminho.startswith('dados'):  # não expõe as planilhas pelo navegador
            return str(RAIZ / '__bloqueado__')
        return str(RAIZ / caminho)

    def log_message(self, *a):
        pass

    def end_headers(self):
        # sem cache: depois de uma atualização o navegador sempre pega a versão nova
        if not self.path.startswith('/api/'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def j(self, x, c=200):
        b = json.dumps(x, ensure_ascii=False, default=str).encode()
        self.send_response(c)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', len(b))
        self.end_headers()
        self.wfile.write(b)

    def erro(self, e):
        if isinstance(e, P.PlanilhaAberta):
            msg = 'A planilha "%s" está aberta no Excel. Feche-a e tente de novo.' % arq_rede().name
            return self.j({'erro': msg}, 409)
        if isinstance(e, PermissionError):
            return self.j({'erro': 'Sem permissão para gravar a planilha. Ela está aberta no Excel?'}, 409)
        return self.j({'erro': str(e)}, 400)

    def do_GET(self):
        p = urlparse(self.path).path
        try:
            if p == '/api/estande/data':
                return self.j(E.scan())
            if p == '/api/m3/data':
                return self.j(m3data())
        except Exception as e:
            return self.erro(e)
        super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n)
        try:
            if p == '/api/m3/semeadura':
                return self.j(registrar(json.loads(body.decode('utf-8'))))
            if p == '/api/estande/upload':
                msg = BytesParser(policy=default).parsebytes(
                    b'Content-Type: ' + self.headers['Content-Type'].encode() + b'\r\nMIME-Version: 1.0\r\n\r\n' + body)
                saved = []
                for x in msg.iter_attachments():
                    fn = Path(x.get_filename() or '').name
                    if fn.lower().endswith('.xlsx'):
                        (E.UP / fn).write_bytes(x.get_payload(decode=True))
                        saved.append(fn)
                return self.j({'saved': saved, 'result': E.scan()})
        except Exception as e:
            return self.erro(e)
        self.j({'erro': 'rota não encontrada'}, 404)


if __name__ == '__main__':
    preparar_dados()
    url = 'http://localhost:%d' % PORTA
    print('Gestão de Ensaios M3 rodando em', url)
    print('Planilhas lidas da pasta:', DADOS)
    print('Deixe esta janela aberta enquanto usa o painel.')
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    ThreadingHTTPServer(('localhost', PORTA), H).serve_forever()
