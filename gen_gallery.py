#!/usr/bin/env python3
"""
gen_gallery.py — 扫描 pictures/<相册>/ 下的照片，自动生成画廊页面。

用法:
    python gen_gallery.py

结构（对应 mkdocs.yml 中的 nav）:
    首页 index.md                     轮播图 + 故事流
    旅游/index.md                     二级分类卡片列表
    旅游/徒步/index.md                地点卡片列表（复刻原站"游记"布局）
    旅游/徒步/云南/index.md           照片墙
    扫街/index.md                     照片墙（直接挂相册）

照片目录: 项目根目录 pictures/<相册>/*.jpg（docs/pictures 是指向它的软链接）
新增/调整地点时修改下方 GALLERIES 配置，并同步 mkdocs.yml 的 nav。
"""
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
PIC_ROOT = DOCS / "pictures"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}

# ---------------------------------------------------------------- 配置区
# folder = pictures/ 下的相册文件夹名；location/desc 显示在卡片上
GALLERIES = {
    "旅游": {
        "subtitle": "TRAVEL",
        "poem": "少年负壮气，奋烈自有时。<br>落花踏尽游何处，笑入胡姬酒肆中。",
        "sections": {
            "徒步": {
                "locations": [
                    {"name": "云南", "folder": "yunnan", "location": "云南", "desc": ""},
                    {"name": "桂林", "folder": "guilin", "location": "广西 · 桂林", "desc": ""},
                    {"name": "稻城", "folder": "daocheng", "location": "四川 · 甘孜", "desc": ""},
                ],
            },
            "风景": {
                "locations": [
                    {"name": "海岛", "folder": "haidao", "location": "", "desc": ""},
                ],
            },
        },
    },
}

# 顶层独立照片墙页面：标题 -> 相册文件夹
PAGES = {
    "扫街": {"folder": "shenzhenwan", "poem": ""},
}

# 地图标记点（Leaflet + OSM）：name 显示在弹窗，url 为照片墙相对路径，lat/lng 为经纬度
# cover 留空则自动取该相册第一张照片
MAP_POINTS = [
    {"name": "云南", "url": "旅游/徒步/云南/", "folder": "yunnan", "lat": 25.0, "lng": 101.5, "location": "云南"},
    {"name": "桂林", "url": "旅游/徒步/桂林/", "folder": "guilin", "lat": 25.27, "lng": 110.29, "location": "广西 · 桂林"},
    {"name": "稻城", "url": "旅游/徒步/稻城/", "folder": "daocheng", "lat": 29.03, "lng": 100.30, "location": "四川 · 甘孜"},
    {"name": "海岛", "url": "旅游/风景/海岛/", "folder": "haidao", "lat": 19.5, "lng": 109.5, "location": ""},
    {"name": "扫街", "url": "扫街/", "folder": "shenzhenwan", "lat": 22.52, "lng": 114.06, "location": "深圳湾"},
]

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


def list_photos(folder: str):
    d = PIC_ROOT / folder
    if not d.is_dir():
        print(f"  [警告] 相册不存在: pictures/{folder}")
        return []
    return sorted(
        p for p in d.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )


def url(path: str) -> str:
    return "/".join(quote(seg) for seg in path.split("/"))


def wall_page(title: str, poem: str, photos: list[Path], folder: str, depth: int) -> str:
    """照片墙页面（glightbox + 懒加载）。depth = 页面相对根目录的深度，用于回指 pictures/"""
    prefix = "../" * depth
    items = []
    for ph in photos:
        u = url(f"{prefix}pictures/{folder}/{ph.name}")
        items.append(
            f'<div class="photo">\n'
            f'<a class="glightbox" data-type="image" data-width="auto" '
            f'data-height="90%" href="{u}" data-desc-position="bottom">\n'
            f'<img src="{SVG_PH}" alt="{ph.stem}" data-lazy-src="{u}">\n'
            f'</a>\n</div>'
        )
    body = "\n".join(items)
    head = f"# {title}\n\n{poem}\n\n" if poem else f"# {title}\n\n"
    return head + f'<div class="photo-wall">\n\n{body}\n\n</div>\n'


def card_list_page(title: str, poem: str, cards: list[dict], depth: int) -> str:
    """卡片列表页（复刻原站"游记"布局：标题+定位+封面+描述）。cards: name/href/cover/desc/location"""
    prefix = "../" * depth
    items = []
    for c in cards:
        cover = url(prefix + c["cover"]) if c.get("cover") else ""
        loc = f'<font size="3">:material-map-marker: {c["location"]}</font>' if c.get("location") else ""
        items.append(
            f'- ### **[{c["name"]}]({c["href"]})** {loc}\n\n'
            f'    ---\n\n'
            f'    <a href="{c["href"]}"><img src="{SVG_PH}" alt="{c["name"]}" '
            f'class="no-glb" data-lazy-src="{cover}"></a>\n\n'
            f'    {c.get("desc", "")}\n'
        )
    body = "\n".join(items)
    head = f"# {title}\n\n{poem}\n\n" if poem else f"# {title}\n\n"
    return head + f'<div class="grid cards index-info" markdown>\n\n{body}\n\n</div>\n'


