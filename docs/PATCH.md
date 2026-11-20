# Technical details

## Source package

| | |
|---|---|
| Official file | `A5G_BY_G23_M03_ST_012_20250707_{L,R}_FotaPackage_*.bin` (the L and R packages are byte-identical, same as on HR+) |
| Size | 1,055,094 bytes |
| SHA-256 | `c90ace5e4c4b3e56c55b87bc21e0f7b1a2f491d0ab7fe0f2295701452f1ff44f` |
| Obtained from | BullSuper's update server: `GET http://43.138.251.38/upgrade?deviceType=A5G_BY_G23_M03_ST&gray=` returns `leftRul` / `rightUrl` |
| Container | Airoha FOTA: LZMA payload plus SHA-256 integrity fields. No signature. |
| Uncompressed payload SHA-256 | `696cd0ec7fcc6ac945e5b1ed0b4bbec128b89e1f3f6be5c27260445425c93ce2` |

## The change

The HR+ patch rewrites a 37-byte block inside a firmware negotiation check. The check only accepts a byte value that iOS 27 no longer sends: iOS 27 sends `0x80`. The patch also accepts `0x80` and removes a debug-log call from that path.

The same function exists in the M03 V012 firmware. It is **16 bytes earlier**: payload offset `0x6b0c0` instead of `0x6b0d0`.

I compared the whole function (from `entry` to `retw.n`, 0x115 bytes) with the HR+ V007 version, instruction by instruction. These are the only differences:

- **Immediates of 7 `l32r` instructions.** These are PC-relative literal-pool loads, and their immediate changes because the code moved. Every one of them still loads the same literal: the log function pointer.
- **5 bytes after an unconditional `j`** (function offsets `0xf7`–`0xfb`). No instruction in the function reaches them.

The negotiation check itself is byte-identical. Inside the 37-byte block, the only difference is the `l32r` of the debug-log call, and the patch replaces that call with `j` and `nop.n` anyway.

```
offset 0x6b0c0 (payload)
original  a86182040192040437983ca79939c851b20405c79b310c0ab1ccff38410c0c818a5de00800
patched   a86182040192040437983ca79939c851b20405562c00b0b064c79b2b3841c600003df03df0
```

After the patch:
- **18 bytes** of the payload differ, all inside `0x6b0d3`–`0x6b0e4`.
- Section layout and text headers are unchanged.
- The package was recompressed and its hashes recalculated. It unpacks back to the exact patched payload.

| | |
|---|---|
| Patched package size | 1,054,532 bytes |
| Patched package SHA-256 | `a6c5fab0d7cadf63cd9b78528a3b016ce3c90fc79caf044ef3d28d21e9eb0508` |

## APK changes vs the HR+ patch app

Only `local.hrpatch.Guard`, one string resource and the bundled assets were changed:

- **Accepted device profiles:** `A5G_BY_G23_M03_ST_005_20241224_L` or `A5G_BY_G23_M03_ST_012_20250707_L`.
- **Expected file length and SHA-256:** set to the patched M03 package.
- **Error message:** when the profile does not match, it now shows the profile the device reported.
- **Bundled files:** `assets/hrpatch/left.bin` and `right.bin` replaced with the patched M03 package.
- **Signing:** rebuilt with apktool 2.10.0 and signed with uber-apk-signer (debug key).

The FOTA transfer code is the original Airoha/BullSuper code and has not been changed.
