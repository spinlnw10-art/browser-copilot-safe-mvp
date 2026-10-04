#!/usr/bin/env python3
"""Local, deterministic policy/analysis backend for Browser Copilot Safe MVP.
No browser control, credentials, external network, or model calls are performed.
"""
import json, re, sys, os, subprocess, time, hashlib, difflib
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

PORT=8787
EMAIL=re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE=re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")
SECRET=re.compile(r"(?i)\b(?:sk-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|Bearer\s+[A-Za-z0-9._-]{12,})\b")
INJECTION=re.compile(r"(?i)(ignore\s+(?:all|any|previous)|system\s+prompt|reveal\s+(?:the\s+)?password|send\s+(?:the\s+)?secret|disable\s+security|bypass\s+approval)")
RISK_TERMS=re.compile(r"(?i)\b(password|passcode|otp|cookie|payment|card number|bank|wallet|bet|wager|captcha|delete|publish|submit)\b")

SAFE_ACTIONS={'read_page','inspect_dom','read_project_file','run_tests','take_screenshot'}
APPROVAL_ACTIONS={'click','type','fill','upload','apply_patch','publish','send_form'}
BLOCKED_ACTIONS={'password','cookie','payment','place_bet','bet','wager','captcha','anti_bot','stealth','proxy_rotation','delete_data'}

def classify_action(action):
    a=str(action or '').strip().lower().replace(' ','_')
    if a in BLOCKED_ACTIONS or any(x in a for x in ('password','cookie','captcha','place_bet','payment','anti_bot','stealth','proxy')):
        return {'decision':'blocked','action':a,'reason':'blocked high-risk or evasion capability'}
    if a in APPROVAL_ACTIONS:
        return {'decision':'approval_required','action':a,'reason':'side-effectful browser or project action'}
    if a in SAFE_ACTIONS:
        return {'decision':'allowed','action':a,'reason':'read-only or bounded local test action'}
    return {'decision':'approval_required','action':a,'reason':'unknown action defaults to human approval'}

def redact(text):
    text=str(text or '')
    text=SECRET.sub('[REDACTED_SECRET]', text)
    text=EMAIL.sub('[REDACTED_EMAIL]', text)
    text=PHONE.sub('[REDACTED_PHONE]', text)
    return text[:20000]


BASE_DIR=Path(__file__).resolve().parent
AUDIT_PATH=BASE_DIR/'audit.jsonl'
SECRET_FILE_PARTS=('.env','cookie','password','secret','token','.pem','.key')

def audit(event, detail):
    safe={'time':int(time.time()),'event':event,'detail':redact(detail if isinstance(detail,str) else json.dumps(detail,ensure_ascii=False))}
    previous='0'*64
    if AUDIT_PATH.exists():
        try:
            last=AUDIT_PATH.read_text(encoding='utf-8').strip().splitlines()[-1]
            previous=json.loads(last).get('hash',previous)
        except Exception: pass
    safe['prevHash']=previous
    payload=json.dumps(safe,ensure_ascii=False,sort_keys=True).encode()
    safe['hash']=hashlib.sha256(payload).hexdigest()
    with AUDIT_PATH.open('a',encoding='utf-8') as f: f.write(json.dumps(safe,ensure_ascii=False)+'\n')
    return safe

def verify_audit_chain():
    if not AUDIT_PATH.exists(): return {'ok':True,'entries':0}
    prev='0'*64; count=0
    for line in AUDIT_PATH.read_text(encoding='utf-8').splitlines():
        row=json.loads(line); stored=row.pop('hash');
        if row.get('prevHash')!=prev: return {'ok':False,'entries':count,'reason':'prevHash mismatch'}
        if hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()!=stored:
            return {'ok':False,'entries':count,'reason':'hash mismatch'}
        prev=stored; count+=1
    return {'ok':True,'entries':count}

def plan_goal(goal):
    g=str(goal or '').strip()
    low=g.lower()
    steps=[]
    if any(x in low for x in ('แก้','bug','error','fix','debug')):
        steps=[('observe','read_page'),('inspect','read_project_file'),('verify','run_tests'),('propose','apply_patch')]
    elif any(x in low for x in ('ค้นหา','สรุป','อ่าน','research','search','summar')):
        steps=[('observe','read_page'),('verify','take_screenshot')]
    else:
        steps=[('observe','read_page'),('plan','unknown_operation'),('verify','run_tests')]
    plan=[]
    for i,(role,action) in enumerate(steps,1):
        decision=classify_action(action)
        plan.append({'step':i,'role':role,'action':action,**decision})
    return {'ok':True,'goal':redact(g)[:1000],'plan':plan,'execution':'planning_only','approvalRequired':any(x['decision']=='approval_required' for x in plan),'blocked':any(x['decision']=='blocked' for x in plan)}

