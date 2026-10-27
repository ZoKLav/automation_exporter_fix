# Automation fixture opacity: experimental fix

The lead developer of the Automation car tycoon game is a fucking idiot and I hate him. He refuses to fix this longstanding exporter bug, so I fixed it myself.

This package contains an experimental patch of the 64-bit exporter.

The patched DLL is unsigned: editing it invalidates its publisher signature, so the obsolete certificate was removed and its PE checksum recalculated. If Automation rejects unsigned plugins, restore the original DLL; this package does not bypass a signature check.

Restore your backed-up DLL to undo the exporter change. Restore your original vehicle ZIP to undo the car change. The x86 DLL and the `.lib`/`.exp` files were not changed and are not needed to install this x64 candidate.

## Recovered control flow and patch scope

Disassembly of the x64 DLL shows that an incoming material flag (bit 3 at source offset 0x204) and a valid shared stamp can suppress loading the individual opacity texture. The opacity writer can then select the stamp instead of the individual map.

The candidate changes two branches:

- RVA 0x565A8, file offset 0x559A8: `75 32` becomes `90 90`. Continue loading the individual opacity texture even when the shared stamp is available.
- RVA 0x5386E, file offset 0x52C6E: `0F 84 37 06 00 00` becomes `90 E9 37 06 00 00`. When an individual opacity pointer exists, take the individual-map writer path regardless of the stamp selection condition.

Materials without an individual opacity pointer retain the existing stamp-selection path. The patch preserves section layout, imports, exports, instruction lengths, and branch destination addresses. Four instruction bytes change, plus the checksum and certificate metadata; the trailing certificate is removed.

This is a precedence workaround. It does not combine intrinsic opacity with a projected stamp. A fixture that intentionally needs both masks could lose its stamped cutout, which is why this broader exporter patch needs regression testing. The car-only correction affects only the two confirmed grille materials.

`patch_plugin.py` reproduces the DLL patch, checks the exact original hash, and refuses to overwrite an output file.

## Bugs

This will throw a sound export warning, you can ignore it, it only happens because the DLL is unsigned.

## Virustotal

https://www.virustotal.com/gui/file/adae820bb1fe66c2de9ebdcaf023f41794f47e6fa4b6de88419cdb475dabc5d0

## DLL hashes

Original SHA-256: `5f52eb582110ab68db835783cabac30cd0728c5b561bbc3beb2dcafbcbe38721`

Patched SHA-256: `adae820bb1fe66c2de9ebdcaf023f41794f47e6fa4b6de88419cdb475dabc5d0`
