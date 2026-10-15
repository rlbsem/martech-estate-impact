# Groundbreakers engineering diagram theme

Technical diagrams follow the Groundbreakers Digital dark-indigo, lavender and off-white palette. The generator in `src/estate_impact/reporting/mermaid.py` owns these styles; regenerate the published Markdown and Mermaid examples with `python scripts/demo.py`, not manual colour edits.

| Role | Hex | Use |
| --- | --- | --- |
| Midnight canvas | `#10101D` | Diagram background |
| Deep charcoal indigo | `#181825` | Containers |
| Graphite | `#2A2A3D` | System nodes |
| Elevated slate | `#2E2E45` | Status nodes |
| Muted periwinkle | `#7C7CAF` | Neutral borders |
| Lavender | `#B8B8FF` | Control and proposed-state accent |
| Off-white | `#F0F0FF` | Labels |
| Teal | `#81C5B0` | Supported |
| Amber | `#E3BC7F` | Unknown |
| Rose | `#D98EA3` | Unsupported and removed |

Typography: **JetBrains Mono** for architectural titles/technical IDs, **IBM Plex Sans** for readable system labels and descriptions; fallback fonts are acceptable. Preserve labelled states and dashed proposed edges so meaning never relies on colour alone.

These are synthetic estate diagrams, not live deployment evidence. GitHub's Mermaid renderer may apply surrounding page-theme defaults; explicit node fills, borders and text colours maintain legibility.
