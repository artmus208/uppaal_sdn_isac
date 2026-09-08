"""Concrete edge replay for software regressions, NOT an UPPAAL verifier.

Interprets the scalar expression/assignment subset used by boundary edges. Tests
choose transitions and times explicitly; there is no state-space exploration,
zone semantics, fairness analysis or inference of temporal query verdicts. Calls
and unsupported expressions fail unless supplied explicitly by the test fixture.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import re
import xml.etree.ElementTree as ET
from .xmlutil import label, source_name


def split(text, separator=','):
    depth=0
    start=0
    parts=[]
    for i,c in enumerate(text):
        if c in '([': depth+=1
        elif c in ')]': depth-=1
        elif c==separator and depth==0:
            parts.append(text[start:i].strip());start=i+1
    parts.append(text[start:].strip())
    return [p for p in parts if p]


def expression(text, values):
    text=text.strip()
    # Recursively replace parenthesized C expressions before handling the ternary.
    tokens=[]
    i=0
    while i<len(text):
        if text[i]=='(':
            start=i;depth=1;i+=1
            while i<len(text) and depth:
                depth += (text[i]=='(')-(text[i]==')');i+=1
            if depth: raise ValueError('unbalanced expression')
            inner=text[start+1:i-1]
            # A function argument list is kept, with each argument translated.
            if tokens and re.search(r'\w$',tokens[-1]):
                tokens.append('('+', '.join(repr(expression(p,values)) for p in split(inner))+')')
            else:
                tokens.append(repr(expression(inner,values)))
        else:
            tokens.append(text[i]);i+=1
    text=''.join(tokens)
    if '?' in text:
        condition, rest=text.split('?',1)
        depth=0;cut=None
        for i,c in enumerate(rest):
            if c=='?':depth+=1
            elif c==':':
                if depth==0:cut=i;break
                depth-=1
        if cut is None:raise ValueError('incomplete conditional')
        return expression(rest[:cut] if expression(condition,values) else rest[cut+1:],values)
    text=re.sub(r'!(?!=)',' not ',text).replace('&&',' and ').replace('||',' or ')
    text=re.sub(r'\btrue\b','True',text);text=re.sub(r'\bfalse\b','False',text)
    tree=ast.parse(text.strip(),mode='eval')
    allowed=(ast.Expression,ast.Constant,ast.Name,ast.Load,ast.BoolOp,ast.And,ast.Or,ast.UnaryOp,ast.Not,
             ast.USub,ast.UAdd,ast.BinOp,ast.Add,ast.Sub,ast.Mult,ast.Div,ast.Mod,ast.Compare,
             ast.Eq,ast.NotEq,ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Call)
    if any(not isinstance(node,allowed) for node in ast.walk(tree)):
        raise ValueError('unsupported replay expression')
    return eval(compile(tree,'<boundary-replay>','eval'),{'__builtins__':{}},values)


def assign(text,values):
    for part in split(text):
        m=re.fullmatch(r'(\w+)\s*=\s*(.+)',part,flags=re.S)
        if m:values[m[1]]=expression(m[2],values)
        else:expression(part,values)


class Replay:
    """Replay selected boundary/core handshakes with receiver guards evaluated first."""
    def __init__(self, model_xml, values=None, processes=None):
        self.root=ET.fromstring(model_xml)
        self.templates={t.findtext('name'):t for t in self.root.findall('template')}
        system=self.root.findtext('system') or ''
        bindings=re.findall(r'(\w+)\s*=\s*(\w+)\(\);',system)
        self.processes={p:self.templates[t] for p,t in bindings}
        if processes is not None:
            self.processes={p:self.processes[p] for p in processes}
        self.locations={p:t.find('init').get('ref') for p,t in self.processes.items()}
        self.values=dict(values or {})
        self.locals={p:{} for p in self.processes}
        self.clocks=set()
        # Constants and explicit globals can be taken from the document. Function
        # bodies are deliberately excluded; tests must supply their implementations
        # when a selected edge invokes a function.
        depth=0;surface=[]
        for line in (self.root.findtext('declaration') or '').splitlines():
            line=line.split('//')[0]
            if depth==0 and '{' not in line:surface.append(line)
            depth+=line.count('{')-line.count('}')
        for stmt in ''.join(surface).split(';'):
            self._declare(stmt,self.values,self.clocks)
        self.values.update(values or {})
        for p,t in self.processes.items():
            clocks=set()
            for stmt in (t.findtext('declaration') or '').split(';'):
                self._declare(stmt,self.locals[p],clocks)
            self.locals[p]['__clocks__']=clocks
        self.trace=[]

    def _declare(self,stmt,values,clocks):
        stmt=stmt.strip()
        if stmt.startswith('clock '):
            for name in stmt[6:].split(','):
                clocks.add(name.strip());values.setdefault(name.strip(),0)
            return
        m=re.fullmatch(r'(?:const\s+)?(?:\w+)(?:\[[^]]+\])?\s+(.+)',stmt,re.S)
        if not m or stmt.startswith(('typedef ','chan ','broadcast ')):return
        for item in split(m[1]):
            n=re.fullmatch(r'(\w+)(?:\s*=\s*(.+))?',item,re.S)
            if not n:continue
            try: values.setdefault(n[1],expression(n[2],dict(self.values,**values)) if n[2] else 0)
            except (NameError,SyntaxError,ValueError): pass

    def context(self,p,select=None):
        return dict(self.values,**self.locals[p],**(select or {}))

    def state(self,p):
        return next(x.findtext('name') for x in self.processes[p].findall('location') if x.get('id')==self.locations[p])

    def candidates(self,p,sync=None,target=None,select=None):
        t=self.processes[p]
        ids={x.get('id'):x.findtext('name') for x in t.findall('location')}
        return [tr for tr in t.findall('transition') if tr.find('source').get('ref')==self.locations[p]
                and (sync is None or label(tr,'synchronisation')==sync)
                and (target is None or ids[tr.find('target').get('ref')]==target)
                and (not label(tr,'guard') or expression(label(tr,'guard'),self.context(p,select)))]

    def take(self,choices):
        """choices: [(process, exact edge, selection mapping), ...], sender first.

        Tests supply every participant of the selected handshake. This is not a
        global enabled-transition enumerator; broadcasts/committed scheduling are
        tested structurally in addition to the concrete traces.
        """
        saved=(deepcopy(self.values),deepcopy(self.locals),dict(self.locations))
        for p,tr,select in choices:
            if self.locations[p]!=tr.find('source').get('ref'):
                raise ValueError('wrong source location')
            if label(tr,'guard') and not expression(label(tr,'guard'),self.context(p,select)):
                raise ValueError('disabled pre-state guard')
            declared={}
            for entry in split(label(tr,'select')):
                m=re.fullmatch(r'(\w+)\s*:\s*int\[([^,]+),([^]]+)\]',entry)
                if not m:raise ValueError('unsupported selection type')
                declared[m[1]]=(expression(m[2],self.context(p)),expression(m[3],self.context(p)))
            if set(select)!=set(declared):raise ValueError('missing or extra selection values')
            for name,(low,high) in declared.items():
                if type(select[name]) is not int or not low<=select[name]<=high:
                    raise ValueError('selection outside its finite domain')
        syncs=[label(tr,'synchronisation') for _,tr,_ in choices if label(tr,'synchronisation')]
        if len(choices)>1 and (not syncs or not syncs[0].endswith('!') or any(s!=syncs[0][:-1]+'?' for s in syncs[1:])):
            raise ValueError('unmatched handshake')
        try:
            for p,tr,select in choices:
                values=self.context(p,select)
                assign(label(tr,'assignment'),values)
                for name,value in values.items():
                    if name in self.locals[p]:self.locals[p][name]=value
                    elif name not in (select or {}):self.values[name]=value
                self.locations[p]=tr.find('target').get('ref')
            self._invariants()
        except Exception:
            self.values,self.locals,self.locations=saved
            raise
        self.trace.append([{'process':p,'from':source_name(self.processes[p],tr),'to':self.state(p),'sync':label(tr,'synchronisation')} for p,tr,_ in choices])

    def _invariants(self):
        for p,t in self.processes.items():
            loc=next(x for x in t.findall('location') if x.get('id')==self.locations[p])
            for inv in loc.findall("label[@kind='invariant']"):
                valid=expression(inv.text,self.context(p))
                if not valid:raise ValueError(f'invariant violated: {p}: {inv.text}')

    def advance(self,dt):
        if dt<0:raise ValueError('negative time')
        for p,t in self.processes.items():
            loc=next(x for x in t.findall('location') if x.get('id')==self.locations[p])
            if dt and (loc.find('committed') is not None or loc.find('urgent') is not None):
                raise ValueError('cannot delay in committed/urgent state')
        saved=(deepcopy(self.values),deepcopy(self.locals))
        for clock in self.clocks:self.values[clock]+=dt
        for p,values in self.locals.items():
            for clock in values['__clocks__']:values[clock]+=dt
        try:self._invariants()
        except Exception:
            self.values,self.locals=saved
            raise
