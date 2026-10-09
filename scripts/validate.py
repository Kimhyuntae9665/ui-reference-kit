"""Validate the reference library with Python's standard library only."""
import json, re, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src') and value:self.links.append(value)

def main():
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    candidates=manifest['candidates'];ids=[c['id'] for c in candidates]
    assert len(set(ids))==len(ids)==manifest['reference_count'],'Reference ID count/duplicates'
    assert set(manifest['selected_ids']).issubset(ids),'Unknown selected ID'
    concepts=json.loads((ROOT/'scenes.json').read_text(encoding='utf-8'))
    assert len(concepts)==manifest['concept_count']==len(candidates),'Concept count'
    assert {int(s['id']) for s in concepts}==set(ids),'Concept ID mismatch'
    gallery=json.loads((ROOT/'gallery/references.json').read_text(encoding='utf-8'))
    assert {r['id'] for r in gallery}==set(ids),'Gallery metadata mismatch'
    for c in candidates:
        photo=ROOT/c['local_reference_image'];svg=ROOT/c['local_concept_image']
        assert photo.is_file() and photo.read_bytes().startswith(b'\xff\xd8\xff'),photo
        ET.parse(svg)
        note=ROOT/'candidates'/f"{c['id']:02d}.md"
        text=note.read_text(encoding='utf-8')
        assert c['source_url'] in text and c['title_ko'] in text,note
        assert urlsplit(c['source_url']).scheme=='https','Source URL must be HTTPS'
        assert c['selected']==(c['id'] in manifest['selected_ids']),'Selection mismatch'
    for file in ROOT.rglob('*.html'):
        parser=Links();parser.feed(file.read_text(encoding='utf-8'))
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or not u.path:continue
            assert (file.parent/unquote(u.path)).is_file(),(file,link)
    for file in ROOT.rglob('*.md'):
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
            u=urlsplit(link.strip('<>'))
            if u.scheme or not u.path:continue
            assert (file.parent/unquote(u.path)).is_file(),(file,link)
    for file in ROOT.rglob('*'):
        if not file.is_file() or '.git' in file.parts or file.suffix not in {'.md','.json','.html','.js','.py','.css'}:continue
        text=file.read_text(encoding='utf-8')
        assert not re.search(r'[A-Za-z]:[/\\]Users[/\\]',text),'Machine-specific path: '+str(file)
        assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',text),'Credential marker: '+str(file)
    print(f'PASS: {len(ids)} references, {len(concepts)} SVGs, notes, metadata, local links, privacy markers')
if __name__=='__main__':main()
