# WSL → Windows Desktop Icon Shortcut Creation

## Overview
Create a Windows desktop shortcut (.lnk) with a custom icon (.ico) for a WSL-based tool, entirely from within WSL.

## Prerequisites
- Pillow (PIL) installed in the WSL Python venv: `pip install Pillow`
- VBScript engine (cscript.exe) available via WSL interop
- Source image (webp, png, jpg) somewhere accessible from WSL

## Step-by-Step

### Step 1: Convert image to multi-resolution ICO

Pillow's built-in ICO save does NOT reliably create multi-resolution ICOs. Use manual ICO file construction:

```python
from PIL import Image
import struct

img = Image.open('/mnt/c/.../source.png')
if img.mode != 'RGBA':
    img = img.convert('RGBA')

ico_path = '/mnt/c/.../output.ico'
sizes = [16, 24, 32, 48, 64, 128, 256]

icon_dirs = []
data_blocks = []
offset = 6 + len(sizes) * 16  # ICO header + directory entries

for s in sizes:
    thumb = img.resize((s, s), Image.LANCZOS)
    
    # BITMAPINFOHEADER (40 bytes)
    bmp_header = struct.pack('<I', 40)  # header size
    bmp_header += struct.pack('<ii', s, s * 2)  # width, height*2 (incl AND mask)
    bmp_header += struct.pack('<HH', 1, 32)  # planes=1, bpp=32
    bmp_header += struct.pack('<I', 0)  # BI_RGB (no compression)
    bmp_header += struct.pack('<I', s * s * 4)  # image size
    bmp_header += struct.pack('<ii', 0, 0)  # DPI
    bmp_header += struct.pack('<I', 0)  # colors used
    bmp_header += struct.pack('<I', 0)  # important colors
    
    # Pixel data: BGRA, bottom-to-top rows (BMP convention)
    pixels = []
    for y in range(s - 1, -1, -1):
        for x in range(s):
            r, g, b, a = thumb.getpixel((x, y))
            pixels.extend([b, g, r, a])
    
    block = bmp_header + bytes(pixels)
    icon_dirs.append((s, s, len(block), offset))
    data_blocks.append(block)
    offset += len(block)

with open(ico_path, 'wb') as f:
    # ICO header
    f.write(struct.pack('<HHH', 0, 1, len(sizes)))
    # Directory entries
    for (w, h, size, off) in icon_dirs:
        w_byte = 0 if w >= 256 else w
        h_byte = 0 if h >= 256 else h
        f.write(struct.pack('<BBBBHHII', w_byte, h_byte, 0, 0, 1, 32, size, off))
    # Data blocks
    for block in data_blocks:
        f.write(block)

print(f'ICO created: {os.path.getsize(ico_path)} bytes, {len(sizes)} sizes')
```

### Step 2: Create .lnk shortcut via VBScript

Write a VBS file to `/mnt/c/tmp/` (accessible as `C:\tmp\` from Windows):

```vbs
Set shell = CreateObject("WScript.Shell")
Set shortcut = shell.CreateShortcut("C:\Users\<USER>\Desktop\<NAME>.lnk")
shortcut.TargetPath = "C:\Users\<USER>\Desktop\<NAME>.bat"
shortcut.WorkingDirectory = "C:\Users\<USER>\Desktop"
shortcut.IconLocation = "C:\Users\<USER>\Desktop\path\to\icon.ico"
shortcut.Description = "Description text"
shortcut.Save
```

Execute from WSL:
```bash
cscript.exe //nologo "C:\tmp\create_shortcut.vbs"
```

**Important**: The VBS file path from WSL must use `"C:\tmp\..."` (quoted) NOT `/mnt/c/tmp/...` because cscript.exe is a Windows binary that expects Windows paths.

### Step 3: Verify

```bash
ls -la "/mnt/c/Users/<USER>/Desktop/<NAME>.lnk"
strings "/mnt/c/Users/<USER>/Desktop/<NAME>.lnk" | grep -i "icon\|ico"
```

The `.ico` file should be ~350KB+ for a 7-size ICO, or smaller for fewer sizes.

## Encoding Rules for .bat Files
**Pure ASCII only.** No Chinese characters, no Unicode, no non-7-bit bytes. Reason: WSL writes files as UTF-8; Windows cmd.exe encoding varies by system locale (CP437, CP936, CP65001). ASCII is the only safe intersection. Verify with:

```python
with open(path, 'rb') as f:
    raw = f.read()
assert all(b < 128 for b in raw), "Non-ASCII bytes found!"
```

## Known Pitfalls
1. **PowerShell COM (New-Object -ComObject WScript.Shell) from WSL** may silently produce a shortcut that lacks the icon. VBScript with cscript.exe is more reliable.
2. **Windows icon cache** may show the old/default icon even after correct creation. User may need to: refresh desktop (F5), delete IconCache.db, or restart explorer.exe.
3. **Cannot visually verify from WSL**. The agent cannot see the Windows desktop. Always state this limitation when reporting completion.
4. **File path for cscript.exe** must be a Windows-style path in quotes, NOT a Linux /mnt/c/ path.
5. **Pillow ICO save() is unreliable** for multi-resolution ICO. Always use manual BMP-in-ICO construction.
