import pathlib,sys,subprocess,tempfile,shutil,json,importlib.util,unittest.mock as mock
ROOT=pathlib.Path('/workspace/scratch/54a565457947/transaction_review_v5/Skills')
out=[]
with tempfile.TemporaryDirectory() as t:
 p=pathlib.Path(t); fifo=p/'sample'; __import__('os').mkfifo(fifo)
 for label,sample in [('probe_fifo',fifo),('probe_zero',pathlib.Path('/dev/zero'))]:
  try:
   r=subprocess.run([sys.executable,str(ROOT/'skills/skillforge-reverse-engineering/scripts/probe_binary.py'),str(sample)],capture_output=True,timeout=0.5);out.append(dict(case=label,exit=r.returncode))
  except subprocess.TimeoutExpired:out.append(dict(case=label,result='timeout_0.5s_killed'))
 dst=p/'skillforge-archerage-addon';shutil.copytree(ROOT/'skills/skillforge-archerage-addon',dst)
 f=dst/'evals/behavior-cases.json';f.unlink();__import__('os').mkfifo(f)
 try:
  r=subprocess.run([sys.executable,str(dst/'scripts/verify_skill.py'),str(dst)],capture_output=True,timeout=0.5);out.append(dict(case='standalone_verifier_eval_fifo',exit=r.returncode))
 except subprocess.TimeoutExpired:out.append(dict(case='standalone_verifier_eval_fifo',result='timeout_0.5s_killed'))
 spec=importlib.util.spec_from_file_location('report',ROOT/'skills/skillforge-archerage-addon/scripts/verify_report.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 inp=p/'in';inp.write_bytes(b'fixture');output=p/'verified.txt';original=pathlib.Path.open
 class Fail:
  def __init__(self,f):self.f=f
  def __enter__(self):return self
  def __exit__(self,*a):self.f.close()
  def write(self,data):self.f.write(data[:3]);self.f.flush();raise OSError('fixture disk full')
 def op(self,*a,**kw):
  f=original(self,*a,**kw);return Fail(f) if self==output and a==('xb',) else f
 with mock.patch.object(sys,'argv',['verify_report',str(inp),'--output',str(output)]), mock.patch.object(m,'decode_pages',return_value={'status':'verified_copy','raw':'abcdef'}),mock.patch.object(pathlib.Path,'open',op):code=m.main()
 out.append(dict(case='report_output_write_failure',exit=code,final_file_exists=output.exists(),final_bytes=output.read_text()))
print(json.dumps(out,indent=2))
