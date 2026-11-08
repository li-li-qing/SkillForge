from pathlib import Path
import importlib.util,hashlib,os,subprocess,sys,tempfile,shutil,json
from unittest.mock import patch
R=Path('/workspace/scratch/54a565457947/transaction_review_v5/Skills');results=[]
def load(name,rel):
 s=importlib.util.spec_from_file_location(name,R/rel);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('probe','skills/skillforge-reverse-engineering/scripts/probe_binary.py');e=load('evidence','skills/skillforge-ida-pro/scripts/ida_evidence.py');v=load('verify','skills/skillforge-archerage-addon/scripts/verify_skill.py');o=load('output','skills/skillforge-archerage-addon/scripts/verify_report.py')
def check(name,fn):
 try:fn();results.append({'case':name,'pass':True})
 except Exception as ex:results.append({'case':name,'pass':False,'error':repr(ex)})
def must_reject(fn):
 try:fn()
 except (OSError,ValueError):return
 raise AssertionError('not rejected')
with tempfile.TemporaryDirectory() as t:
 d=Path(t);good=d/'good';good.write_bytes(b'hello\n');link=d/'link';link.symlink_to(good);fifo=d/'fifo';os.mkfifo(fifo);badlink=d/'badlink';badlink.symlink_to(fifo)
 for label,fn in [('probe',p.inspect_file),('hash',e.sha256_file),('verifier_reader',v.read_regular_text)]:
  for kind,path in [('fifo',fifo),('zero',Path('/dev/zero')),('fifo_symlink',badlink)]:check(label+'_'+kind,lambda fn=fn,path=path:must_reject(lambda:fn(path)))
 check('probe_normal',lambda: __import__('unittest').TestCase().assertEqual(p.inspect_file(good)['sha256'],hashlib.sha256(good.read_bytes()).hexdigest().upper()))
 check('probe_regular_symlink',lambda:__import__('unittest').TestCase().assertEqual(p.inspect_file(link),p.inspect_file(good)))
 check('hash_normal_symlink',lambda:__import__('unittest').TestCase().assertEqual(e.sha256_file(link),hashlib.sha256(good.read_bytes()).hexdigest()))
 check('reader_regular_symlink_refused',lambda:must_reject(lambda:v.read_regular_text(link)))
 check('reader_normal',lambda:__import__('unittest').TestCase().assertEqual(v.read_regular_text(good),'hello\n'))
 big=d/'big';big.write_bytes(b'a'*(2*1024*1024+1));check('reader_size_cap',lambda:must_reject(lambda:v.read_regular_text(big)))
 target=d/'skillforge-archerage-addon';shutil.copytree(R/'skills/skillforge-archerage-addon',target)
 def cli(expected):
  x=subprocess.run([sys.executable,str(target/'scripts/verify_skill.py'),str(target)],capture_output=True,timeout=3);assert x.returncode==expected,(x.returncode,x.stderr)
 check('verifier_whole_normal',lambda:cli(0));ev=target/'evals/behavior-cases.json';ev.unlink();os.mkfifo(ev);check('verifier_whole_fifo',lambda:cli(1))
 def publish_normal():
  x=d/'normal';s=o.publish_output(x,b'abc');assert s['published'] and x.read_bytes()==b'abc' and not Path(str(x)+'.partial').exists()
 check('publish_normal',publish_normal)
 for kind in ['file','symlink','dangling','fifo']:
  x=d/('existing_'+kind)
  if kind=='file':x.write_bytes(b'keep')
  elif kind=='fifo':os.mkfifo(x)
  else:x.symlink_to(good if kind=='symlink' else d/'missing')
  check('publish_refuse_'+kind,lambda x=x:must_reject(lambda:o.publish_output(x,b'new')))
 original=Path.open
 class Wrapped:
  def __init__(self,f,mode):self.f=f;self.mode=mode
  def __enter__(self):return self
  def __exit__(self,*args):
   self.f.close()
   if self.mode=='close':raise OSError('close fault')
  def write(self,data):
   if self.mode=='short':return self.f.write(data[:1])
   if self.mode=='write':self.f.write(data[:1]);raise OSError('write fault')
   return self.f.write(data)
  def flush(self):
   if self.mode=='flush':raise OSError('flush fault')
   return self.f.flush()
  def fileno(self):return self.f.fileno()
 for mode in ['write','short','flush','fsync','close','link','cleanup']:
  def test(mode=mode):
   x=d/('fault_'+mode);partial=Path(str(x)+'.partial')
   def op(path,*a,**k):
    f=original(path,*a,**k);return Wrapped(f,mode) if path==partial else f
   from contextlib import ExitStack
   with ExitStack() as st:
    st.enter_context(patch.object(Path,'open',op))
    if mode in ['fsync','link','cleanup']:st.enter_context(patch.object(o.os,{'cleanup':'unlink'}.get(mode,mode),side_effect=OSError(mode)))
    if mode=='cleanup':
     s=o.publish_output(x,b'abcdef');assert s['published'] and s['cleanup_error']
    else:must_reject(lambda:o.publish_output(x,b'abcdef'))
   assert x.exists()==(mode=='cleanup');assert partial.exists()
   if x.exists():assert x.read_bytes()==b'abcdef'
  check('publish_fault_'+mode,test)
print(json.dumps(results,indent=2));assert all(x['pass'] for x in results)
