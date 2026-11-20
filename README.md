# AirReps V5.3 HR (non-plus, M03) — unofficial iOS 27 patch

Port of [Niaktou/hrplus-ios27-patch](https://github.com/Niaktou/hrplus-ios27-patch) (HR+ V007) to the **regular V5.3 HR** firmware profile `A5G_BY_G23_M03_ST`.

After iOS 27, these earbuds stopped working with the iPhone. With this patch, pairing and music playback in both earbuds work again.

> **Experimental. Tested on ONE pair.** Flashing firmware can brick your earbuds and recovery is not guaranteed. Use at your own risk.

## Tested

| | |
|---|---|
| Earbuds | AirReps V5.3 HR (non-plus) |
| Profile before update | `A5G_BY_G23_M03_ST_005_20241224_L` |
| Firmware installed | Official `A5G_BY_G23_M03_ST_012_20250707` + iOS 27 patch |
| Phone | iPhone on iOS 27 — pairing and music OK on both earbuds |
| Flashed from | Android, using the included APK |

The APK **only** accepts these two device profiles:
- `A5G_BY_G23_M03_ST_005_20241224_L`
- `A5G_BY_G23_M03_ST_012_20250707_L`

It refuses every other device and shows the profile the device reported. If yours is HR+ (`M05`), use the original HR+ patch instead.

## Contents

```
apk/HR-M03-iOS27-patch.apk     Modified HR+ patch app (BullSuper-based) with the M03 files bundled
firmware/HR_M03_V012_iOS27_left.bin
firmware/HR_M03_V012_iOS27_right.bin
docs/PATCH.md                  Technical details
tools/hr-ios27-port/           Script that reproduces the patch from the official package
SHA256SUMS.txt
```

## Install (Android)

1. Uninstall the HR+ patch app if you have it, because both apps use the same package name. BullSuper can stay installed.
2. Install `HR-M03-iOS27-patch.apk`. It is signed with a debug key, so Android will warn you about an unknown source.
3. Connect your earbuds in the app and tap **Verify patch**. This does not flash anything: it only checks the device profile and the bundled files.
4. If it says *"HR M03 (V005/V012) confirmed"*, take **both** earbuds out of the case. Make sure they are charged (more than 50% recommended), then tap **Install patch**.
5. Keep the app open until both earbuds restart. Then pair them with your iPhone.

Do not update through BullSuper afterwards: an update overwrites the patch. The app still shows **V12**.

## Verify it yourself

The two `.bin` files are the official vendor package with **18 bytes changed**. You can reproduce them from the official files:

```
# Official package from http://43.138.251.38/upgrade?deviceType=A5G_BY_G23_M03_ST&gray=
python3 tools/hr-ios27-port/hr_ios27_port.py <official_L.bin> <official_R.bin> --out out
# out/*.bin must match SHA256SUMS.txt
```

## Credits

- Original HR+ patch and app: [Niaktou/hrplus-ios27-patch](https://github.com/Niaktou/hrplus-ios27-patch)
- Airoha FOTA container tooling: [MattiaIppoliti/pairbridge](https://github.com/MattiaIppoliti/pairbridge) (MIT)
