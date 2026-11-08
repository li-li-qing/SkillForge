exec(open('/workspace/shared/script_safety_v5/reverify.py').read().split('with tempfile.TemporaryDirectory() as t:')[0])
with tempfile.TemporaryDirectory() as t:
 d=Path(t);realopen=os.open
 for label,fn in [('probe',p.inspect_file),('hash',e.sha256_file),('reader',v.read_regular_text)]:
  x=d/label;x.write_bytes(b'original')
  def swap(path,flags,*a,**kw):
   if Path(path)==x:x.unlink();os.mkfifo(x)
   return realopen(path,flags,*a,**kw)
  with patch.object(os,'open',swap):must_reject(lambda:fn(x))
  print(label+' stat->FIFO swap: PASS')
 for label,fn in [('probe',p.inspect_file),('hash',e.sha256_file)]:
  for mode in ['grow','shrink']:
   x=d/(label+mode);x.write_bytes(b'original');realfstat=os.fstat;fired=[False]
   # First fstat in probe checks type, second captures size; hash first captures size.
   count=[0];targetcount=2 if label=='probe' else 1
   def mutate(fd):
    result=realfstat(fd);count[0]+=1
    if count[0]==targetcount:
     x.write_bytes(b'longer than original' if mode=='grow' else b'')
    return result
   with patch.object(os,'fstat',mutate):must_reject(lambda:fn(x))
   print(label+' '+mode+': PASS')
