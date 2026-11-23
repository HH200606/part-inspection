"""生成测试用工业零件图片：模拟用户上传的 3D 渲染风格机械零件合集 + 实拍风格零件。
纯 PIL 绘制，不消耗额外积分。
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path('test-images')
OUT.mkdir(exist_ok=True)


def bg_canvas(w, h, color=(168, 168, 168)):
    im = Image.new('RGB', (w, h), color)
    d = ImageDraw.Draw(im)
    # 轻微噪点模拟渲染背景
    random.seed(7)
    for _ in range(3000):
        x = random.randint(0, w - 1); y = random.randint(0, h - 1)
        v = color[0] + random.randint(-6, 6)
        d.point((x, y), fill=(v, v, v))
    return im


def shadow(d, cx, cy, r):
    d.ellipse([cx - r + 5, cy - r + 7, cx + r + 5, cy + r + 7], fill=(120, 120, 120))


def draw_screw(d, cx, cy, L, angle):
    """三维感螺丝：圆柱杆 + 头部"""
    a = math.radians(angle)
    dx, dy = math.cos(a) * L, math.sin(a) * L
    shadow(d, cx + dx / 2, cy + dy / 2, L * 0.5)
    # 杆（灰色渐变多段）
    for t in range(9):
        k = t / 8
        x, y = cx + dx * k, cy + dy * k
        r = L * 0.16
        d.ellipse([x - r, y - r, x + r, y + r], fill=(195 - t * 4, 195 - t * 4, 200 - t * 4))
    # 头
    hx, hy = cx, cy
    d.ellipse([hx - L * 0.3, hy - L * 0.3, hx + L * 0.3, hy + L * 0.3], fill=(225, 225, 230), outline=(150, 150, 155), width=2)
    d.ellipse([hx - L * 0.15, hy - L * 0.15, hx + L * 0.15, hy + L * 0.15], fill=(90, 90, 95))
    # 螺纹线
    for t in range(1, 9):
        k = t / 9
        x, y = cx + dx * k, cy + dy * k
        px, py = -dy / L * L * 0.15, dx / L * L * 0.15
        d.line([x - px, y - py, x + px, y + py], fill=(140, 140, 145), width=1)


def draw_nut(d, cx, cy, R):
    shadow(d, cx, cy, R)
    pts = [(cx + R * math.cos(math.radians(60 * i)), cy + R * math.sin(math.radians(60 * i))) for i in range(6)]
    d.polygon(pts, fill=(212, 212, 218))
    d.line(pts + [pts[0]], fill=(240, 240, 245), width=2)
    d.ellipse([cx - R * 0.55, cy - R * 0.55, cx + R * 0.55, cy + R * 0.55], fill=(110, 110, 115), outline=(180, 180, 185), width=2)
    d.ellipse([cx - R * 0.42, cy - R * 0.42, cx + R * 0.42, cy + R * 0.42], fill=(70, 70, 75))


def draw_washer(d, cx, cy, R):
    shadow(d, cx, cy, R)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(205, 205, 210), outline=(235, 235, 240), width=2)
    d.ellipse([cx - R * 0.45, cy - R * 0.45, cx + R * 0.45, cy + R * 0.45], fill=(150, 150, 155))
    d.ellipse([cx - R * 0.42, cy - R * 0.42, cx + R * 0.42, cy + R * 0.42], fill=(168, 168, 168))


def draw_spring(d, cx, cy, L):
    shadow(d, cx, cy, L * 0.6)
    pts = []
    for i in range(60):
        t = i / 59
        x = cx + (t - 0.5) * L
        y = cy + math.sin(t * math.pi * 8) * L * 0.16
        pts.append((x, y))
    d.line(pts, fill=(215, 215, 220), width=4)
    d.line([(p[0], p[1] + 2) for p in pts], fill=(150, 150, 155), width=2)


def draw_bracket(d, cx, cy, R, angle):
    shadow(d, cx, cy, R)
    a = math.radians(angle)
    pts = []
    for i in range(8):
        ang = a + math.radians(i * 45)
        rr = R if i % 2 == 0 else R * 0.6
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=(200, 200, 206), outline=(235, 235, 240))
    d.ellipse([cx - R * 0.2, cy - R * 0.2, cx + R * 0.2, cy + R * 0.2], fill=(110, 110, 115))


def draw_cylinder(d, cx, cy, R, h):
    shadow(d, cx, cy, R)
    d.rectangle([cx - R, cy - h // 2, cx + R, cy + h // 2], fill=(198, 198, 204))
    d.ellipse([cx - R, cy - h // 2 - R * 0.35, cx + R, cy - h // 2 + R * 0.35], fill=(225, 225, 230), outline=(160, 160, 165), width=1)
    d.rectangle([cx - R + 4, cy - h // 2, cx - R + 10, cy + h // 2], fill=(235, 235, 240))


def draw_plate(d, cx, cy, R, angle):
    shadow(d, cx, cy, R)
    a = math.radians(angle)
    pts = [(cx + R * math.cos(a + math.radians(i * 60)) * (1 if i % 2 == 0 else 0.75),
            cy + R * math.sin(a + math.radians(i * 60)) * (1 if i % 2 == 0 else 0.75)) for i in range(6)]
    d.polygon(pts, fill=(210, 210, 216), outline=(240, 240, 245))
    for i in range(3):
        ang = a + math.radians(i * 120)
        hx, hy = cx + R * 0.5 * math.cos(ang), cy + R * 0.5 * math.sin(ang)
        d.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=(90, 90, 95))


def make_cad_set(path, seed, n=24):
    """3D 渲染风格机械零件合集（类似用户上传图）"""
    random.seed(seed)
    im = bg_canvas(900, 700, (172, 172, 172))
    d = ImageDraw.Draw(im)
    funcs = [
        lambda x, y: draw_screw(d, x, y, random.randint(38, 62), random.randint(0, 180)),
        lambda x, y: draw_nut(d, x, y, random.randint(22, 34)),
        lambda x, y: draw_washer(d, x, y, random.randint(20, 30)),
        lambda x, y: draw_spring(d, x, y, random.randint(45, 75)),
        lambda x, y: draw_bracket(d, x, y, random.randint(25, 38), random.randint(0, 180)),
        lambda x, y: draw_cylinder(d, x, y, random.randint(18, 28), random.randint(40, 70)),
        lambda x, y: draw_plate(d, x, y, random.randint(26, 40), random.randint(0, 180)),
    ]
    positions = []
    for i in range(n):
        for _ in range(30):
            x = random.randint(70, 830); y = random.randint(60, 640)
            if all((x - px) ** 2 + (y - py) ** 2 > 80 ** 2 for px, py in positions):
                positions.append((x, y)); break
        f = random.choice(funcs)
        f(x, y)
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    im.save(path, quality=95)
    print(path.name, n, 'parts')


def make_clean_set(path, seed):
    """规则排列的零件（便于计数质检）"""
    random.seed(seed)
    im = bg_canvas(900, 700, (160, 163, 167))
    d = ImageDraw.Draw(im)
    # 3行5列规则排列
    for r in range(3):
        for c in range(5):
            x = 120 + c * 165; y = 130 + r * 200
            k = (r * 5 + c) % 4
            if k == 0: draw_screw(d, x, y, 55, random.randint(0, 180))
            elif k == 1: draw_nut(d, x, y, 30)
            elif k == 2: draw_washer(d, x, y, 28)
            else: draw_spring(d, x, y, 60)
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    im.save(path, quality=95)
    print(path.name, 15, 'parts')


make_cad_set(OUT / 'test-cad-parts-1.jpg', 101, 24)
make_cad_set(OUT / 'test-cad-parts-2.jpg', 202, 18)
make_clean_set(OUT / 'test-organized-parts.jpg', 303)
