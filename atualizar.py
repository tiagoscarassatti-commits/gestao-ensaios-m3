"""Atualiza o painel com a versão mais nova do GitHub antes de abrir.

Só funciona se existir o arquivo token_github.txt nesta pasta (veja o LEIA-ME).
Nunca mexe na pasta dados/ (planilhas, backups e registros ficam intactos).
Se estiver sem internet ou der qualquer erro, apenas abre a versão atual.
"""
import io
import urllib.request
import zipfile
from pathlib import Path

REPO = 'tiagoscarassatti-commits/gestao-ensaios-m3'
RAIZ = Path(__file__).parent
TOKEN = RAIZ / 'token_github.txt'
VERSAO = RAIZ / 'versao.txt'
PROTEGIDOS = {'dados', 'token_github.txt', 'versao.txt'}


def baixar(url, accept):
    req = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + TOKEN.read_text(encoding='utf-8').strip(),
        'Accept': accept,
        'User-Agent': 'gestao-ensaios-m3',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    if not TOKEN.exists():
        print('Atualização automática desligada (falta o token_github.txt).')
        return
    try:
        sha = baixar('https://api.github.com/repos/%s/commits/main' % REPO, 'application/vnd.github.sha').decode().strip()
        if VERSAO.exists() and VERSAO.read_text().strip() == sha:
            print('Painel já está na versão mais recente.')
            return
        print('Baixando a versão nova do painel...')
        z = zipfile.ZipFile(io.BytesIO(baixar('https://api.github.com/repos/%s/zipball/%s' % (REPO, sha), 'application/vnd.github+json')))
        n = 0
        for info in z.infolist():
            partes = Path(info.filename).parts[1:]  # tira a pasta-raiz do zip
            if info.is_dir() or not partes or partes[0] in PROTEGIDOS:
                continue
            destino = RAIZ.joinpath(*partes)
            novo = z.read(info)
            if destino.exists() and destino.read_bytes() == novo:
                continue  # só grava o que mudou
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(novo)
            n += 1
        VERSAO.write_text(sha)
        print('Painel atualizado (%d arquivos).' % n)
    except Exception as e:
        print('Não deu para verificar atualização agora (%s). Abrindo a versão atual.' % e)


if __name__ == '__main__':
    main()
