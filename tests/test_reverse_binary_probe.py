"""用合成 PE 验证地址换算及损坏文件处理，不运行样本。"""

import hashlib
import json
import os
import subprocess
import sys
from unittest.mock import patch
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/skillforge-reverse-engineering/scripts/probe_binary.py'


def fixture():
    data = bytearray(0x600)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 0x3C, 0x80)
    data[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<HHIIIHH', data, 0x84, 0x8664, 1, 0, 0, 0, 0xF0, 0x22)
    struct.pack_into('<H', data, 0x98, 0x20B)
    struct.pack_into('<Q', data, 0x98 + 24, 0x140000000)
    struct.pack_into('<I', data, 0x98 + 60, 0x400)
    section = 0x98 + 0xF0
    data[section:section + 8] = b'.data\0\0\0'
    struct.pack_into('<IIII', data, section + 8, 0x300, 0x2000, 0x200, 0x400)
    return data


class BinaryProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('binary_probe', SCRIPT)
        cls.probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.probe)

    def inspect(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.bin'
            path.write_bytes(data)
            result = self.probe.inspect_file(path, **kwargs)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(result['sha256'], hashlib.sha256(data).hexdigest().upper())
            return result

    def assert_special_refused(self, path):
        try:
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path)],
                                    capture_output=True, text=True, timeout=2)
        except subprocess.TimeoutExpired:
            self.fail("special-file probe blocked or read indefinitely")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("regular file", json.loads(result.stderr)["error"])
        self.assertEqual(result.stdout, "")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unavailable")
    def test_fifo_refused_without_writer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input"
            os.mkfifo(path)
            self.assert_special_refused(path)

    @unittest.skipUnless(Path("/dev/zero").exists(), "zero device unavailable")
    def test_device_refused_without_unbounded_hash(self):
        self.assert_special_refused(Path("/dev/zero"))

    @unittest.skipUnless(Path("/dev/zero").exists(), "zero device unavailable")
    def test_opened_descriptor_rechecked_and_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input"
            path.write_bytes(b"abc")
            descriptor = os.open("/dev/zero", os.O_RDONLY)
            with patch.object(self.probe.os, "open", return_value=descriptor):
                with self.assertRaisesRegex(ValueError, "opened input must be a regular file"):
                    self.probe.inspect_file(path)
            with self.assertRaises(OSError): os.fstat(descriptor)

    def test_growth_during_hash_is_rejected(self):
        real_sha = hashlib.sha256
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input"
            path.write_bytes(b"abc")
            class GrowingDigest:
                def __init__(self): self.digest = real_sha()
                def update(self, data):
                    self.digest.update(data)
                    with path.open("ab") as stream: stream.write(b"growing")
                def hexdigest(self): return self.digest.hexdigest()
            with patch.object(self.probe.hashlib, "sha256", GrowingDigest):
                with self.assertRaisesRegex(ValueError, "grew while hashing"):
                    self.probe.inspect_file(path)

    def test_regular_cli_keeps_hash_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input"
            path.write_bytes(b"abc")
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(path)],
                                    capture_output=True, text=True, timeout=2)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["sha256"], hashlib.sha256(b"abc").hexdigest().upper())

    def test_raw_offset_is_distinct_from_rva_and_va(self):
        result = self.inspect(fixture(), rva=0x2080, loaded_base=0x7FF600000000)
        self.assertEqual(result['format'], 'PE32+')
        self.assertEqual(result['mapping']['file_offset'], '0x480')
        self.assertEqual(result['mapping']['runtime_va'], '0x7FF600002080')

    def test_virtual_tail_has_no_patchable_file_bytes(self):
        result = self.inspect(fixture(), rva=0x2250)
        self.assertIsNone(result['mapping']['file_offset'])
        self.assertIn('virtual_only', result['mapping']['status'])

    def test_headers_can_be_mapped(self):
        result = self.inspect(fixture(), rva=0x100)
        self.assertEqual(result['mapping']['file_offset'], '0x100')

    def test_overlapping_sections_are_not_silently_resolved(self):
        data = fixture()
        struct.pack_into('<H', data, 0x86, 2)
        section = 0x98 + 0xF0
        data[section + 40:section + 80] = data[section:section + 40]
        result = self.inspect(data, rva=0x2080)
        self.assertIsNone(result['mapping']['file_offset'])
        self.assertEqual(result['mapping']['status'], 'ambiguous_sections')

    def test_truncated_pe_fails_explicitly(self):
        with self.assertRaises(ValueError):
            self.inspect(fixture()[:0x150])

    def test_truncated_section_data_is_not_patchable(self):
        result = self.inspect(fixture()[:0x450], rva=0x2080)
        self.assertEqual(result['mapping']['status'], 'outside_file')
        self.assertIsNone(result['mapping']['file_offset'])

    def test_not_mz_or_filename_based(self):
        result = self.inspect(b'not an executable')
        self.assertEqual(result['format'], 'unknown')
        self.assertIsNone(result['mapping'])

    def test_elf_is_identification_only(self):
        result = self.inspect(b'\x7fELF\x02\x01' + bytes(64), rva=0x2080)
        self.assertEqual(result['format'], 'ELF')
        self.assertEqual(result['mapping']['status'], 'unsupported_format')

    def test_negative_address_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(fixture(), rva=-1)

    def test_pe32_base_is_read_at_its_own_offset(self):
        data = fixture()
        struct.pack_into('<H', data, 0x98, 0x10B)
        struct.pack_into('<I', data, 0x98 + 28, 0x400000)
        result = self.inspect(data, rva=0x2080)
        self.assertEqual(result['format'], 'PE32')
        self.assertEqual(result['preferred_image_base'], '0x400000')
        self.assertEqual(result['mapping']['file_offset'], '0x480')

    def test_shared_magic_is_not_assumed_to_be_java(self):
        result = self.inspect(b'\xca\xfe\xba\xbe' + bytes(16))
        self.assertEqual(result['format'], 'Java-class-or-Mach-O-fat')

    def test_runtime_address_overflow_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(fixture(), rva=0x2080, loaded_base=0xFFFFFFFFFFFFFFFF)

    def test_base_without_rva_is_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect(fixture(), loaded_base=0x400000)

    def test_header_size_cannot_exclude_section_table(self):
        data = fixture()
        struct.pack_into('<I', data, 0x98 + 60, 0x40)
        with self.assertRaises(ValueError):
            self.inspect(data, rva=0x10)

    def test_header_size_cannot_exceed_file(self):
        data = fixture()
        struct.pack_into('<I', data, 0x98 + 60, 0x800)
        with self.assertRaises(ValueError):
            self.inspect(data, rva=0x100)


if __name__ == '__main__':
    unittest.main()
