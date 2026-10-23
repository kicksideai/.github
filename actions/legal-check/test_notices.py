# SPDX-License-Identifier: LicenseRef-KickSide-Community-1.0
import hashlib
import io
import json
import os
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

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks are unavailable')
    def test_source_symlink_to_in_repo_source_is_not_new_authored_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'legacy.lua').write_text('return {}\n')
            (root / 'assist_under_test.lua').symlink_to('legacy.lua')
            self.assertEqual(notices.header_findings(root, [('A', 'assist_under_test.lua')]), [])

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks are unavailable')
    def test_source_symlink_must_resolve_to_in_repo_source_outside_ignored_areas(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside_temp:
            root = Path(temp)
            outside = Path(outside_temp) / 'outside.lua'
            outside.write_text('-- SPDX-License-Identifier: MIT\nreturn {}\n')
            (root / 'vendor').mkdir()
            (root / 'vendor' / 'library.lua').write_text('-- SPDX-License-Identifier: MIT\nreturn {}\n')
            (root / 'not_source.txt').write_text('not source\n')
            (root / 'directory.lua').mkdir()
            (root / 'dangling.lua').symlink_to('missing.lua')
            (root / 'outside.lua').symlink_to(outside)
            (root / 'vendor.lua').symlink_to('vendor/library.lua')
            (root / 'not_source.lua').symlink_to('not_source.txt')
            (root / 'directory_target.lua').symlink_to('directory.lua')
            self.assertEqual(
                notices.header_findings(root, [
                    ('A', 'dangling.lua'),
                    ('M', 'outside.lua'),
                    ('A', 'vendor.lua'),
                    ('A', 'not_source.lua'),
                    ('A', 'directory_target.lua'),
                ]),
                [
                    'dangling.lua: source symlink is dangling',
                    'outside.lua: source symlink escapes repository root',
                    'vendor.lua: source symlink targets ignored source area',
                    'not_source.lua: source symlink target is not a source file',
                    'directory_target.lua: source symlink target is not a regular file',
                ])


class WippyWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lock = self.root / 'ui/package-lock.json'
        self.lock.parent.mkdir()
        self.name = '@example/widgets'
        self.location = '.wippy/npm/' + self.name
        self.data = {'packages': {self.location: {'version': '1.2.3', 'license': 'MIT'},
            'node_modules/' + self.name: {'link': True, 'resolved': self.location}}}
        self.component = {'name': self.name, 'version': '1.2.3',
            'properties': [{'name': 'cdx:npm:package:path', 'value': self.location}],
            'licenses': [{'license': {'id': 'MIT'}}]}
        self.save()

    def save(self):
        self.lock.write_text(json.dumps(self.data))

    def inspect(self):
        return notices.wippy_workspace_texts(self.component, self.lock, self.root)

    def materialize(self):
        directory = self.lock.parent / self.location
        directory.mkdir(parents=True)
        (directory / 'package.json').write_text(json.dumps({
            'name': self.name, 'version': '1.2.3', 'license': 'MIT'}))
        return directory

    def test_built_artifact_retains_locked_license_in_inventory(self):
        self.materialize()
        (self.root / 'ui/package.json').write_text(json.dumps({'name': '@example/app'}))
        with patch('notices.tracked', return_value=['ui/package.json', 'ui/package-lock.json']), \
             patch('notices.command_json', return_value={'components': [self.component]}), \
             patch('notices.urlopen', side_effect=AssertionError('workspace must not fetch an npm archive')):
            records = notices.collect(self.root, self.root / 'cache')
        row = records[('npm', self.name, '1.2.3')]
        self.assertEqual(row['license'], 'MIT')
        self.assertEqual(row['sources'], {'ui/package-lock.json'})
        rendered = notices.render('# Notices\n', records)
        self.assertIn('@example/widgets@1.2.3', rendered)
        self.assertIn('License: MIT', rendered)


    def test_unbuilt_artifact_requires_materialization_instead_of_omitting_attribution(self):
        with self.assertRaisesRegex(ValueError, 'Materialize Wippy build inputs'):
            self.inspect()

    def test_materialized_attribution_is_preserved(self):
        (self.materialize() / 'LICENSE').write_text('MIT\nCopyright Widget Authors\n')
        self.assertEqual(self.inspect(), ('MIT', {'LICENSE': 'MIT\nCopyright Widget Authors\n'}))

    def test_mismatched_version_and_link_are_rejected(self):
        for field, value in [('version', '9.9.9'), ('license', '')]:
            with self.subTest(field=field):
                original = self.data['packages'][self.location][field]
                self.data['packages'][self.location][field] = value
                self.save()
                with self.assertRaises(ValueError):
                    self.inspect()
                self.data['packages'][self.location][field] = original
        self.data['packages']['node_modules/' + self.name]['resolved'] = '../somewhere'
        self.save()
        with self.assertRaisesRegex(ValueError, 'match its lock'):
            self.inspect()

    def test_sbom_license_and_materialized_license_must_match_lock(self):
        self.component['licenses'] = [{'license': {'id': 'Apache-2.0'}}]
        with self.assertRaisesRegex(ValueError, 'license differs'):
            self.inspect()
        self.component['licenses'] = [{'license': {'id': 'MIT'}}]
        directory = self.materialize()
        (directory / 'package.json').write_text(json.dumps({
            'name': self.name, 'version': '1.2.3', 'license': 'Apache-2.0'}))
        with self.assertRaisesRegex(ValueError, 'differs from its lock'):
            self.inspect()

    def test_unknown_nonarchive_dependency_keeps_existing_failure(self):
        self.component['properties'][0]['value'] = '../outside'
        self.assertIsNone(self.inspect())
        with self.assertRaisesRegex(ValueError, 'no unique locked archive'):
            notices.npm_texts(self.component, self.root)

    def test_symlinked_artifact_and_legal_file_cannot_escape_repository(self):
        with tempfile.TemporaryDirectory() as external:
            directory = self.lock.parent / self.location
            directory.parent.mkdir(parents=True)
            directory.symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'outside the repository'):
                self.inspect()
            directory.unlink()
            directory = self.materialize()
            text = Path(external) / 'LICENSE'
            text.write_text('outside')
            (directory / 'LICENSE').symlink_to(text)
            with self.assertRaisesRegex(ValueError, 'outside the repository'):
                self.inspect()
