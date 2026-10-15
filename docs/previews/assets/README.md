# Original Stock Pixel font

`stock-pixel.ttf` is the local font asset for all preview text, including tables,
navigation and controls. It keeps real selectable, searchable text and supports
normal browser text scaling. No CDN, font download or system install is used.
Lowercase codepoints intentionally use matching uppercase pixel forms.

Original 5×7 glyph outlines are recorded in `pixel-glyphs.json`. These project
assets and their generator are distributed under the repository's root LICENSE;
no third-party font or artwork is included. The generated TTF is a required
preview asset, not a build cache.

Rebuild deterministically with Node's standard library:

```text
node docs/previews/assets/build-pixel-font.cjs
```

The generator verifies the whole-font checksum. Glyph coverage includes ASCII
and the punctuation used in the preview. Missing other scripts/characters may
use the system monospace fallback; production must specify localization coverage
before claiming all-language pixel rendering. Check legibility, user font/spacing
overrides, zoom, contrast and loading in browser verification; a generated font
alone does not certify accessibility. At default sizes body text is 20px and
headings are larger, avoiding tiny pixel text.
