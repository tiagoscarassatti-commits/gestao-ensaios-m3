from pathlib import Path
from collections import defaultdict
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse
from email.parser import BytesParser
from email.policy import default
from openpyxl import load_workbook
import json,re,statistics,unicodedata,threading,webbrowser
ROOT=Path(__file__).parent;UP=ROOT/'uploads'
REG={'M301':['RIO VERDE 1','RIO VERDE 2','JATAI 1','JATAI 2','MONTIVIDIU'],'M303':['ARAGUARI','MONTE CARMELO','UBERABA','PATOS DE MINAS','TUPACIGUARA 1','TUPACIGUARA 2'],'M304':['CABECEIRAS','BURITIS','PLANALTINA 1','PLANALTINA 2','CRISTALINA','UNAI']}
def plain(v):
 s=str(v or '').strip().upper();s=''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn');return re.sub(r'\s+',' ',s)
def localize(fn):
 s=plain(Path(fn).stem).replace('_',' ');rules=[('RIO VERDE 2','M301'),('RIO VERDE 1','M301'),('RIO VERDE','M301'),('JATAI 2','M301'),('JATAI 1','M301'),('JATAI','M301'),('MONTIVIDIU','M301'),('ARAGUARI','M303'),('MONTE CARMELO','M303'),('UBERABA','M303'),('PATOS DE MINAS','M303'),('TUPACIGUARA 2','M303'),('TUPACIGUARA 1','M303'),('TUPACIGUARA','M303'),('CABECEIRAS','M304'),('BURITIS','M304'),('PLANALTINA 2','M304'),('PLANALTINA 1','M304'),('PLANALTINA','M304'),('CRISTALINA','M304'),('UNAI','M304')]
 for k,m in rules:
  if k in s:
   if k in ('RIO VERDE','JATAI','PLANALTINA','TUPACIGUARA'):
    nums=re.findall(r'(?<!\d)([12])(?!\d)',s);k=k+(' '+nums[-1] if nums else ' 1')
   return m,k
 return 'Não mapeada',Path(fn).stem
def num(v):
 try:return float(v)
 except:return None
def parse(p):
 wb=load_workbook(p,data_only=True,read_only=True);micro,local=localize(p.name);raw=[]
 for ws in wb.worksheets:
  rows=list(ws.iter_rows(values_only=True))
  for i,r in enumerate(rows[:20]):
   h=[plain(x) for x in r]
   if 'VARIEDADE' in h and 'DIFERENCA DO REAL' in h:
    mi=h.index('VARIEDADE');di=h.index('DIFERENCA DO REAL');raw += [(plain(x[mi]),num(x[di])) for x in rows[i+1:] if mi<len(x) and di<len(x) and x[mi] and num(x[di]) is not None];break
  for i,r in enumerate(rows[:20]):
   h=[plain(x) for x in r]
   if ('VARIEDADE' in h or 'NOME COMERCIAL' in h) and 'DIF' in h:
    mi=h.index('VARIEDADE') if 'VARIEDADE' in h else h.index('NOME COMERCIAL');di=h.index('DIF')
    for x in rows[i+1:]:
     if mi<len(x) and di<len(x) and x[mi] and num(x[di]) is not None:
      v=num(x[di]);raw.append((plain(x[mi]),v*100 if abs(v)<=2 else v))
    break
  for i,r in enumerate(rows[:20]):
   h=[plain(x) for x in r]
   if 'PRODUTO' in h and any(x in ('POP','POP %') for x in h):
    mi=h.index('PRODUTO');di=[j for j,x in enumerate(h) if x in ('POP','POP %')][-1]
    raw += [(plain(x[mi]),num(x[di])) for x in rows[i+1:] if mi<len(x) and di<len(x) and x[mi] and not plain(x[mi]).startswith('PREENCHIMENTO') and num(x[di]) is not None];break
 if not raw:raise ValueError('Formato não reconhecido')
 g=defaultdict(list)
 for m,v in raw:g[m].append(v)
 return [{'material':m,'value':statistics.mean(v),'reps':len(v),'micro':micro,'local':local,'file':p.name,'group':('SB' if m.startswith('SB') else 'NEO' if m.startswith('NEO') else 'BRASMAX' if m.startswith('BRASMAX') else 'TMG' if m.startswith('TMG') else 'STINE' if m.startswith('STINE') else 'OUTROS')} for m,v in g.items()],len(raw)
def scan():
 data=[];files=[]
 for p in sorted(UP.glob('*.xlsx')):
  try:
   d,n=parse(p);data+=d;files.append({'file':p.name,'micro':d[0]['micro'],'local':d[0]['local'],'raw':n,'distinct':len(d),'sb':sum(x['group']=='SB' for x in d),'neo680':next((x['reps'] for x in d if x['material'].startswith('NEO680')),0),'ok':True})
  except Exception as e:files.append({'file':p.name,'ok':False,'error':str(e)})
 return {'data':data,'files':files,'map':REG}
class H(SimpleHTTPRequestHandler):
 def translate_path(self,path):return str(ROOT/(urlparse(path).path.lstrip('/') or 'index.html'))
 def j(self,x,c=200):
  b=json.dumps(x,ensure_ascii=False).encode();self.send_response(c);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',len(b));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  if self.path.startswith('/api/data'):return self.j(scan())
  super().do_GET()
 def do_POST(self):
  n=int(self.headers.get('Content-Length',0));body=self.rfile.read(n);msg=BytesParser(policy=default).parsebytes(b'Content-Type: '+self.headers['Content-Type'].encode()+b'\r\nMIME-Version: 1.0\r\n\r\n'+body);saved=[]
  for x in msg.iter_attachments():
   fn=Path(x.get_filename() or '').name
   if fn.lower().endswith('.xlsx'):(UP/fn).write_bytes(x.get_payload(decode=True));saved.append(fn)
  self.j({'saved':saved,'result':scan()})
if __name__=='__main__':threading.Timer(1,lambda:webbrowser.open('http://localhost:8030')).start();ThreadingHTTPServer(('localhost',8030),H).serve_forever()
