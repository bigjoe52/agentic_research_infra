# Data Boundary

Data are not committed by default. Document each source, permitted use, temporal
semantics, known limitations, and retention constraints before relying on it.

- `raw/`: immutable source captures when preservation is justified.
- `derived/`: reproducible transformations.
- `artifacts/`: generated results and manifests.

Directory names and checksums do not establish semantic validity or access
authority. Use `.gitkeep` only to preserve this lightweight structure.

