from sf_v5_multiprocess_audit import *
def exp_pause(root,ident,ready,release,out):
 e=load('exp','skills/skillforge-experience-maintenance/scripts/experience_store.py');orig=e._json_write
 def checkpoint(p,v):
  if v.get('status')=='committed':
   ready.set()
   if not release.wait(8):raise TimeoutError('checkpoint')
  return orig(p,v)
 e._json_write=checkpoint
 try:out.put(('ok',e.promote(Path(root),ident,reviewed=True)))
 except BaseException as x:out.put(('error',type(x).__name__,str(x)))
def update_plain(root,pkg,q):
 u=load('u','scripts/apply_skillforge_update.py')
 try:q.put(('ok',u.apply_update(Path(root),Path(pkg),apply=True)))
 except BaseException as x:q.put(('error',type(x).__name__,str(x)))
def run_update(ctx,r,k):
 q=ctx.Queue();p=ctx.Process(target=update_plain,args=(str(r),str(k),q));p.start();p.join(3)
 if p.is_alive():p.kill();p.join();raise AssertionError('timeout')
 return q.get(timeout=1)
if __name__=='__main__':
 ctx=mp.get_context('spawn');results=[]
 for killed in (False,True):
  with tempfile.TemporaryDirectory(prefix='sf-reverse-') as d:
   r,k,e,ids=setup(d);ready=ctx.Event();release=ctx.Event();q=ctx.Queue()
   # experience modifies OTHER, updater modifies SAME: genuinely unrelated scope.
   p=ctx.Process(target=exp_pause,args=(str(r),ids['other'],ready,release,q));p.start();assert ready.wait(5)
   row={'kill':killed,'during_unrelated_update':run_update(ctx,r,k)}
   if killed:
    p.terminate();p.join(3);assert not p.is_alive();row['exit']=p.exitcode
    row['lock_remains']=(r/'.skillforge-memory/write.lock').exists()
    row['journal']=json.loads((r/'.skillforge-memory/transactions'/f"{ids['other']}.json").read_text())['status']
    (r/'.skillforge-memory/write.lock').unlink()
    row['after_explicit_lock_cleanup']=run_update(ctx,r,k)
    row['recover']=e.recover(r,ids['other'])
    row['after_recover']=run_update(ctx,r,k)
    assert row['after_explicit_lock_cleanup'][0]=='error' and row['after_recover'][0]=='ok'
   else:
    release.set();p.join(3);assert not p.is_alive();row['experience']=q.get(timeout=1);row['after_update']=run_update(ctx,r,k);assert row['after_update'][0]=='ok'
   results.append(row)
 print(json.dumps(results,ensure_ascii=False,indent=2))