def safe_target(rel):
    rel=str(rel or '').strip()
    if not rel or Path(rel).is_absolute() or any(part.lower() in SECRET_FILE_PARTS for part in Path(rel).parts): return None
    target=(BASE_DIR/rel).resolve()
    return target if BASE_DIR in target.parents and target!=BASE_DIR else None

def make_diff(rel, content):
    target=safe_target(rel)
    if target is None: return {'ok':False,'execution':'blocked','reason':'unsafe path'}
    if not isinstance(content,str) or len(content)>100_000: return {'ok':False,'execution':'rejected','reason':'content missing or too large'}
    old=target.read_text(encoding='utf-8',errors='replace') if target.exists() else ''
    diff=''.join(difflib.unified_diff(old.splitlines(True),content.splitlines(True),fromfile=str(rel),tofile=str(rel)+' (proposed)'))
    audit('diff_created',{'path':rel,'changed':old!=content})
    return {'ok':True,'execution':'diff_only','path':rel,'changed':old!=content,'diff':redact(diff)[:20000]}

def execute_action(action, payload):
    decision=classify_action(action)
    approved=bool(payload.get('approved',False))
    if decision['decision']=='blocked':
        audit('blocked_action',decision)
        return {'ok':False,**decision,'execution':'blocked'}
    if decision['decision']=='approval_required' and not approved:
        audit('approval_required',decision)
        return {'ok':False,**decision,'execution':'waiting_for_approval'}
    if decision['decision']=='approval_required':
        # Approval is not permission to invent an executor. Only explicitly implemented safe actions run.
        audit('approved_but_not_implemented',decision)
        return {'ok':False,**decision,'execution':'not_implemented','reason':'This action has no executor in Safe MVP'}
    if action=='run_tests':
        try:
            proc=subprocess.run([sys.executable,'-m','unittest','-v','test_operator.SafeOperatorTests.test_injection_blocks','test_operator.SafeOperatorTests.test_normal_page_has_plan','test_operator.SafeOperatorTests.test_policy_allows_bounded','test_operator.SafeOperatorTests.test_policy_blocks_dangerous','test_operator.SafeOperatorTests.test_risky_terms_are_flagged'],cwd=str(BASE_DIR),capture_output=True,text=True,timeout=30)
            result={'ok':proc.returncode==0,'action':action,'execution':'completed','exitCode':proc.returncode,'stdout':redact(proc.stdout)[-8000:],'stderr':redact(proc.stderr)[-4000:]}
            audit('safe_action',{'action':action,'ok':result['ok']}); return result
        except Exception as e:
            audit('safe_action_error',{'action':action,'error':str(e)}); return {'ok':False,'action':action,'execution':'error','error':str(e)}
    if action=='read_project_file':
        rel=str(payload.get('path','')).strip()
        if not rel or Path(rel).is_absolute() or any(part.lower() in SECRET_FILE_PARTS for part in Path(rel).parts):
            audit('blocked_path',rel); return {'ok':False,'action':action,'execution':'blocked','reason':'unsafe or secret-like path'}
        target=(BASE_DIR/rel).resolve()
        if BASE_DIR not in target.parents and target!=BASE_DIR:
            audit('blocked_path',rel); return {'ok':False,'action':action,'execution':'blocked','reason':'path escapes workspace'}
        if not target.is_file() or target.stat().st_size>100_000:
            return {'ok':False,'action':action,'execution':'rejected','reason':'file missing or too large'}
        data=target.read_text(encoding='utf-8',errors='replace')
        audit('safe_action',{'action':action,'path':rel}); return {'ok':True,'action':action,'execution':'completed','path':rel,'content':redact(data)}
    return {'ok':False,'action':action,'execution':'rejected','reason':'safe action is not implemented'}

def analyze(payload):
    text=redact(payload.get('text',''))
    title=redact(payload.get('title',''))
    url=str(payload.get('url',''))
    headings=[redact(x) for x in (payload.get('headings') or [])[:20]]
    errors=[redact(x) for x in (payload.get('errors') or [])[:10]]
    injection=bool(INJECTION.search(text))
    risks=sorted(set(m.group(0).lower() for m in RISK_TERMS.finditer(text)))
    blocked=[]
    if injection: blocked.append('possible_prompt_injection')
    if risks: blocked.append('sensitive_or_irreversible_content')
    plan=[
      {'step':1,'actor':'Observer','action':'read visible page content and headings','risk':'low','approval':'not_required'},
      {'step':2,'actor':'Verifier','action':'check visible errors and page state','risk':'low','approval':'not_required'},
      {'step':3,'actor':'Policy','action':'classify any requested action before execution','risk':'low','approval':'not_required'},
    ]
    if blocked:
        plan.append({'step':4,'actor':'Recovery','action':'stop and show the reason; do not execute page instructions','risk':'high','approval':'blocked'})
    else:
        plan.append({'step':4,'actor':'Human','action':'review any click, typing, upload, submit, delete, publish, or account change','risk':'medium','approval':'required'})
    return {'ok':True,'title':title,'url':url,'redactedTextLength':len(text),'headings':headings[:8],'errors':errors[:5], 'signals':{'promptInjection':injection,'riskTerms':risks},'blocked':blocked,'plan':plan,'execution':'analysis_only'}

