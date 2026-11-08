import multiprocessing as mp, tempfile, importlib.util, json, hashlib, time, platform, os
from pathlib import Path
BASE=Path('/workspace/scratch/54a565457947/transaction_review_v5/Skills')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,BASE/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def updater(root,pkg,ready,release,out):
 u=load('up','scripts/apply_skillforge_update.py');orig=u.atomic_write;count=0
 def checkpoint(path,data,mode=None):
  nonlocal count
  if path.name=='state.json':
   count+=1
   if count==2:
    ready.set()
    if not release.wait(8):raise TimeoutError('test checkpoint timed out')
  return orig(path,data,mode)
 u.atomic_write=checkpoint
 try:out.put(('update',u.apply_update(Path(root),Path(pkg),apply=True)))
 except BaseException as x:out.put(('error',type(x).__name__,str(x)))
def promote(root,ident,out):
 e=load('exp','skills/skillforge-experience-maintenance/scripts/experience_store.py')
 try:out.put(('ok',e.promote(Path(root),ident,reviewed=True)))
 except BaseException as x:out.put(('error',type(x).__name__,str(x)))
def run_promote(ctx,r,i):
 q=ctx.Queue();p=ctx.Process(target=promote,args=(str(r),i,q));p.start();p.join(3)
 if p.is_alive():p.kill();p.join();raise AssertionError('promotion exceeded 3 s')
 return q.get(timeout=1)
def setup(d):
 r=Path(d)/'root';k=Path(d)/'pkg';r.mkdir();entries=[]
 for name in ('same','other'):
  t=r/f'skills/demo/references/{name}.md';t.parent.mkdir(parents=True,exist_ok=True);t.write_text('old')
 n='skills/demo/references/same.md';p=k/'payload'/n;p.parent.mkdir(parents=True);p.write_text('update')
 sha=lambda x:hashlib.sha256(x.encode()).hexdigest()
 (k/'manifest.json').write_text(json.dumps({'schema_version':1,'entries':[{'path':n,'operation':'modify','before':sha('old'),'after':sha('update')}]}))
 e=load('e','skills/skillforge-experience-maintenance/scripts/experience_store.py')
 ids={x:e.propose(r,f'skills/demo/references/{x}.md','experience',actor='audit',kind='technical',evidence=['isolated test'],conditions='fixture') for x in ('same','other')}
 return r,k,e,ids
if __name__=='__main__':
 ctx=mp.get_context('spawn');results={'platform':platform.platform(),'start_method':'spawn','scenarios':[]}
 for killed in (False,True):
  with tempfile.TemporaryDirectory(prefix='sf-realprocess-') as d:
   r,k,e,ids=setup(d);ready=ctx.Event();release=ctx.Event();out=ctx.Queue();p=ctx.Process(target=updater,args=(str(r),str(k),ready,release,out));p.start();assert ready.wait(5)
   row={'kill':killed,'during_same':run_promote(ctx,r,ids['same']),'during_unrelated':run_promote(ctx,r,ids['other'])}
   assert row['during_same'][0]==row['during_unrelated'][0]=='error'
   if killed:
    p.terminate();p.join(3);assert not p.is_alive()
    row['terminated_exitcode']=p.exitcode
    row['lock_remains']=(r/'.skillforge-memory/write.lock').exists()
    row['journal']=json.loads(next(r.glob('.skillforge-backups/*/state.json')).read_text())['status']
    row['target']=(r/'skills/demo/references/same.md').read_text()
    row['before_manual_cleanup']=run_promote(ctx,r,ids['other'])
    # Explicit test-only recovery after updater is joined and every writer stopped.
    (r/'.skillforge-memory/write.lock').unlink()
    new=e.propose(r,'skills/demo/references/same.md','experience',actor='audit',kind='technical',evidence=['fixture'],conditions='fixture')
    row['after_cleanup_same']=run_promote(ctx,r,new)
    row['after_cleanup_unrelated']=run_promote(ctx,r,ids['other'])
    assert row['lock_remains'] and row['journal']=='prepared' and row['target']=='update'
    assert row['after_cleanup_same'][0]=='error' and row['after_cleanup_unrelated'][0]=='ok'
   else:
    release.set();p.join(3);assert not p.is_alive();row['updater_result']=out.get(timeout=1)
    row['after_same_stale']=run_promote(ctx,r,ids['same']);row['after_unrelated']=run_promote(ctx,r,ids['other'])
    assert row['after_same_stale'][0]=='error' and row['after_unrelated'][0]=='ok'
   results['scenarios'].append(row)
 print(json.dumps(results,ensure_ascii=False,indent=2))
