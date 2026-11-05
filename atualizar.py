"""Atualiza o painel com a versão mais nova do GitHub antes de abrir.

Na primeira execução pede o token do GitHub e salva em token_github.txt.
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


LINK_TOKEN = ('https://github.com/settings/personal-access-tokens/new'
              '?name=painel-m3&description=Atualizar+painel+Gestao+de+Ensaios+M3'
              '&expires_in=365&contents=read')


def configurar_token():
    """Primeira execução: abre a página do GitHub e pede para colar o token."""
    import webbrowser
    print()
    print('=' * 64)
    print(' CONFIGURAR ATUALIZACAO AUTOMATICA (so na primeira vez)')
    print('=' * 64)
    print(' Vou abrir o GitHub no navegador. Na pagina:')
    print('  1. Em "Repository access", marque "Only select repositories"')
    print('     e escolha  gestao-ensaios-m3')
    print('  2. Confira em Permissions > Contents = Read-only')
    print('  3. Clique em "Generate token" e copie o token (github_pat_...)')
    print()
    try:
        webbrowser.open(LINK_TOKEN)
    except Exception:
        print(' Abra este link:', LINK_TOKEN)
    try:
        tok = input(' Cole o token aqui e tecle Enter (ou so Enter para pular): ').strip()
    except EOFError:
        tok = ''
    TOKEN.write_text(tok, encoding='utf-8')
    if tok:
        print(' Token salvo. A partir de agora o painel se atualiza sozinho.')
    else:
        print(' Pulado. Para configurar depois, apague o arquivo token_github.txt.')
    print()


def main():
    if not TOKEN.exists():
        configurar_token()
    if not TOKEN.read_text(encoding='utf-8').strip():
        print('Atualização automática desligada (token_github.txt vazio).')
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
