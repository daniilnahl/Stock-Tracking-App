/* Build original monochrome pixel glyphs as a real text TrueType font.
 * Node standard library only; no font package, downloads or system install.
 * Source outlines: pixel-glyphs.json. Units: 100 per pixel; 600 advance.
 */
const fs = require('node:fs');
const path = require('node:path');
const glyphSource = JSON.parse(fs.readFileSync(path.join(__dirname, 'pixel-glyphs.json'), 'utf8'));
const u16 = value => { const b = Buffer.alloc(2); b.writeUInt16BE(value); return b; };
const i16 = value => { const b = Buffer.alloc(2); b.writeInt16BE(value); return b; };
const u32 = value => { const b = Buffer.alloc(4); b.writeUInt32BE(value >>> 0); return b; };
const join = (...parts) => Buffer.concat(parts.flat());
const padded = b => join(b, Buffer.alloc((4 - b.length % 4) % 4));
const chars = Object.keys(glyphSource).sort((a, b) => a.codePointAt(0) - b.codePointAt(0));
const entries = [['.notdef', glyphSource['?']], ...chars.map(c => [c, glyphSource[c]])];
let maxPoints = 0, maxContours = 0;
function outline(pattern) {
  const pixels = [];
  const rows = pattern.split('/');
  if (rows.length !== 7 || rows.some(row => !/^[01]{5}$/.test(row))) throw Error('Invalid glyph');
  rows.forEach((row, y) => [...row].forEach((bit, x) => {
    if (bit === '1') pixels.push([x * 100, (6 - y) * 100]);
  }));
  if (!pixels.length) return Buffer.alloc(0);
  const points = pixels.flatMap(([x, y]) => [[x,y],[x,y+100],[x+100,y+100],[x+100,y]]);
  maxPoints = Math.max(maxPoints, points.length);
  maxContours = Math.max(maxContours, pixels.length);
  let previousX = 0, previousY = 0;
  const dx = [], dy = [];
  for (const [x, y] of points) {
    dx.push(i16(x - previousX)); dy.push(i16(y - previousY));
    previousX = x; previousY = y;
  }
  return padded(join(i16(pixels.length), i16(0), i16(0), i16(500), i16(700),
    pixels.map((_, index) => u16(index * 4 + 3)), u16(0),
    Buffer.alloc(points.length, 1), dx, dy));
}
const outlines = entries.map(([, pattern]) => outline(pattern));
let cursor = 0;
const offsets = outlines.map(outline => { const start = cursor; cursor += outline.length; return u32(start); });
const tables = {};
tables.glyf = join(outlines);
tables.loca = join(offsets, u32(cursor));
tables.hmtx = join(entries.map(() => join(u16(600), i16(0))));
tables.head = join(u32(0x00010000), u32(0x00010000), u32(0), u32(0x5f0f3cf5),
  u16(3), u16(1000), Buffer.alloc(16), i16(0), i16(0), i16(500), i16(700),
  u16(0), u16(7), i16(2), i16(1), i16(0));
tables.hhea = join(u32(0x00010000), i16(800), i16(-200), i16(0), u16(600),
  i16(0), i16(100), i16(500), i16(1), i16(0), i16(0), Buffer.alloc(8),
  i16(0), u16(entries.length));
tables.maxp = join(u32(0x00010000), u16(entries.length), u16(maxPoints), u16(maxContours),
  u16(0), u16(0), u16(1), Buffer.alloc(16));
// One format-4 segment per supported BMP character; sentinel maps to .notdef.
const codes = chars.map(c => c.codePointAt(0));
const segments = codes.length + 1;
const power = 2 ** Math.floor(Math.log2(segments));
const cmap4 = join(u16(4), u16(16 + segments * 8), u16(0), u16(segments * 2),
  u16(power * 2), u16(Math.log2(power)), u16(segments * 2 - power * 2),
  codes.map(u16), u16(65535), u16(0), codes.map(u16), u16(65535),
  codes.map((code, index) => u16((index + 1 - code) & 65535)), u16(1),
  Buffer.alloc(segments * 2));
tables.cmap = join(u16(0), u16(1), u16(3), u16(1), u32(12), cmap4);
const names = [[1,'Stock Pixel'],[2,'Regular'],[3,'StockPixel-Original-1'],
  [4,'Stock Pixel Regular'],[5,'Version 1.0'],[6,'StockPixel-Regular'],
  [13,'Original project glyphs. Distributed under the repository LICENSE.']];
let nameOffset = 0;
const strings = [], records = [];
for (const [id, text] of names) {
  const value = join([...text].map(c => u16(c.charCodeAt(0))));
  records.push(join(u16(3), u16(1), u16(0x0409), u16(id), u16(value.length), u16(nameOffset)));
  strings.push(value); nameOffset += value.length;
}
tables.name = join(u16(0), u16(names.length), u16(6 + names.length * 12), records, strings);
tables.post = join(u32(0x00030000), u32(0), i16(-100), i16(50), u32(1), Buffer.alloc(16));
const os2 = Buffer.alloc(96);
os2.writeUInt16BE(4, 0); os2.writeInt16BE(600, 2); os2.writeUInt16BE(400, 4);
os2.writeUInt16BE(5, 6); // fsType=0: installable embedding, never auto-installed.
os2.writeInt16BE(650, 10); os2.writeInt16BE(600, 12); os2.writeInt16BE(75, 16);
os2.writeInt16BE(650, 18); os2.writeInt16BE(600, 20); os2.writeInt16BE(350, 24);
os2.writeInt16BE(50, 26); os2.writeInt16BE(300, 28);
os2[32]=2; os2[33]=11; os2[34]=5; os2[35]=9;
os2.writeUInt32BE(3, 42); // Basic Latin + Latin-1.
os2.write('STPX', 58, 'ascii'); os2.writeUInt16BE(64, 62);
os2.writeUInt16BE(codes[0], 64); os2.writeUInt16BE(codes.at(-1), 66);
os2.writeInt16BE(800, 68); os2.writeInt16BE(-200, 70);
os2.writeUInt16BE(800, 74); os2.writeUInt16BE(200, 76); os2.writeUInt32BE(1, 78);
os2.writeInt16BE(700, 86); os2.writeInt16BE(700, 88); os2.writeUInt16BE(32, 92);
os2.writeUInt16BE(1, 94); tables['OS/2'] = os2;
function checksum(buffer) {
  const data = padded(buffer); let sum = 0;
  for (let i = 0; i < data.length; i += 4) sum = (sum + data.readUInt32BE(i)) >>> 0;
  return sum;
}
const tags = Object.keys(tables).sort();
const tablePower = 2 ** Math.floor(Math.log2(tags.length));
const header = join(u32(0x00010000), u16(tags.length), u16(tablePower * 16),
  u16(Math.log2(tablePower)), u16(tags.length * 16 - tablePower * 16));
let offset = 12 + tags.length * 16;
let headOffset;
const directory = [], data = [];
for (const tag of tags) {
  const table = tables[tag];
  directory.push(join(Buffer.from(tag), u32(checksum(table)), u32(offset), u32(table.length)));
  if (tag === 'head') headOffset = offset;
  const aligned = padded(table); data.push(aligned); offset += aligned.length;
}
const font = join(header, directory, data);
font.writeUInt32BE((0xb1b0afba - checksum(font)) >>> 0, headOffset + 8);
if (checksum(font) !== 0xb1b0afba) throw Error('Font checksum failed');
fs.writeFileSync(path.join(__dirname, 'stock-pixel.ttf'), font);
console.log(`Built original Stock Pixel: ${chars.length} characters, ${font.length} bytes.`);
