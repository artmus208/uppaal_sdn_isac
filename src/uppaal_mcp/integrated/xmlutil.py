"""Small XML construction and lexical alpha-renaming helpers.

Only the pinned scalar, zero-argument template dialect is supported. Identifiers
are renamed injectively, including function parameters, template locals and edge
selections. Thus lexical shadowing is preserved rather than resolved by textual
substring replacement. Comments, strings and location/member names are untouched.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_][A-Za-z_0-9]*|.', re.S)
IDENT = re.compile(r'[A-Za-z_][A-Za-z_0-9]*\Z')
RESERVED = set('const int bool clock chan broadcast urgent typedef void return if else true false for while do break continue scalar struct system process not and or imply deadlock A E forall exists sum double rate hybrid'.split())


def rename(text: str, prefix: str, processes: dict[str, str] | None = None) -> str:
    """Alpha-convert all non-keyword identifiers; preserve scoped member names."""
    result, previous = [], ''
    for token in TOKEN.findall(text):
        if IDENT.fullmatch(token) and token not in RESERVED and previous != '.':
            result.append((processes or {}).get(token, prefix + token))
        else:
            result.append(token)
        if not token.isspace() and not token.startswith(('//', '/*')):
            previous = token
    return ''.join(result)


def label(edge, kind):
    return edge.findtext(f"label[@kind='{kind}']") or ''


def set_label(edge, kind, text):
    node = edge.find(f"label[@kind='{kind}']")
    if not text:
        if node is not None:
            edge.remove(node)
        return
    if node is None:
        node = ET.SubElement(edge, 'label', {'kind': kind})
    node.text = text


def append_update(edge, text):
    set_label(edge, 'assignment', ', '.join(filter(None, [label(edge, 'assignment'), text])))


def location(template, name, invariant='', committed=False):
    index = len(template.findall('location'))
    ident = f"{template.findtext('name')}_{name}"
    loc = ET.SubElement(template, 'location', {'id': ident, 'x': str(index % 5 * 240), 'y': str(index // 5 * 180)})
    ET.SubElement(loc, 'name').text = name
    if invariant:
        ET.SubElement(loc, 'label', {'kind': 'invariant'}).text = invariant
    if committed:
        ET.SubElement(loc, 'committed')
    return ident


def loc_id(template, name):
    return next(x.get('id') for x in template.findall('location') if x.findtext('name') == name)


def edge(template, source, target, guard='', sync='', update='', select=''):
    tr = ET.SubElement(template, 'transition')
    ET.SubElement(tr, 'source', {'ref': loc_id(template, source)})
    ET.SubElement(tr, 'target', {'ref': loc_id(template, target)})
    for kind, text in [('select', select), ('guard', guard), ('synchronisation', sync), ('assignment', update)]:
        set_label(tr, kind, text)
    return tr


def template(name, locations, declarations=''):
    node = ET.Element('template')
    ET.SubElement(node, 'name').text = name
    if declarations:
        ET.SubElement(node, 'declaration').text = declarations
    for item in locations:
        if isinstance(item, str):
            location(node, item)
        else:
            location(node, *item)
    ET.SubElement(node, 'init', {'ref': node.find('location').get('id')})
    return node


def source_name(t, tr):
    ref = tr.find('source').get('ref')
    return next(x.findtext('name') for x in t.findall('location') if x.get('id') == ref)


def normalize_order(t):
    order = {'name': 0, 'parameter': 1, 'declaration': 2, 'location': 3, 'branchpoint': 4, 'init': 5, 'transition': 6}
    t[:] = sorted(t, key=lambda x: order[x.tag])
