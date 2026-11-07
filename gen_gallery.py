#!/usr/bin/env python3
"""
gen_gallery.py — 扫描 docs/pictures/<分类>/ 下的照片，自动生成画廊页面。

用法:
    python gen_gallery.py

目录约定:
    docs/pictures/游记/*.jpg   ->  docs/游记/index.md (照片墙页面)
    首页 docs/index.md 的轮播图按分类生成，封面取该分类第一张照片。

分类的英文副标题和诗句在下方 CATEGORIES 中维护；
首页故事流在 STORIES 中维护。新增分类文件夹后在此补充即可。
"""
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
PIC_ROOT = DOCS / "pictures"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}

# ---------------------------------------------------------------- 配置区
# key = pictures/ 下的文件夹名（同时也是生成的页面路径和标题）
CATEGORIES = {
    "haidao": {
        "subtitle": "HAIDAO",
        "poem": "",
    },
    "yunnan": {
        "subtitle": "YUNNAN",
        "poem": "",
    },
    "shenzhenwan": {
        "subtitle": "SHENZHENWAN",
        "poem": "",
    },
    "guilin": {
        "subtitle": "GUILIN",
        "poem": "",
    },
    "daocheng": {
        "subtitle": "DAOCHENG",
        "poem": "",
    },
}

# 首页照片故事流：img 为 pictures/ 下的相对路径，side 决定竖排文字在左还是右
STORIES = [
    {
        "img": "pictures/haidao/9V5A0474.jpg",
        "line1": "野旷天低树",
        "line2": "江清月近人",
        "side": "right",
    },
    {
        "img": "pictures/yunnan/9V5A7008.jpg",
        "line1": "云海映楼阁",
        "line2": "白浪绕山丘",
        "side": "left",
    },
]
# ---------------------------------------------------------------- 配置区结束

SVG_PH = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 3'%3E%3C/svg%3E"


def list_photos(category_dir: Path):
    return sorted(
        p for p in category_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )


def url(path: str) -> str:
    return "/".join(quote(seg) for seg in path.split("/"))


def gen_category_page(category: str, photos: list[Path]) -> str:
    """生成单个分类的照片墙页面（复刻原站 glightbox + 懒加载结构）"""
    meta = CATEGORIES.get(category, {})
    poem = meta.get("poem", "").replace("<br>", " ")
    items = []
    for ph in photos:
        rel = f"pictures/{category}/{ph.name}"
        u = url(f"../{rel}")
        items.append(
            f'<div class="photo">\n'
            f'<a class="glightbox" data-type="image" data-width="auto" '
            f'data-height="90%" href="{u}" data-desc-position="bottom">\n'
            f'<img src="{SVG_PH}" alt="{ph.stem}" data-lazy-src="{u}">\n'
            f'</a>\n</div>'
        )
    wall = "\n".join(items)
    return (
        f"# {category}\n\n"
        f"{poem}\n\n"
        f'<div class="photo-wall-s2">\n\n{wall}\n\n</div>\n'
    )


def gen_homepage(categories: dict[str, list[Path]]) -> str:
    """生成首页：轮播图 + 照片故事流（复刻原站结构）"""
    slides_css, slides_html = [], []
    for i, (cat, photos) in enumerate(categories.items(), 1):
        meta = CATEGORIES.get(cat, {"subtitle": cat.upper(), "poem": ""})
        cover = url(f"pictures/{cat}/{photos[0].name}") if photos else ""
        slides_css.append(
            f".carousel-item--{i} .carousel-item__image {{ background-image: url('{cover}'); }}"
        )
        slides_html.append(
            f'''<div class="carousel-item carousel-item--{i}{" active" if i == 1 else ""}">
<div class="carousel-item__image"></div>
<div class="carousel-item__info">
<div class="carousel-item__container">
<h2 class="carousel-item__subtitle">{meta["subtitle"]}</h2>
<h1 class="carousel-item__title">{cat}</h1>
<p class="carousel-item__description">{meta["poem"]}</p>
<a href="{url(cat)}/" class="carousel-item__btn">Explore</a>
</div>
</div>
</div>'''
        )

    carousel = ""
    if slides_html:
        carousel = f"""<style>
{chr(10).join(slides_css)}
</style>
<div class="travel-div">
<div class="carousel">
<div class="carousel__nav">
<span id="moveLeft" class="carousel__arrow"><svg class="carousel__icon" width="24" height="24" viewBox="0 0 24 24"><path d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"></path></svg></span>
<span id="moveRight" class="carousel__arrow"><svg class="carousel__icon" width="24" height="24" viewBox="0 0 24 24"><path d="M4,11V13H16L10.5,18.5L11.92,19.92L19.84,12L11.92,4.08L10.5,5.5L16,11H4Z"></path></svg></span>
</div>
{chr(10).join(slides_html)}
</div>
</div>"""

    stories = []
    for s in STORIES:
        img = Path(DOCS / s["img"])
        if not img.exists():
            print(f"  [跳过] 故事流图片不存在: {s['img']}")
            continue
        cls = "story-text" if s.get("side") == "right" else "story-text-l"
        u = url(s["img"])
        stories.append(
            f'''<div class="photo-story">
<a class="glightbox" data-type="image" data-width="auto" data-height="90%" href="{u}" data-desc-position="bottom">
<img alt="{img.stem}" src="{u}" data-lazy-src="{u}">
</a>
<div class="{cls}">
<div class="story-1">{s["line1"]}</div>
<div class="story-2">{s["line2"]}</div>
</div>
</div>'''
        )

    return carousel + "\n\n" + "\n\n".join(stories) + "\n"


def main():
    if not PIC_ROOT.exists():
        raise SystemExit(f"目录不存在: {PIC_ROOT}\n请先创建并放入分类文件夹和照片。")

    categories = {}
    for d in sorted(PIC_ROOT.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            photos = list_photos(d)
            if photos:
                categories[d.name] = photos
            else:
                print(f"  [跳过] 空分类: {d.name}")

    if not categories:
        raise SystemExit("docs/pictures/ 下没有任何照片。")

    # 首页
    (DOCS / "index.md").write_text(gen_homepage(categories), encoding="utf-8")
    print(f"生成首页: docs/index.md （{len(categories)} 个轮播分类）")

    # 分类页
    for cat, photos in categories.items():
        out = DOCS / cat / "index.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(gen_category_page(cat, photos), encoding="utf-8")
        print(f"生成分类页: docs/{cat}/index.md （{len(photos)} 张照片）")

    print("\n完成。接下来运行: mkdocs serve 预览 / mkdocs gh-deploy 部署")


if __name__ == "__main__":
    main()