def gen_homepage(leaves: list[dict]) -> str:
    """首页轮播图（每个叶子相册一张幻灯片）+ 照片故事流"""
    slides_css, slides_html = [], []
    for i, leaf in enumerate(leaves, 1):
        cover = url(leaf["cover"]) if leaf.get("cover") else ""
        slides_css.append(
            f".carousel-item--{i} .carousel-item__image {{ background-image: url('{cover}'); }}"
        )
        slides_html.append(
            f'''<div class="carousel-item carousel-item--{i}{" active" if i == 1 else ""}">
<div class="carousel-item__image"></div>
<div class="carousel-item__info">
<div class="carousel-item__container">
<h2 class="carousel-item__subtitle">{leaf["subtitle"]}</h2>
<h1 class="carousel-item__title">{leaf["name"]}</h1>
<p class="carousel-item__description">{leaf.get("poem", "")}</p>
<a href="{url(leaf["href"])}" class="carousel-item__btn">Explore</a>
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


FRONTMATTER = "---\nhide:\n  - navigation\n---\n\n"


def write(rel: str, content: str):
    out = DOCS / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(FRONTMATTER + content, encoding="utf-8")
    print(f"生成: docs/{rel}")


def main():
    if not PIC_ROOT.exists():
        raise SystemExit(f"目录不存在: {PIC_ROOT}")

    leaves = []  # 首页轮播用：每个叶子相册 {name, subtitle, poem, href, cover}

    for top, cfg in GALLERIES.items():
        section_cards = []
        for sec, sec_cfg in cfg["sections"].items():
            loc_cards = []
            for loc in sec_cfg["locations"]:
                photos = list_photos(loc["folder"])
                if not photos:
                    continue
                cover = f"pictures/{loc['folder']}/{photos[0].name}"
                # 叶子：照片墙（深度 3，如 旅游/徒步/云南/）
                rel_base = f"{top}/{sec}/{loc['name']}"
                write(
                    f"{rel_base}/index.md",
                    wall_page(loc["name"], loc.get("poem", ""), photos, loc["folder"], 3),
                )
                loc_cards.append({
                    "name": loc["name"], "href": f"{loc['name']}/",
                    "cover": cover, "location": loc.get("location", ""),
                    "desc": loc.get("desc", ""),
                })
                leaves.append({
                    "name": loc["name"], "subtitle": loc.get("location", sec).upper() or sec.upper(),
                    "href": f"{rel_base}/", "cover": cover,
                })
            if loc_cards:
                # 二级列表页（深度 2，如 旅游/徒步/）
                write(
                    f"{top}/{sec}/index.md",
                    card_list_page(sec, sec_cfg.get("poem", ""), loc_cards, 2),
                )
                section_cards.append({
                    "name": sec, "href": f"{sec}/",
                    "cover": loc_cards[0]["cover"],
                    "location": "", "desc": "",
                })
        if section_cards:
            # 一级列表页（深度 1，如 旅游/）
            write(
                f"{top}/index.md",
                card_list_page(top, cfg.get("poem", ""), section_cards, 1),
            )

    for title, cfg in PAGES.items():
        photos = list_photos(cfg["folder"])
        if not photos:
            continue
        write(title + "/index.md", wall_page(title, cfg.get("poem", ""), photos, cfg["folder"], 1))
        leaves.append({
            "name": title, "subtitle": title.upper(),
            "href": f"{title}/", "cover": f"pictures/{cfg['folder']}/{photos[0].name}",
        })

    write("index.md", gen_homepage(leaves))
    write_map()
    print(f"\n完成，共 {len(leaves)} 个相册。接下来: mkdocs serve 预览 / git push 自动部署")


def write_map():
    """生成地图页：内嵌 JSON 标记数据，map.js 读取后渲染 Leaflet 标记。"""
    import json
    pts = []
    for p in MAP_POINTS:
        photos = list_photos(p["folder"])
        cover = p.get("cover") or (f"pictures/{p['folder']}/{photos[0].name}" if photos else "")
        pts.append({
            "name": p["name"], "url": url(p["url"]),
            "lat": p["lat"], "lng": p["lng"], "location": p.get("location", ""),
            # 站点部署在 /gallery/ 子路径，封面用相对根路径避免在 /map/ 下拼错
            "cover": url(cover) if cover else "",
        })
    # 所有页面同级（use_directory_urls 下 map/ 是一级目录），返回上一级即站点根
    for p in pts:
        p["url"] = "../" + p["url"]
        if p["cover"]:
            p["cover"] = "../" + p["cover"]
    data = json.dumps(pts, ensure_ascii=False)
    content = (
        "# 地图\n\n"
        '<div id="gallery-map"></div>\n\n'
        f'<script id="map-data" type="application/json">{data}</script>\n'
    )
    out = DOCS / "map.md"
    out.write_text(FRONTMATTER + content, encoding="utf-8")
    print("生成: docs/map.md")


if __name__ == "__main__":
    main()
