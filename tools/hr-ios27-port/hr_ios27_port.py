#!/usr/bin/env python3
"""
Porta el parche iOS 27 del HR+ V5.3 (Niaktou/hrplus-ios27-patch) a otro
firmware Airoha AB1562AE, p. ej. el de los AirReps V5.3 HR "normal".

NO se conecta a ningún dispositivo y NO flashea nada. Solo:
  1. Valida el paquete FOTA original (hashes SHA-256 de paquete y secciones).
  2. Lo descomprime (LZMA).
  3. Busca la función de validación de negociación EXACTA del HR+, con su
     contexto antes y después. Si no aparece idéntica UNA sola vez, se para.
  4. Sustituye el bloque de 37 bytes (18 cambian) por el del parche HR+.
  5. Recomprime, recalcula los hashes y comprueba la ida y vuelta.

Si el código no coincide byte a byte, no se fuerza nada: hace falta
análisis manual del firmware (Xtensa) y el script lo indica.

Uso:
  python3 hr_ios27_port.py IZQUIERDO.bin DERECHO.bin [--out carpeta]
  python3 hr_ios27_port.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from airoha.container import FirmwareError, Package, read_limited  # noqa: E402

# --- Parche HR+ V007 (docs/PATCH.md de Niaktou/hrplus-ios27-patch) ---------
HRPLUS_OFFSET = 0x6B0D0
ORIGINAL = bytes.fromhex(
    "a86182040192040437983ca79939c851b20405c79b310c0ab1ccff38410c0c81895de00800")
PATCHED = bytes.fromhex(
    "a86182040192040437983ca79939c851b20405562c00b0b064c79b2b3841c600003df03df0")
# Contexto del firmware HR+ alrededor del bloque (función desde 0x6b01c).
CTX_BEFORE = bytes.fromhex(
    "368100ad422aaaa2daffa20afba506eb0c1ec135a94136a9812fa9a9410ca30c0a7d0382"
    "0800d20402920404b20c00620c04520c02f20403c20c03420400808e93803b9380e5930c"
    "0b8074934d0b5d0480b693b951805f931c96806d93fd04dd0380499380fc93f961cd42b9"
    "01c971b1e0ff0c4c81a15de0080070d07460e07450f0740c0ab1dbff0c4c4090749901819"
    "a5de008004871b1d8ff0c4c2a44f20404e20403d20401a20405a9010c0a81925de00800")
CTX_AFTER = bytes.fromhex(
    "a203040c0b0c6cdd02a555eaad422aaaa20a00bd02a0a00425eaff46060000507605060c"
    "0ab1feff0c0c817d5de00800ad02817c5de008000c021df000000090")
HRPLUS_ORIGINAL_PKG_SHA = "1dea0bbd7abe2f5fdaeac962d02ec06f5ca9195300ee2961353269c1adebd8d6"
HRPLUS_PATCHED_PKG_SHA = "e33a563c45a5a7bad6b4d957c8db68ab209e1711ddabbb12943b93132da1a5a2"

assert len(ORIGINAL) == len(PATCHED) == 37
assert sum(a != b for a, b in zip(ORIGINAL, PATCHED)) == 18


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def find_all(hay: bytes, needle: bytes) -> list[int]:
    out, i = [], hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


# Coincidencia "tolerante": en otra build (p. ej. HR normal, perfil M03) la
# función puede estar desplazada y las instrucciones L32R (carga desde la
# tabla de literales, relativas al PC) cambian su inmediato. Se ignoran SOLO
# esos bytes de inmediato y los 5 bytes inalcanzables tras el J (0xf7-0xfb).
_REF = CTX_BEFORE + ORIGINAL + CTX_AFTER
_L32R_AT = [0x74, 0x8F, 0xAE, 0xD3, 0xFE, 0x103, 0x10B]  # offsets de L32R en _REF
_IGNORE = {o + k for o in _L32R_AT for k in (1, 2)} | set(range(0xF7, 0xFC))
_CHECK_END = 0x115  # hasta retw.n inclusive
assert all(_REF[o] & 0xF == 1 for o in _L32R_AT)


def find_tolerant(payload: bytes) -> list[int]:
    hits = []
    for start in find_all(payload, CTX_BEFORE[:16]):
        win = payload[start:start + _CHECK_END]
        if len(win) < _CHECK_END:
            continue
        ok = all(win[i] == _REF[i] for i in range(_CHECK_END) if i not in _IGNORE)
        ok = ok and all(win[o] & 0xF == 1 for o in _L32R_AT)
        if ok:
            hits.append(start + len(CTX_BEFORE))
    return hits


def analyse(payload: bytes) -> dict:
    full_orig = CTX_BEFORE + ORIGINAL + CTX_AFTER
    full_patched = CTX_BEFORE + PATCHED + CTX_AFTER
    r = {
        "bloque_original_en": [hex(x) for x in find_all(payload, ORIGINAL)],
        "bloque_parcheado_en": [hex(x) for x in find_all(payload, PATCHED)],
        "funcion_completa_original_en": [hex(x + len(CTX_BEFORE)) for x in find_all(payload, full_orig)],
        "funcion_completa_parcheada_en": [hex(x + len(CTX_BEFORE)) for x in find_all(payload, full_patched)],
        # Pistas para análisis manual si no hay coincidencia exacta
        "prefijo_16B_en": [hex(x) for x in find_all(payload, ORIGINAL[:16])],
        "inicio_funcion_16B_en": [hex(x) for x in find_all(payload, CTX_BEFORE[:16])],
    }
    if r["funcion_completa_parcheada_en"]:
        r["veredicto"] = "YA_PARCHEADO"
    elif len(r["funcion_completa_original_en"]) == 1:
        r["veredicto"] = "PORTABLE"
    elif len(r["funcion_completa_original_en"]) > 1:
        r["veredicto"] = "AMBIGUO"
    else:
        tol = find_tolerant(payload)
        r["funcion_tolerante_l32r_en"] = [hex(x) for x in tol]
        if len(tol) == 1:
            r["veredicto"] = "PORTABLE_L32R"
            r["funcion_completa_original_en"] = [hex(tol[0])]
        else:
            r["veredicto"] = "AMBIGUO" if tol else "NO_COINCIDE"
    return r


def port_one(path: Path) -> tuple[bytes | None, dict]:
    data = read_limited(path)
    pkg = Package(data, path.name)
    info = pkg.info()
    payload = pkg.unpack()
    rep = {
        "archivo": str(path), "sha256": sha(data), "tamano": len(data),
        "compresion": info["compression"], "cabeceras_texto": info["text_header_values"],
        "secciones": [(s["payload_offset"], s["length"], hex(s["destination"])) for s in info["sections"]],
        "payload_sha256": sha(payload),
    }
    if rep["sha256"] == HRPLUS_ORIGINAL_PKG_SHA:
        rep["nota"] = "Es exactamente el firmware HR+ V007 original: usa directamente el parche publicado."
    rep.update(analyse(payload))
    if rep["veredicto"] not in ("PORTABLE", "PORTABLE_L32R"):
        return None, rep
    off = int(rep["funcion_completa_original_en"][0], 16)
    # En el bloque solo puede diferir el inmediato del L32R del log (bytes
    # 0x20-0x21 del bloque), que el parche sustituye por J + NOPs.
    blk = payload[off:off + 37]
    assert all(blk[i] == ORIGINAL[i] for i in range(37) if i not in (0x20, 0x21)), "bloque inesperado"
    if off != HRPLUS_OFFSET:
        rep["aviso"] = (f"La función está en {hex(off)} en vez de {hex(HRPLUS_OFFSET)}. El bloque y su contexto "
                        "son idénticos y el reemplazo no añade llamadas ni l32r, pero revisa con más cuidado.")
    new = bytearray(payload)
    new[off:off + 37] = PATCHED
    new = bytes(new)
    diff = [i for i in range(len(payload)) if payload[i] != new[i]]
    assert 1 <= len(diff) <= 37 and min(diff) >= off and max(diff) < off + 37
    rebuilt = pkg.rebuild(new)
    check = Package(rebuilt, "check").unpack()
    assert check == new
    rep.update(parche_offset=hex(off), bytes_cambiados=len(diff),
               salida_sha256=sha(rebuilt), salida_tamano=len(rebuilt))
    return rebuilt, rep


def run(left: Path, right: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    reports, ok = {}, True
    outputs = {}
    for side, p in (("left", left), ("right", right)):
        try:
            rebuilt, rep = port_one(p)
        except FirmwareError as e:
            rebuilt, rep = None, {"archivo": str(p), "error": str(e), "veredicto": "NO_VALIDO"}
        reports[side] = rep
        if rebuilt is None:
            ok = False
        else:
            outputs[side] = rebuilt
    if ok:
        sums = []
        for side, blob in outputs.items():
            name = f"{Path(reports[side]['archivo']).stem}_iOS27patch_{side}.bin"
            target = out / name
            if target.exists():
                print(f"No sobrescribo {target}; usa otra carpeta --out", file=sys.stderr)
                return 3
            target.write_bytes(blob)
            sums.append(f"{sha(blob)}  {name}")
        (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    (out / "informe.json").write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n")
    for side, rep in reports.items():
        print(f"[{side}] {rep.get('veredicto')}  {rep.get('error', '')}{rep.get('nota', '')}")
        if rep.get("aviso"):
            print("   AVISO:", rep["aviso"])
    if ok:
        print(f"\nOK. Paquetes parcheados en {out}/ (ver SHA256SUMS.txt e informe.json).")
        print("Recuerda: probado solo offline. Flashear sigue siendo bajo tu riesgo.")
        return 0
    print(f"\nNo se ha generado firmware. Detalles en {out}/informe.json")
    return 2


def selftest() -> int:
    """Reconstruye un 'original' a partir del HR+ parcheado y comprueba que se
    vuelve a parchear byte a byte igual."""
    src = Path(__file__).resolve().parent / "selftest" / "HRplus_V007_iOS27_candidate_v1_left.bin"
    if not src.exists():
        print(f"Para el selftest, copia el .bin parcheado del HR+ en {src}")
        return 1
    data = src.read_bytes()
    assert sha(data) == HRPLUS_PATCHED_PKG_SHA, "no es el paquete HR+ parcheado publicado"
    pkg = Package(data, src.name)
    patched_payload = pkg.unpack()
    assert analyse(patched_payload)["veredicto"] == "YA_PARCHEADO"
    orig = bytearray(patched_payload)
    orig[HRPLUS_OFFSET:HRPLUS_OFFSET + 37] = ORIGINAL
    fake_original = pkg.rebuild(bytes(orig))
    tmp = src.parent / "_fake_original.bin"
    tmp.write_bytes(fake_original)
    try:
        rebuilt, rep = port_one(tmp)
    finally:
        tmp.unlink()
    assert rep["veredicto"] == "PORTABLE" and rebuilt is not None
    assert Package(rebuilt, "x").unpack() == patched_payload
    print("Selftest OK: original reconstruido -> PORTABLE -> payload idéntico al parche HR+ publicado.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("left", nargs="?", type=Path)
    ap.add_argument("right", nargs="?", type=Path)
    ap.add_argument("--out", type=Path, default=Path("salida"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.left and a.right):
        ap.error("indica los .bin izquierdo y derecho originales")
    return run(a.left, a.right, a.out)


if __name__ == "__main__":
    sys.exit(main())
