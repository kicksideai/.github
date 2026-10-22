# SPDX-License-Identifier: LicenseRef-KickSide-Community-1.0
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import notices


class NoticesTests(unittest.TestCase):
    def test_locked_archive_preserves_copyright_and_rejects_tampering(self):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            text = b'MIT License\nCopyright Example Authors\n'
            item = tarfile.TarInfo('package/LICENSE')
            item.size = len(text)
            archive.addfile(item, io.BytesIO(text))
            metadata = json.dumps({'license': 'UNLICENSED'}).encode()
            item = tarfile.TarInfo('package/package.json')
            item.size = len(metadata)
            archive.addfile(item, io.BytesIO(metadata))
        data = stream.getvalue()
        component = {'name': 'example', 'version': '1.0', 'hashes': [
            {'alg': 'SHA-512', 'content': hashlib.sha512(data).hexdigest()}],
            'externalReferences': [{'type': 'distribution', 'url': 'https://registry.npmjs.org/example.tgz'}]}
        with tempfile.TemporaryDirectory() as temp:
            with patch('notices.urlopen', return_value=io.BytesIO(data)):
                license_id, texts = notices.npm_texts(component, Path(temp))
            self.assertEqual(license_id, 'UNLICENSED')
            self.assertIn('Copyright Example Authors', texts['LICENSE'])
            next(Path(temp).iterdir()).write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                notices.npm_texts(component, Path(temp))

    def test_generation_keeps_curated_notices_and_is_stable(self):
        curated = '# Third-Party Notices\n\nExisting font and C library notices.\n'
        records = {('npm', 'example', '1.0'): {
            'license': 'MIT', 'sources': {'ui/package-lock.json'},
            'texts': {'LICENSE': 'Copyright Example Authors\nMIT License\n'}}}
        first = notices.render(curated, records)
        second = notices.render(first, records)
        self.assertEqual(first, second)
        self.assertTrue(first.startswith(curated))
        self.assertIn('Copyright Example Authors', first)
        self.assertIn('ui/package-lock.json', first)

    def test_changed_legacy_file_needs_no_mass_header_edit_but_new_source_does(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'legacy.lua').write_text('return {}\n')
            (root / 'new.lua').write_text('return {}\n')
            changes = [('M', 'legacy.lua'), ('A', 'new.lua')]
            self.assertEqual(notices.header_findings(root, changes), ['new.lua: missing SPDX-License-Identifier'])
            (root / 'new.lua').write_text('-- SPDX-License-Identifier: MIT\nreturn {}\n')
            self.assertEqual(notices.header_findings(root, changes), [])

    def test_modified_source_retains_its_existing_header(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'source.lua').write_text('return {}\n')
            before = {'source.lua': '-- SPDX-License-Identifier: MIT\nreturn {}\n'}
            self.assertEqual(notices.header_findings(root, [('M', 'source.lua')], before),
                             ['source.lua: missing SPDX-License-Identifier'])
