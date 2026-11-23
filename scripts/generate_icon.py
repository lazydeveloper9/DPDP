"""
CS-01 DPDP Compliance Auditor — Icon Generation Script.

Creates multi-resolution Windows .ico and high-res PNG shield icons
representing zero-egress data protection under India's DPDP Act, 2023.
"""
from __future__ import annotations

from pathlib import Path


def generate_icons(output_dir: Path | None = None) -> tuple[Path, Path]:
    """Generates assets/cs01.png and assets/cs01.ico with multi-resolution layers."""
    from PIL import Image, ImageDraw, ImageFont

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "assets"
    output_dir.mkdir(parents=True, exist_ok=True)

    png_path = output_dir / "cs01.png"
    ico_path = output_dir / "cs01.ico"

    # Base size 512x512
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Outer Hexagonal Shield Outline
    # Coordinates for a modern cybersecurity shield
    shield_pts = [
        (256, 32),    # Top center
        (460, 96),    # Top right
        (430, 360),   # Bottom right curve
        (256, 480),   # Bottom apex
        (82, 360),    # Bottom left curve
        (52, 96),     # Top left
    ]

    # Draw dark corporate blue background fill
    draw.polygon(shield_pts, fill=(15, 23, 42, 255))  # #0f172a

    # Draw thick neon cyan border (#38bdf8)
    draw.polygon(shield_pts, outline=(56, 189, 248, 255), width=18)

    # 2. Inner Shield Accent (#1e293b)
    inner_pts = [
        (256, 68),
        (420, 120),
        (394, 335),
        (256, 440),
        (118, 335),
        (92, 120),
    ]
    draw.polygon(inner_pts, fill=(30, 41, 59, 255), outline=(14, 165, 233, 200), width=6)

    # 3. Security Padlock / Shield Emblem in Center (Emerald #10b981)
    # Shackle
    draw.arc([200, 140, 312, 250], start=180, end=0, fill=(16, 185, 129, 255), width=18)
    # Body
    draw.rounded_rectangle([180, 220, 332, 340], radius=16, fill=(16, 185, 129, 255))
    # Keyhole
    draw.ellipse([242, 254, 270, 282], fill=(15, 23, 42, 255))
    draw.polygon([(250, 274), (262, 274), (266, 308), (246, 308)], fill=(15, 23, 42, 255))

    # 4. Text "DPDP" banner at bottom
    try:
        font = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font = ImageFont.load_default()

    draw.text((256, 375), "DPDP", fill=(248, 250, 252, 255), font=font, anchor="mm")

    # Save PNG
    img.save(png_path, format="PNG")

    # Save Multi-resolution ICO
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
    img.save(ico_path, format="ICO", sizes=icon_sizes)

    return png_path, ico_path


if __name__ == "__main__":
    p_png, p_ico = generate_icons()
    print(f"Generated icons successfully:\n  PNG: {p_png}\n  ICO: {p_ico}")
