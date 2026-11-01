"""Create a portable, data-only ZIP; never includes HTML, scripts or unrelated files.

Run from source-code/backend:
.venv/bin/python scripts/package_prepared_textbook.py /path/ai-prepared-v1 /path/draft.zip
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.prepared_textbooks import read_package


def build(folder: Path, output: Path):
    folder = folder.resolve()
    # A prepared folder may reference source screenshots immediately outside it.
    # Restrict access to its parent topic directory, not arbitrary local files.
    root = folder.parent
    package = json.loads((folder / 'topic-package.json').read_text())
    source_hash = hashlib.sha256((folder / 'topic-package.json').read_bytes()).hexdigest()
    files = {}
    for index, page in enumerate(package['pages'], 1):
        source = (folder / page['sourcePath']).resolve()
        if root not in source.parents: raise ValueError('Source page escapes the topic directory')
        name = f'pages/page-{index:04d}.png'
        files[name] = source.read_bytes(); page['sourcePath'] = name
    for index, figure in enumerate(package['figures'], 1):
        source = (folder / figure['path']).resolve()
        if root not in source.parents: raise ValueError('Figure escapes the topic directory')
        name = f'figures/figure-{index:04d}.png'
        files[name] = source.read_bytes(); figure['path'] = name
    package['provenance']['sourceFirstPackageSha256'] = source_hash
    import io
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('topic-package.json', json.dumps(package, ensure_ascii=False, allow_nan=False))
        for name, content in files.items(): z.writestr(name, content)
    content = stream.getvalue()
    read_package(content)
    if output.exists(): raise FileExistsError('Choose a new candidate output path; existing packages are never overwritten')
    output.write_bytes(content)
    print(f'Validated package: {output} ({len(content):,} bytes)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.folder, args.output)
