from PIL import Image, ImageDraw


def make_icon(size: int = 64) -> Image.Image:
    """生成托盘和 exe 共用的图标，避免依赖外部图片文件。"""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = size / 64
    draw.ellipse(
        [4 * scale, 4 * scale, 60 * scale, 60 * scale],
        fill=(76, 141, 255, 255),
    )
    draw.rectangle(
        [18 * scale, 22 * scale, 46 * scale, 28 * scale],
        fill=(255, 255, 255, 255),
    )
    draw.rectangle(
        [18 * scale, 34 * scale, 40 * scale, 40 * scale],
        fill=(255, 255, 255, 255),
    )
    return image