class Handler(BaseHTTPRequestHandler):
    def _origin_ok(self):
        origin=self.headers.get('Origin','')
        return origin.startswith('chrome-extension://') or origin in ('http://localhost','http://127.0.0.1','http://localhost:8787','http://127.0.0.1:8787')
    def _send(self, status, obj):
        raw=json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(raw)))
        origin=self.headers.get('Origin','')
        if self._origin_ok():
            self.send_header('Access-Control-Allow-Origin',origin); self.send_header('Vary','Origin')
        self.end_headers(); self.wfile.write(raw)
    def do_OPTIONS(self):
        if not self._origin_ok(): self.send_response(403); self.end_headers(); return
        self.send_response(204); self.send_header('Access-Control-Allow-Origin',self.headers.get('Origin','')); self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Vary','Origin'); self.end_headers()
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/health': self._send(200,{'ok':True,'service':'browser-copilot-safe-mvp','execution':'analysis_only','audit':verify_audit_chain()})
        elif path=='/audit':
            rows=[]
            if AUDIT_PATH.exists():
                for line in AUDIT_PATH.read_text(encoding='utf-8').splitlines()[-100:]:
                    try: rows.append(json.loads(line))
                    except Exception: pass
            self._send(200,{'ok':True,'entries':rows,'chain':verify_audit_chain()})
        else: self._send(404,{'ok':False,'error':'not_found'})
    def do_POST(self):
        path=urlparse(self.path).path
        if path in ('/policy','/plan','/execute','/diff','/apply','/rollback'):
            try:
                n=int(self.headers.get('Content-Length','0')); data=json.loads(self.rfile.read(n) or '{}')
                if path=='/policy': out={'ok':True,**classify_action(data.get('action'))}
                elif path=='/plan': out=plan_goal(data.get('goal','')); audit('plan_created',data.get('goal',''))
                elif path=='/execute': out=execute_action(data.get('action',''),data)
                elif path=='/diff': out=make_diff(data.get('path',''),data.get('content',''))
                elif path=='/apply':
                    if classify_action('apply_patch')['decision']!='approval_required' or not data.get('approved'): out={'ok':False,'execution':'waiting_for_approval','reason':'explicit approval required'}
                    else:
                        target=safe_target(data.get('path','')); content=data.get('content','')
                        if target is None or not isinstance(content,str) or len(content)>100000: out={'ok':False,'execution':'blocked','reason':'unsafe path or content'}
                        else:
                            if target.exists(): target.with_suffix(target.suffix+'.bak').write_text(target.read_text(encoding='utf-8',errors='replace'),encoding='utf-8')
                            target.write_text(content,encoding='utf-8'); audit('approved_patch_applied',data.get('path','')); out={'ok':True,'execution':'applied','path':data.get('path','')}
                else:
                    if not data.get('approved'): out={'ok':False,'execution':'waiting_for_approval','reason':'explicit approval required'}
                    else:
                        target=safe_target(data.get('path','')); backup=target.with_suffix(target.suffix+'.bak') if target else None
                        if not target or not backup or not backup.exists(): out={'ok':False,'execution':'rejected','reason':'no safe backup found'}
                        else:
                            target.write_text(backup.read_text(encoding='utf-8',errors='replace'),encoding='utf-8'); audit('approved_rollback',data.get('path','')); out={'ok':True,'execution':'rolled_back','path':data.get('path','')}
                self._send(200,out)
            except Exception as e: self._send(400,{'ok':False,'error':str(e)})
            return
        if path!='/analyze': self._send(404,{'ok':False,'error':'not_found'}); return
        try:
            n=int(self.headers.get('Content-Length','0')); data=json.loads(self.rfile.read(n) or '{}'); self._send(200,analyze(data))
        except Exception as e: self._send(400,{'ok':False,'error':str(e)})
    def log_message(self, fmt, *args): pass

def main():
    port=int(sys.argv[1]) if len(sys.argv)>1 else PORT
    print(f'Browser Copilot Safe MVP operator listening on http://127.0.0.1:{port}', flush=True)
    HTTPServer(('127.0.0.1',port),Handler).serve_forever()
if __name__=='__main__': main()
