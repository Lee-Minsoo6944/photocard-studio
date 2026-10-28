"""PNG/JPEG 파일에 EXIF·GPS·XMP 등 메타데이터가 있는지 검사합니다 (외부 라이브러리 없음).

사용법:  python check_meta.py 완성1.png 완성2.jpg 완성3.png
"""
import struct
import sys


def png_chunks(data):
    pos, found = 8, []
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        ctype = ctype.decode("latin-1")
        body = data[pos + 8:pos + 8 + length]
        if ctype in ("eXIf", "tEXt", "zTXt", "iTXt", "tIME"):
            found.append(ctype + (" (GPS 포함 가능)" if ctype == "eXIf" else ""))
        if ctype == "iTXt" and b"XML:com.adobe.xmp" in body[:40]:
            found.append("XMP")
        pos += 12 + length
        if ctype == "IEND":
            break
    return found


def jpeg_segments(data):
    pos, found = 2, []
    while pos + 4 <= len(data) and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker in (0xD9, 0xDA):  # 끝 / 이미지 본문 시작
            break
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        body = data[pos + 4:pos + 2 + length]
        if marker == 0xE1 and body.startswith(b"Exif"):
            found.append("EXIF" + (" + GPS" if b"\x88\x25" in body or b"\x25\x88" in body else ""))
        elif marker == 0xE1 and b"adobe" in body[:40]:
            found.append("XMP")
        elif marker == 0xED:
            found.append("IPTC/Photoshop")
        pos += 2 + length
    return found


def main(paths):
    if not paths:
        print(__doc__)
        return 1
    bad = 0
    for p in paths:
        with open(p, "rb") as f:
            data = f.read()
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            kind, found = "PNG", png_chunks(data)
        elif data[:3] == b"\xff\xd8\xff":
            kind, found = "JPEG", jpeg_segments(data)
        else:
            print(f"{p}: PNG/JPEG가 아님")
            bad += 1
            continue
        gps = any("GPS" in x for x in found)
        bad += bool(found)
        print(f"{p}: {kind}, 메타데이터 {len(found)}건 {found if found else ''} / 위치정보(GPS) {'있음' if gps else '0건'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
