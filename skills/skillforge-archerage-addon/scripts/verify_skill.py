#!/usr/bin/env python3
"""Validate THIS skill package's structure, references, and evaluation schemas.

Python >=3.10, standard library only. Frontmatter parser intentionally supports
this package's simple YAML subset, not arbitrary YAML. Structural validation is
not agent-behavior evaluation, Lua/runtime validation, or a secret-content scan.
"""
from __future__ import annotations
import argparse
import ast
import stat
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

REQUIRED_TOOLS=('verify_skill.py','verify_report.py','audit_patch.py','check_lua51.py')

def frontmatter(text: str) -> dict:
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:raise ValueError('frontmatter delimiters')
    block=text[4:].split('\n---\n',1)[0];result={};section=None
    for line in block.splitlines():
        if not line:continue
        m=re.fullmatch(r'(  )?([a-z][a-z0-9_-]*):(?: (.+))?',line)
        if not m:raise ValueError('frontmatter unsupported YAML; use simple quoted scalars')
        indent,key,value=m.groups()
        target=result
        if indent:
            if section!='metadata':raise ValueError('frontmatter unexpected indentation')
            target=result['metadata']
        else:section=None
        if key in target:raise ValueError('frontmatter duplicate key:'+key)
        if value is None:
            if indent or key!='metadata':raise ValueError('frontmatter missing scalar')
            target[key]={};section=key;continue
        parsed=json.loads(value) if value.startswith('"') else value
        if not isinstance(parsed,str):raise ValueError('frontmatter non-string')
        target[key]=parsed
    if set(result)-{'name','description','metadata','compatibility','license','allowed-tools'}:raise ValueError('frontmatter unknown field')
    return result

def unique_object(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('duplicate JSON key:'+key)
        result[key]=value
    return result

def walk_error(error):
    raise error

def read_regular_text(path: Path) -> str:
    """统一入口：先拒绝特殊文件，再以已打开描述符核对并限量读取。"""
    limit=2*1024*1024
    info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>limit:
        raise ValueError('not_regular_or_size_limit')
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(path,flags)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>limit:
            raise ValueError('not_regular_or_size_limit')
        with os.fdopen(fd,'rb') as stream:
            fd=None
            raw=stream.read(limit+1)
        if len(raw)>limit:raise ValueError('text_size_limit')
        return raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
    finally:
        if fd is not None:os.close(fd)


def validate(root: Path) -> list[str]:
    root=Path(root);errors=[]
    if root.is_symlink() or not root.is_dir():return ['skill root not a regular directory']
    root=root.resolve();files=[];names=set()
    for current,dirs,entries in os.walk(root,followlinks=False,onerror=walk_error):
        dirs[:]=[d for d in dirs if d!='__pycache__']
        for name in dirs+entries:
            p=Path(current)/name
            if p.is_symlink():errors.append('symlink:'+str(p.relative_to(root)))
            rel=p.relative_to(root).as_posix().casefold()
            if rel in names:errors.append('duplicate/case collision:'+rel)
            names.add(rel)
        files.extend(Path(current)/n for n in entries if not n.endswith('.pyc') and not (Path(current)/n).is_symlink())
    main=root/'SKILL.md'
    if not main.is_file():return errors+['SKILL.md missing']
    try:
        text=read_regular_text(main);data=frontmatter(text)
        name=data.get('name','');desc=data.get('description','')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64 or name!=root.name:errors.append('invalid/mismatched skill name')
        if not 1<=len(desc)<=1024 or not desc.startswith('Use when'):errors.append('invalid triggering description')
        if len(data.get('compatibility',''))>500:errors.append('compatibility length')
        if len(text.splitlines())>=500:errors.append('main skill exceeds 499 lines')
        metadata=data.get('metadata',{})
        if not isinstance(metadata,dict):errors.append('metadata must be object')
        elif not metadata.get('revision'):errors.append('revision metadata missing')
    except (ValueError,OSError) as e:errors.append(str(e))
    for p in files:
        if p.suffix.lower() not in ('.md','.json','.py'):continue
        try:
            raw=read_regular_text(p)
            if p.suffix.lower()=='.json':json.loads(raw,object_pairs_hook=unique_object)
            elif p.suffix.lower()=='.py':
                try:ast.parse(raw,filename=str(p))
                except SyntaxError as e:errors.append('Python syntax:'+str(p.relative_to(root))+':'+str(e))
            else:
                body=re.sub(r'```.*?```','',raw,flags=re.S)
                for link in re.findall(r'\[[^\]\n]+\]\(([^)]+)\)',body):
                    if urlsplit(link).scheme or link.startswith('#'):continue
                    local=unquote(link.split('#',1)[0])
                    dest=(p.parent/local).resolve()
                    if not dest.is_relative_to(root) or not dest.is_file():errors.append('broken/escaping link:'+p.relative_to(root).as_posix()+':'+link)
        except (OSError,ValueError) as e:errors.append('invalid text/json:'+str(p.relative_to(root))+':'+str(e))
    for tool in REQUIRED_TOOLS:
        if not (root/'scripts'/tool).is_file():errors.append('required tool missing:'+tool)
    for filename in ('behavior-cases.json','trigger-cases.json'):
        try:
            cases=json.loads(read_regular_text(root/'evals'/filename),object_pairs_hook=unique_object);seen=set()
            if not isinstance(cases,list) or not cases:raise ValueError('expected nonempty case list')
            for c in cases:
                if not isinstance(c,dict):raise ValueError('case must be object')
                identity=c.get('id')
                if not isinstance(identity,str) or not c.get('prompt'):raise ValueError('case identity/prompt missing')
                if identity in seen:errors.append('duplicate eval id:'+identity)
                seen.add(identity)
                if filename.startswith('behavior'):
                    expectations=c.get('expectations')
                    if not isinstance(expectations,list) or not expectations or not all(isinstance(x,str) and x for x in expectations):errors.append('case expectations missing:'+identity)
                    if int(identity.split('-')[-1])>=27:
                        if c.get('execution_status')!='not_run':errors.append('scenario spec is not an execution record:'+identity)
                        rubric=c.get('rubric',{})
                        if not isinstance(rubric,dict):errors.append('case rubric must be object:'+identity)
                        elif not rubric.get('critical_failures'):errors.append('critical failures missing:'+identity)
                        elif not isinstance(rubric['critical_failures'],list) or not all(isinstance(x,str) and x.strip() for x in rubric['critical_failures']):errors.append('critical failures must be nonempty list of nonblank strings:'+identity)
                elif c.get('expected') not in ('trigger','no_trigger','conditional'):
                    errors.append('invalid trigger verdict:'+identity)
        except (ValueError,OSError,TypeError) as e:errors.append('eval schema:'+filename+':'+str(e))
    return errors

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    try:errors=validate(args.root)
    except OSError as e:errors=['unreadable_package:'+str(e)]
    print(json.dumps({'status':'failed' if errors else 'passed','scope':'structure_only','errors':errors},ensure_ascii=False,indent=2))
    return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
