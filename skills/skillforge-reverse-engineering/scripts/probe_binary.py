#!/usr/bin/env python3
"""只读识别文件及核验 PE 地址；不装载或执行样本。"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import struct
import stat
import sys


def hex_value(value):
    return f'0x{value:X}'


def read_at(stream, offset, length, file_size):
    if offset < 0 or length < 0 or offset + length > file_size:
        raise ValueError('truncated or invalid header range')
    stream.seek(offset)
    value = stream.read(length)
    if len(value) != length:
        raise ValueError('file changed or header is truncated')
    return value


def parse_pe(stream, file_size):
    dos = read_at(stream, 0, 64, file_size)
    offset = struct.unpack_from('<I', dos, 0x3C)[0]
    if offset < 64:
        raise ValueError('PE header overlaps DOS header')
    header = read_at(stream, offset, 24, file_size)
    if header[:4] != b'PE\0\0':
        raise ValueError('MZ input has no supported PE signature')
    machine, count = struct.unpack_from('<HH', header, 4)
    optional_size = struct.unpack_from('<H', header, 20)[0]
    if optional_size < 64:
        raise ValueError('optional header too short for supported PE fields')
    optional = read_at(stream, offset + 24, optional_size, file_size)
    magic = struct.unpack_from('<H', optional)[0]
    if magic == 0x20B:
        image_base = struct.unpack_from('<Q', optional, 24)[0]
        kind = 'PE32+'
    elif magic == 0x10B:
        image_base = struct.unpack_from('<I', optional, 28)[0]
        kind = 'PE32'
    else:
        raise ValueError('unsupported PE optional-header magic')
    headers_size = struct.unpack_from('<I', optional, 60)[0]
    section_table_offset = offset + 24 + optional_size
    if not section_table_offset + count * 40 <= headers_size <= file_size:
        raise ValueError('SizeOfHeaders does not cover the header tables within the file')
    table = read_at(stream, section_table_offset, count * 40, file_size)
    sections = []
    for index in range(count):
        row = table[index * 40:(index + 1) * 40]
        virtual_size, virtual_address, raw_size, raw_pointer = struct.unpack_from('<IIII', row, 8)
        sections.append({
            'name': row[:8].split(b'\0', 1)[0].decode('ascii', errors='replace'),
            'virtual_size': virtual_size, 'rva': virtual_address,
            'raw_size': raw_size, 'file_offset': raw_pointer,
        })
    return kind, machine, image_base, headers_size, sections


def map_rva(rva, loaded_base, file_size, headers_size, sections):
    result = {'rva': hex_value(rva), 'file_offset': None, 'runtime_va': None, 'status': 'unmapped'}
    if loaded_base is not None:
        result['runtime_va'] = hex_value(loaded_base + rva)
    matches = [section for section in sections
               if section['rva'] <= rva < section['rva'] + max(section['virtual_size'], section['raw_size'])]
    # 重叠布局不能静默采用第一节，否则可能给出错误补丁位置。
    if len(matches) + int(rva < headers_size) > 1:
        result['status'] = 'ambiguous_sections'
        return result
    if rva < headers_size:
        offset = rva
    elif matches:
        section = matches[0]
        result['section'] = section['name']
        delta = rva - section['rva']
        if delta >= section['raw_size']:
            result['status'] = 'virtual_only'
            return result
        offset = section['file_offset'] + delta
    else:
        return result
    if offset >= file_size:
        result['status'] = 'outside_file'
    else:
        result['status'] = 'mapped'
        result['file_offset'] = hex_value(offset)
    return result


@contextmanager
def regular_input(path):
    # Reject stable devices/FIFOs before open. Recheck the actual descriptor too.
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('input must be a regular file; devices/FIFOs are unsupported')
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError('opened input must be a regular file')
        stream = os.fdopen(descriptor, 'rb')
        descriptor = None  # stream now owns it, including on later exceptions.
        with stream:
            yield stream
    finally:
        if descriptor is not None:
            os.close(descriptor)


def inspect_file(path, *, rva=None, loaded_base=None):
    if rva is not None and not 0 <= rva <= 0xFFFFFFFF:
        raise ValueError('RVA must fit an unsigned 32-bit integer')
    if loaded_base is not None and (rva is None or not 0 <= loaded_base <= 0xFFFFFFFFFFFFFFFF - rva):
        raise ValueError('loaded base requires an RVA and their sum must fit 64 bits')
    path = Path(path)
    with regular_input(path) as stream:
        before = os.fstat(stream.fileno())
        digest = hashlib.sha256()
        remaining = before.st_size
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError('file shrank while hashing; repeat on a stable copy')
            digest.update(chunk)
            remaining -= len(chunk)
        if stream.read(1):
            raise ValueError('file grew while hashing; repeat on a stable copy')
        stream.seek(0)
        magic = stream.read(8)
        result = {'size': before.st_size, 'sha256': digest.hexdigest().upper(), 'format': 'unknown', 'mapping': None}
        if magic.startswith(b'MZ'):
            kind, machine, image_base, headers_size, sections = parse_pe(stream, before.st_size)
            result.update(format=kind, machine=hex_value(machine), preferred_image_base=hex_value(image_base), sections=sections)
            if rva is not None:
                result['mapping'] = map_rva(rva, loaded_base, before.st_size, headers_size, sections)
        elif magic.startswith(b'\x7fELF'):
            result['format'] = 'ELF'
        elif magic[:4] in (b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe'):
            result['format'] = 'Mach-O'
        elif magic[:4] == b'\xca\xfe\xba\xbe':
            # Java class 与 universal Mach-O 共享 magic，单凭头四字节不能定性。
            result['format'] = 'Java-class-or-Mach-O-fat'
        elif magic[:4] == b'\x00asm':
            result['format'] = 'WASM'
        if rva is not None and result['format'] != 'unknown' and result['mapping'] is None:
            result['mapping'] = {'status': 'unsupported_format', 'file_offset': None}
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('file changed while being inspected; repeat on a stable copy')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('--rva', type=lambda value: int(value, 0))
    parser.add_argument('--loaded-base', type=lambda value: int(value, 0))
    args = parser.parse_args(argv)
    try:
        result = inspect_file(args.sample, rva=args.rva, loaded_base=args.loaded_base)
    except (OSError, ValueError, struct.error) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
