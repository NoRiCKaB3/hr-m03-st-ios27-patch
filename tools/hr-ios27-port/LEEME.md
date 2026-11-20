# Port del parche iOS 27 (HR+ V5.3) a AirReps V5.3 HR normal

Este script aplica al firmware de tus HR el mismo cambio de 18 bytes que el parche publicado para el HR+ ([Niaktou/hrplus-ios27-patch](https://github.com/Niaktou/hrplus-ios27-patch)). Así pasan a aceptar también el valor `0x80` que envía iOS 27 en la negociación.

Solo modifica el firmware si la función de validación coincide **byte a byte** con la del HR+, incluyendo su contexto. Si no coincide, se para y no genera nada.

No se conecta a los auriculares ni flashea nada.

## Paso 0: comprueba si ya te vale el parche del HR+

Instala `HRplus-iOS27-English.apk` en un Android, conecta los auriculares y pulsa solo **Verify patch** (no flashea). Si tus HR muestran el perfil `A5G_BY_G23_M05_ST_007_20260122_L`, tienen el mismo firmware que el HR+ y puedes usar el parche publicado tal cual. Si el perfil es otro, sigue con este script.

## Paso 1: consigue el firmware original de tus HR

Necesitas los dos paquetes FOTA (`left` y `right`) **de tu perfil exacto**. Por ejemplo, el que ofrece la app BullSuper como actualización, o el que haya compartido alguien de r/AirReps o del Discord con el mismo perfil.

## Paso 2: ejecuta el script (requiere Python 3.9 o superior, sin dependencias)

```
python3 hr_ios27_port.py left.bin right.bin --out salida
```

Posibles resultados:
- `PORTABLE`: genera `salida/*_iOS27patch_left.bin` y `*_right.bin`, junto con `SHA256SUMS.txt` e `informe.json`.
- `PORTABLE_L32R`: la función es la misma, pero está desplazada y algunas instrucciones `l32r` (cargas desde la tabla de constantes) tienen otro inmediato. Esto es normal entre builds distintas, y es lo que ocurre con el perfil HR `A5G_BY_G23_M03_ST_012`. El script parchea igual.
- `YA_PARCHEADO`: el firmware ya lleva el parche; no hay que hacer nada.
- `NO_COINCIDE` o `AMBIGUO`: tu firmware tiene otra versión del código. No se genera nada, y `informe.json` incluye pistas (`prefijo_16B_en`, `inicio_funcion_16B_en`) para un análisis manual.
- `NO_VALIDO`: el archivo no es un paquete Airoha válido, está cifrado o está corrupto.

Para comprobar que el script reproduce el parche publicado, copia `HRplus_V007_iOS27_candidate_v1_left.bin` del repositorio del HR+ en `selftest/` y ejecuta `python3 hr_ios27_port.py --selftest`.

## Paso 3: flashear (bajo tu responsabilidad)

Usa un Android con una app FOTA Airoha que permita elegir los binarios izquierdo y derecho. Por ejemplo, la app de utilidades del SDK de Airoha que usa [PairBridge](https://github.com/MattiaIppoliti/pairbridge) (TWS FLASH → FOTA bin → Left/Right).

- Saca los dos auriculares del estuche, con más del 20 % de batería, y lánzalo **una sola vez**.
- Espera al mensaje de éxito y al reinicio.
- Después, empareja con el iPhone y prueba los dos lados.

## Limitaciones

- El parche original solo se ha probado en un par de HR+ (emparejamiento y música). Este port solo se ha probado offline.
- Un firmware incorrecto o un flasheo interrumpido puede inutilizar los auriculares.
- Una actualización oficial posterior sobrescribirá el parche.

El código de `airoha/` es de PairBridge (licencia MIT, ver `airoha/LICENSE-PairBridge`).
