#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-KickSide-Community-1.0
"""Generate dependency notices from npm SBOMs and Cargo metadata without changing locks."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
from urllib.request import urlopen

MARKER = '<!-- BEGIN GENERATED DEPENDENCY NOTICES -->'
LEGAL_FILE = re.compile(r'^(licen[cs]e|copying|copyright|notice)([.\-_ ].*)?$', re.I)
SOURCE_SUFFIXES = {'.lua', '.py', '.mjs', '.cjs', '.js', '.jsx', '.ts', '.tsx', '.yaml',
                   '.yml', '.sh', '.ps1', '.css', '.scss', '.vue', '.html', '.md', '.toml', '.rs', '.c', '.h'}
IGNORED_SOURCE_PARTS = {'static', 'ui_fs', 'vendor', 'node_modules'}


def command_json(args, root):
    return json.loads(subprocess.check_output(args, cwd=root, text=True))


def tracked(root):
    return subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')[:-1]


def npm_texts(component, cache):
    urls = [item['url'] for item in component.get('externalReferences', []) if item['type'] == 'distribution']
    if len(urls) != 1:
        raise ValueError('npm dependency has no unique locked archive: ' + component['name'])
    url = urls[0]
    hashes = component['hashes']
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.tgz')
    if not path.exists():
        with urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    for digest in hashes:
        algorithm = digest['alg'].lower().replace('-', '')
        if hashlib.new(algorithm, data).hexdigest() != digest['content']:
            raise ValueError('npm archive integrity mismatch: ' + component['name'])
    if not hashes:
        raise ValueError('npm archive has no integrity: ' + component['name'])
    texts = {}
    license_id = None
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            parts = Path(member.name).parts
            if member.isfile() and member.name == 'package/package.json':
                license_id = json.load(archive.extractfile(member)).get('license')
            if member.isfile() and len(parts) == 2 and LEGAL_FILE.match(parts[-1]):
                texts[parts[-1]] = archive.extractfile(member).read().decode('utf-8')
    return license_id, texts


def wippy_workspace_texts(component, lock_path, root):
    """Read a locked materialized Wippy artifact; never invent an npm archive."""
    name = component['name']
    if not re.fullmatch(r'@[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*', name):
        return None
    expected = '.wippy/npm/' + name
    locations = [p['value'] for p in component.get('properties', [])
                 if p['name'] == 'cdx:npm:package:path']
    if locations != [expected]:
        return None
    packages = json.loads(lock_path.read_text()).get('packages', {})
    package = packages.get(expected, {})
    link = packages.get('node_modules/' + name, {})
    if package.get('version') != component['version'] or link.get('link') is not True or link.get('resolved') != expected:
        raise ValueError('Wippy workspace does not match its lock: ' + name)
    license_id = package.get('license')
    if not isinstance(license_id, str) or not license_id.strip():
        raise ValueError('Wippy workspace has no locked license: ' + name)
    declared = [v.get('expression') or v.get('license', {}).get('id') or v.get('license', {}).get('name')
                for v in component.get('licenses', [])]
    if declared != [license_id]:
        raise ValueError('Wippy workspace license differs from its lock: ' + name)
    directory = lock_path.parent / expected
    if not directory.resolve().is_relative_to(root.resolve()):
        raise ValueError('Wippy workspace resolves outside the repository: ' + name)
    texts = {}
    if not directory.exists():
        raise ValueError('Materialize Wippy build inputs before checking notices: ' + name)
    if directory.exists():
        metadata = json.loads((directory / 'package.json').read_text())
        if any(metadata.get(k) != value for k, value in
               [('name', name), ('version', component['version']), ('license', license_id)]):
            raise ValueError('Materialized Wippy package differs from its lock: ' + name)
        for path in sorted(directory.iterdir()):
            if path.is_file() and LEGAL_FILE.match(path.name):
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError('Wippy workspace legal file resolves outside the repository: ' + name)
                texts[path.name] = path.read_text()
    return license_id, texts


def cargo_texts(package):
    directory = Path(package['manifest_path']).parent
    if package.get('license_file'):
        path = directory / package['license_file']
        return {path.name: path.read_text()}
    # Workspace crates commonly inherit the repository's licence text.
    while True:
        files = sorted(p for p in directory.iterdir() if p.is_file() and LEGAL_FILE.match(p.name))
        if files:
            return {p.name: p.read_text() for p in files}
        if (directory / '.git').exists() or not (directory.parent / 'Cargo.toml').is_file():
            return {}
        directory = directory.parent


def collect(root, cache):
    records = {}
    components = {}
    paths = tracked(root)
    owned = {json.loads((root / path).read_text())["name"] for path in paths
             if Path(path).name == "package.json"}
    for name in paths:
        path = root / name
        if path.name == 'package-lock.json':
            bom = command_json(['npm', 'sbom', '--package-lock-only', '--omit=dev', '--sbom-format=cyclonedx'], path.parent)
            for item in bom.get('components', []):
                if not any(ref['type'] == 'distribution' for ref in item.get('externalReferences', [])) and item['name'] in owned:
                    continue
                key = ('npm', item['name'], item['version'])
                licenses = [value.get('expression') or value['license'].get('id') or value['license']['name']
                            for value in item.get('licenses', [])]
                expression = ' AND '.join(licenses) or 'Not declared in package metadata; see package license text below.'
                row = records.setdefault(key, {'license': expression, 'sources': set(), 'texts': {}})
                if row['license'] != expression:
                    raise ValueError('Inconsistent locked license: ' + item['name'])
                row['sources'].add(name)
                workspace = None
                if not any(ref['type'] == 'distribution' for ref in item.get('externalReferences', [])):
                    workspace = wippy_workspace_texts(item, path, root)
                if workspace is None:
                    components[key] = item
                else:
                    row['texts'].update(workspace[1])
        elif path.name == 'Cargo.lock':
            metadata = command_json(['cargo', 'metadata', '--locked', '--format-version', '1'], path.parent)
            for item in metadata['packages']:
                if item['id'] in metadata['workspace_members']:
                    continue
                key = ('cargo', item['name'], item['version'])
                texts = cargo_texts(item)
                if not item.get('license') and not texts:
                    raise ValueError('Cargo dependency has neither license metadata nor text: ' + item['name'])
                row = records.setdefault(key, {'license': item.get('license') or 'See package license text below.',
                                               'sources': set(), 'texts': texts})
                row['sources'].add(name)
    with ThreadPoolExecutor(max_workers=4) as pool:
        keys = sorted(components)
        for key, (license_id, texts) in zip(keys, pool.map(lambda key: npm_texts(components[key], cache), keys)):
            if records[key]['license'].startswith('Not declared') and isinstance(license_id, str) and license_id.strip():
                records[key]['license'] = license_id
            if not texts and records[key]['license'].startswith('Not declared'):
                raise ValueError('npm dependency has neither license metadata nor text: ' + key[1])
            records[key]['texts'] = texts
    return records


def render(existing, records):
    curated = existing.split(MARKER)[0].rstrip() + '\n\n'
    lines = [curated + MARKER, '', '## Locked npm and Cargo dependencies', '',
             'Generated from production npm lock entries with `npm sbom` and from',
             'Cargo lock entries with `cargo metadata --locked`. Build-only Cargo',
             'dependencies are included. Wippy module licenses remain in their published',
             'packages. Curated notices above cover dependencies outside these ecosystems.',
             'Package-provided license and attribution texts below retain their original wording.', '']
    license_texts = {}
    for (ecosystem, name, version), row in sorted(records.items()):
        lines.extend([f'### {ecosystem}: {name}@{version}', '', 'License: ' + row['license'], '',
                      'Lockfiles: ' + ', '.join('`' + path + '`' for path in sorted(row['sources'])), ''])
        for filename, text in sorted(row['texts'].items()):
            identity = hashlib.sha256(text.encode()).hexdigest()
            license_texts[identity] = text
            lines.extend([f'{filename}: [License text](#license-text-{identity})', ''])
    for identity, text in sorted(license_texts.items()):
        fence = '`' * max(3, max((len(v) for v in re.findall(r'`+', text)), default=0) + 1)
        lines.extend(['## License text ' + identity, '', fence + 'text', '\n'.join(line.rstrip() for line in text.splitlines()), fence, ''])
    return '\n'.join(lines).rstrip() + '\n'


def source_symlink_error(root, path):
    try:
        target = path.resolve(strict=True)
    except FileNotFoundError:
        return 'source symlink is dangling'
    except (OSError, RuntimeError):
        return 'source symlink cannot be resolved'
    try:
        relative = target.relative_to(root)
    except ValueError:
        return 'source symlink escapes repository root'
    if not target.is_file():
        return 'source symlink target is not a regular file'
    if target.suffix not in SOURCE_SUFFIXES:
        return 'source symlink target is not a source file'
    if any(part in IGNORED_SOURCE_PARTS for part in relative.parts):
        return 'source symlink targets ignored source area'
    return None


def header_findings(root, changes, previous=None):
    findings = []
    previous = previous or {}
    for status, name in changes:
        path = root / name
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        if path.is_symlink():
            error = source_symlink_error(root, path)
            if error:
                findings.append(name + ': ' + error)
            continue
        if not path.is_file():
            continue
        if any(part in IGNORED_SOURCE_PARTS for part in path.relative_to(root).parts):
            continue
        required = status == 'A' or 'SPDX-License-Identifier:' in previous.get(name, '')[:2048]
        if required and not re.search(r'SPDX-License-Identifier:\s*\S+', path.read_text()[:2048]):
            findings.append(name + ': missing SPDX-License-Identifier')
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--base', help='Check SPDX headers on source additions since this Git revision.')
    args = parser.parse_args()
    root = args.root.resolve()
    args.cache.mkdir(parents=True, exist_ok=True)
    if args.base:
        data = subprocess.check_output(['git', 'diff', '--no-renames', '--name-status', '-z',
                                        '--diff-filter=AM', args.base], cwd=root).decode().split('\0')[:-1]
        changes = list(zip(data[::2], data[1::2]))
        previous = {name: subprocess.check_output(['git', 'show', args.base + ':' + name],
                                                  cwd=root, text=True)
                    for status, name in changes if status == 'M' and Path(name).suffix in SOURCE_SUFFIXES}
        findings = header_findings(root, changes, previous)
        if findings:
            raise ValueError('\n'.join(findings))
    target = root / 'THIRD_PARTY_NOTICES.md'
    license_id = 'LicenseRef-KickSide-Community-1.0' if (root / 'LICENSE.md').exists() else 'MIT'
    existing = target.read_text() if target.exists() else '<!-- SPDX-License-Identifier: ' + license_id + ' -->\n# Third-Party Notices\n'
    expected = render(existing, collect(root, args.cache))
    if args.check:
        if not target.exists() or existing != expected:
            raise ValueError('THIRD_PARTY_NOTICES.md differs; run legal-notices to regenerate it.')
        print(root.name + ': third-party notices match locked dependencies')
    else:
        target.write_text(expected)
        print(root.name + ': third-party notices generated')


if __name__ == '__main__':
    main()
