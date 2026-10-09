"""Validate generated local reference documents using Python's standard library."""
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.links.append(value)
            if key == 'id':
                assert value not in self.ids, f'Duplicate HTML ID: {value}'
                self.ids.add(value)


def local_path(base, value):
    parsed = urlsplit(value)
    assert not parsed.scheme and not parsed.netloc, f'Expected local asset: {value}'
    target = (base / unquote(parsed.path)).resolve()
    assert target.is_relative_to(ROOT), f'Asset outside kit: {value}'
    assert target.is_file(), f'Missing local file: {value}'
    return target


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    candidates = manifest['candidates']
    ids = [candidate['id'] for candidate in candidates]
    assert all(type(ident) is int and ident > 0 for ident in ids), 'Invalid ID'
    assert len(set(ids)) == len(ids) == manifest['reference_count'], 'Reference count or duplicate IDs'
    assert ids == sorted(ids), 'Candidate IDs must be ordered'
    assert len(set(manifest['selected_ids'])) == len(manifest['selected_ids']) <= 3, 'Invalid selection'
    assert set(manifest['selected_ids']).issubset(ids), 'Unknown selected ID'
    scenes = json.loads((ROOT / 'scenes.json').read_text(encoding='utf-8'))
    scene_ids = [int(scene['id']) for scene in scenes]
    assert len(scenes) == len(set(scene_ids)) == manifest['concept_count'] == len(candidates), 'Concept count or duplicate IDs'
    assert set(scene_ids) == set(ids), 'Concept ID mismatch'
    wrapped = (ROOT / 'gallery/scenes.js').read_text(encoding='utf-8')
    scene_match = re.fullmatch(r'window\.MATCHROOM_SCENES=(.*);\nwindow\.MATCHROOM_SELECTED_IDS=(.*);\s*', wrapped, re.S)
    assert scene_match, 'Scene wrapper format'
    assert json.loads(scene_match[1]) == sorted(scenes, key=lambda scene: int(scene['id'])), 'Stale scene wrapper'
    assert json.loads(scene_match[2]) == manifest['selected_ids'], 'Stale selected-ID wrapper'
    gallery = json.loads((ROOT / 'gallery/references.json').read_text(encoding='utf-8'))
    assert len(gallery) == len(candidates) and [ref['id'] for ref in gallery] == ids, 'Gallery metadata mismatch'
    required = ('title_ko', 'reference_name', 'source_url', 'visual_description', 'visual_principle',
                'suitable_tasks', 'reuse_rule', 'category', 'tradeoff', 'matchroom_adaptation',
                'interaction_idea', 'evidence_status', 'snapshot_date', 'snapshot_type', 'concept_status')
    for candidate, ref in zip(candidates, gallery):
        ident = candidate['id']
        assert all(candidate.get(key) for key in required), f'Incomplete candidate {ident}'
        assert candidate['concept_status'] == 'unimplemented_design_study', f'Concept status {ident}'
        assert ref == {**candidate, 'image_url': '../' + candidate['local_reference_image']}, f'Stale reference metadata {ident}'
        photo = local_path(ROOT, candidate['local_reference_image'])
        header = photo.read_bytes()[:12]
        assert header.startswith(b'\xff\xd8\xff') or header.startswith(b'\x89PNG\r\n\x1a\n') or (header[:4] == b'RIFF' and header[8:12] == b'WEBP'), f'Invalid local reference image: {photo}'
        assert local_path(ROOT / 'gallery', ref['image_url']) == photo, f'Gallery asset mismatch {ident}'
        svg_file = local_path(ROOT, candidate['local_concept_image'])
        svg, scene_svg = ET.parse(svg_file).getroot(), ET.fromstring(next(scene['svg'] for scene in scenes if int(scene['id']) == ident))
        for element in (svg, scene_svg):
            assert element.tag == '{http://www.w3.org/2000/svg}svg' and element.get('viewBox'), f'SVG metadata {ident}'
            assert '미구현' in ''.join(element.itertext()) or '미구현' in element.get('aria-label', ''), f'SVG missing status {ident}'
        assert svg.get('viewBox') == scene_svg.get('viewBox'), f'SVG dimension mismatch {ident}'
        note = ROOT / 'candidates' / f'{ident:02d}.md'
        text = note.read_text(encoding='utf-8')
        assert candidate['source_url'] in text and candidate['title_ko'] in text and '미구현' in text, f'Note mismatch {ident}'
        assert urlsplit(candidate['source_url']).scheme == 'https', f'Source URL must be HTTPS: {ident}'
        assert candidate['selected'] == (ident in manifest['selected_ids']), f'Selection mismatch {ident}'
    parsed_html = {}
    for file in ROOT.rglob('*.html'):
        if '.git' in file.parts:
            continue
        parser = Links()
        parser.feed(file.read_text(encoding='utf-8'))
        parsed_html[file.resolve()] = parser
    book = parsed_html[(ROOT / 'index.html').resolve()]
    assert {f'ui-{ident:02d}' for ident in ids}.issubset(book.ids), 'Missing book cards'
    assert 'fetch(' not in (ROOT / 'index.html').read_text(encoding='utf-8'), 'Offline book must not fetch'
    for file, parser in parsed_html.items():
        for link in parser.links:
            parsed = urlsplit(link)
            if parsed.scheme or not parsed.path:
                continue
            target = local_path(file.parent, link)
            if parsed.fragment and target in parsed_html:
                assert unquote(parsed.fragment) in parsed_html[target].ids, f'Missing HTML anchor: {file} {link}'
    for file in ROOT.rglob('*.md'):
        if '.git' in file.parts:
            continue
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
            parsed = urlsplit(link.strip('<>'))
            if not parsed.scheme and parsed.path:
                local_path(file.parent, link.strip('<>'))
    for file in ROOT.rglob('*'):
        if not file.is_file() or '.git' in file.parts or file.suffix not in {'.md', '.json', '.html', '.js', '.py', '.css'}:
            continue
        text = file.read_text(encoding='utf-8')
        assert not re.search(r'[A-Za-z]:[/\\]Users[/\\]', text), 'Machine-specific path: ' + str(file)
        assert not re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----', text), 'Credential marker: ' + str(file)
    print(f'PASS: {len(ids)} references, {len(scenes)} SVGs, scene/gallery consistency, notes, local links, privacy markers')


if __name__ == '__main__':
    main()
