exec(open('/workspace/shared/script_safety_v5/reverify.py').read().split('with tempfile.TemporaryDirectory() as t:')[0])
with tempfile.TemporaryDirectory() as t:
 d=Path(t);x=d/'final';partial=d/'final.partial';original=os.link
 def race(src,dst):Path(dst).write_bytes(b'winner');return original(src,dst)
 with patch.object(o.os,'link',race):must_reject(lambda:o.publish_output(x,b'candidate'))
 assert x.read_bytes()==b'winner' and partial.read_bytes()==b'candidate'
 print('late competing publisher preserved: PASS')
 x=d/'second';target=d/'keep';target.write_bytes(b'keep');Path(str(x)+'.partial').symlink_to(target);must_reject(lambda:o.publish_output(x,b'candidate'));assert target.read_bytes()==b'keep' and not x.exists();print('partial symlink refused: PASS')
 raw=b'hello';cs=o.check(raw);wire=(f'RS-ERROR-PAGE-1;ID=fixture;PAGE=1/1;TOTAL_BYTES=5;TOTAL_CHECK={cs};RAW_BYTES=5;RAW_CHECK={cs};OFFSET=0;DATA_BYTES=5;DATA_CHECK={cs};DATA='.encode()+raw+b';RS-ERROR-PAGE-END');inp=d/'report';inp.write_bytes(wire);out=d/'valid'
 a=subprocess.run([sys.executable,str(R/'skills/skillforge-archerage-addon/scripts/verify_report.py'),str(inp),'--output',str(out)],capture_output=True,timeout=3);assert a.returncode==0 and out.read_bytes()==raw and json.loads(a.stdout)['output_state']['published'];print('real wire CLI publish: PASS')
 out=d/'diagnostic'
 from io import StringIO
 err=StringIO();realprint=print
 def print_fault(*args,**kw):
  if kw.get('file') is sys.stderr:return realprint(*args,file=err)
  raise OSError('stdout broken')
 with patch.object(sys,'argv',['verify',str(inp),'--output',str(out)]),patch('builtins.print',print_fault):code=o.main()
 assert code==1 and out.read_bytes()==raw and json.loads(err.getvalue())['status']=='published_diagnostic_error';print('stdout failure preserves published fact: PASS')
print('HASHES')
for rel in ['skills/skillforge-reverse-engineering/scripts/probe_binary.py','skills/skillforge-ida-pro/scripts/ida_evidence.py','skills/skillforge-archerage-addon/scripts/verify_skill.py','skills/skillforge-archerage-addon/scripts/verify_report.py']:
 print(hashlib.sha256((R/rel).read_bytes()).hexdigest(),rel)
