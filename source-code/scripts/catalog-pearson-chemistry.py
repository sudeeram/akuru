#!/usr/bin/env python3
"""Create a read-only intake catalogue for local Pearson 4CH1 Chemistry PDFs.

The output is kept beside ignored source files; this does not upload or publish content.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import pymupdf

KINDS = {'question-paper': 'past_paper', 'mark-scheme': 'mark_scheme', 'examiner-report': 'examiner_report'}
COMPONENTS = ('1C', '2C', '1CR', '2CR')
FIELDS = ('paper_key', 'qualification', 'specification', 'session', 'year', 'month', 'component',
          'paper_number', 'variant', 'kind', 'source_path', 'sha256', 'bytes', 'pdf_pages',
          'pages_with_text', 'internal_code_check', 'source_paper_key', 'review_status', 'note')


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def identity(path: Path):
    match = re.search(r'(January|June|November)\s+(20\d{2})\.pastpapers$', path.parts[-3])
    if not match:
        raise ValueError(f'Unrecognised exam session: {path}')
    month, year = match.groups()
    folder = path.parent.name.lower()
    if folder not in KINDS:
        raise ValueError(f'Unrecognised document kind: {path}')
    paper = re.search(r'Paper(1CR|2CR|1C|2C|CR)-', path.name, re.I)
    if not paper:
        raise ValueError(f'Unrecognised paper component: {path}')
    component = paper.group(1).upper()
    note = ''
    if component == 'CR':
        if (month, year) != ('January', '2020'):
            raise ValueError(f'Ambiguous component requires manual review: {path}')
        component = '2CR'
        note = 'Filename says PaperCR; internal PDF title identifies Paper 2CR.'
    return month, year, KINDS[folder], component, note


def make_catalogue(root: Path):
    rows = []
    seen = set()
    files = sorted(root.glob('*.pastpapers/*/*.pdf'))
    for path in files:
        month, year, kind, component, note = identity(path)
        paper_key = f'4CH1-2017-{year}-{month.upper()}-{component}'
        pair = (paper_key, kind)
        if pair in seen:
            raise ValueError(f'Duplicate catalogue identity: {pair}')
        seen.add(pair)
        with pymupdf.open(path) as doc:
            if doc.page_count == 0:
                raise ValueError(f'Empty PDF: {path}')
            pages = len(doc)
            text_pages = sum(bool(page.get_text().strip()) for page in doc)
            front_text = ' '.join(doc[i].get_text() for i in range(min(4, pages)))
            codes = {code.upper() for code in re.findall(
                r'(?:4CH[I1]{1,2}\s*[/ ]\s*|\bPaper\s*)([12]C(?:R)?)\b', front_text, re.I)}
            if codes and component not in codes:
                raise ValueError(f'Internal paper code disagrees with filename: {path}, {codes}')
            code_check = 'matched' if codes else 'manual_review'
            if not codes:
                note += ' Internal paper code could not be extracted from the first four pages.'
            if text_pages == 0:
                note += ' No extractable text; OCR required.'
        rows.append(dict(paper_key=paper_key, qualification='4CH1', specification='2017',
                         session=f'{month} {year}', year=year, month=month, component=component,
                         paper_number=component[0], variant='regional' if component.endswith('R') else 'standard',
                         kind=kind, source_path=str(path.relative_to(root)), sha256=file_hash(path),
                         bytes=str(path.stat().st_size), pdf_pages=str(pages), pages_with_text=str(text_pages),
                         internal_code_check=code_check,
                         source_paper_key='' if kind == 'past_paper' else paper_key,
                         review_status='pending', note=note.strip()))
    if not files:
        raise ValueError(f'No PDFs found beneath {root}')
    by_paper = defaultdict(set)
    for row in rows:
        by_paper[row['paper_key']].add(row['kind'])
    if any('past_paper' not in kinds for kinds in by_paper.values()):
        raise ValueError('A companion document has no matching question paper')
    return rows, by_paper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    rows, by_paper = make_catalogue(root)
    spec = root / 'specification' / 'Pearson-Edexcel-International-GCSE-Chemistry-4CH1-2017-Specification-Issue-3-September-2024.pdf'
    if not spec.is_file():
        raise ValueError('Official specification PDF is missing')
    with (root / 'intake-catalogue.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader();writer.writerows(rows)
    audit = {'qualification': '4CH1', 'specification': '2017', 'document_count': len(rows),
             'paper_count': len(by_paper), 'specification_path': str(spec.relative_to(root)),
             'specification_sha256': file_hash(spec),
             'manual_code_checks': [row['source_path'] for row in rows if row['internal_code_check'] == 'manual_review'],
             'incomplete_sets': [{'paper_key': key, 'missing': sorted({'mark_scheme','examiner_report'} - kinds)}
                                 for key, kinds in sorted(by_paper.items()) if kinds != {'past_paper','mark_scheme','examiner_report'}],
             'filename_corrections': [{'paper_key': row['paper_key'], 'kind': row['kind'], 'note': row['note']}
                                      for row in rows if 'Filename says PaperCR' in row['note']]}
    (root / 'intake-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
