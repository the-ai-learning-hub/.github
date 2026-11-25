# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50", "brotli>=1.1"]
# ///
"""Build the SVG artwork used by profile/README.md.

    uv run scripts/build_profile_assets.py

Every image comes in a light and a dark version and carries its own subset of
Bricolage Grotesque and JetBrains Mono (both SIL OFL), so it looks the same on
every machine. To add a lesson, append it to LESSONS and run the script again.
"""

from __future__ import annotations

import base64
import io
import urllib.request
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "profile" / "assets"
CACHE = Path(__file__).resolve().parent / ".cache"

# ─────────────────────────────────────────────────────────────── content ──

ORG = "the-ai-learning-hub"
RAW = f"https://raw.githubusercontent.com/{ORG}/.github/main/profile/assets"

# One entry per lesson, in order. Fields:
#   repo   repository name in the organization (slides are assumed at
#          https://ORG.github.io/<repo>/)
#   num    two-digit lesson number      short  one word under the network
#   title  station title                text   one or two sentences
#   code   one line of code, as (text, colour) runs; colours: text, muted,
#          fn, str, or any palette name
#   facts  two short lines shown under the code
#   colab  optional link for "Run without installing"
#   color  optional; otherwise taken in order from PALETTE
LESSONS = [
    dict(
        repo="00-environment-setup",
        num="00",
        short="Setup",
        title="Setup & first steps",
        text="Install uv, VS Code and Git, then write your first three "
        "Python programs and push them to GitHub.",
        code=[("$ ", "muted"), ("uv run ", "fn"), ("3_talking_cow.py", "text")],
        facts=["Slides and a hands-on challenge", "Windows, macOS and Linux"],
        color="teal",
    ),
    dict(
        repo="01-python-as-ai-first-steps",
        num="01",
        short="Python",
        title="Python: first steps",
        text="Variables, loops, functions and classes, then pandas and charts "
        "with real data: penguins, the Titanic and a novel.",
        code=[("penguins", "text"), (".", "muted"), ("groupby", "fn"),
              ("(", "muted"), ('"species"', "str"), (")", "muted")],
        facts=["6 notebooks", "109 exercises with solutions"],
        color="orange",
    ),
    dict(
        repo="02-machine-learning-fundamentals",
        num="02",
        short="ML",
        title="Machine Learning fundamentals",
        text="Run a real project with CRISP-DM, train and judge models, build "
        "a neural network from scratch and teach an agent to play.",
        code=[("model", "text"), (".", "muted"), ("fit", "fn"),
              ("(X_train, y_train)", "text")],
        facts=["5 notebooks, about 6 hours", "Opens in Google Colab"],
        colab=f"https://github.com/{ORG}/02-machine-learning-fundamentals#o-percurso",
        color="purple",
    ),
    dict(
        repo="03-applied-ai-projects",
        num="03",
        short="Applied AI",
        title="Applied AI: text, images, sound",
        text="Build a spam filter, read tweets, tell cats from dogs, then "
        "connect words, photos and voices with CLIP, Whisper and RAG.",
        code=[("clip_zero_shot", "fn"), ("(", "muted"), ("photos", "text"),
              (", ", "muted"), ('["cat", "dog"]', "str"), (")", "muted")],
        facts=["5 notebooks and 3 challenges", "Opens in Google Colab"],
        colab=f"https://github.com/{ORG}/03-applied-ai-projects#the-path",
        color="blue",
    ),
]

NEXT = dict(
    num=f"{len(LESSONS):02d}",
    title="The next station",
    text="The next lesson is being built. Follow the organization to know "
    "when it opens.",
)

# Palmer Penguins species colours (Lesson 01's dataset) on polar night / ice,
# then sea-ice blue, krill coral and sun gold for the lessons after them.
PALETTE = ["teal", "orange", "purple", "blue", "coral", "gold"]
THEMES = {
    "dark": dict(
        page="#0d1117", bg="#0E1A2E", surface="#132440", text="#EEF4FA",
        muted="#8EA2BF", line="#2B4163", teal="#3CCBC2", orange="#FF9F45",
        purple="#B884FF", blue="#6CB4FF", coral="#FF7F91", gold="#E9C44C",
    ),
    "light": dict(
        page="#ffffff", bg="#EAF1F7", surface="#F6F9FC", text="#10213A",
        muted="#53647E", line="#BFD0E2", teal="#00807C", orange="#C45E08",
        purple="#8740D0", blue="#1F62C4", coral="#C0354C", gold="#856500",
    ),
}
for _i, _L in enumerate(LESSONS):
    _L.setdefault("color", PALETTE[_i % len(PALETTE)])

# ───────────────────────────────────────────────────────────────── fonts ──

FONT_SOURCES = {
    "bricolage": "https://github.com/google/fonts/raw/main/ofl/bricolagegrotesque/"
    "BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf",
    "jbmono": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/"
    "JetBrainsMono%5Bwght%5D.ttf",
}

ROLES = {
    "display": ("bricolage", {"wght": 800, "opsz": 96, "wdth": 100}),
    "semi": ("bricolage", {"wght": 650, "opsz": 28, "wdth": 100}),
    "text": ("bricolage", {"wght": 420, "opsz": 14, "wdth": 100}),
    "mono": ("jbmono", {"wght": 450}),
}


def _download(name: str) -> bytes:
    path = CACHE / f"{name}.ttf"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(FONT_SOURCES[name]) as r:  # noqa: S310
            path.write_bytes(r.read())
    return path.read_bytes()


class Fonts:
    def __init__(self) -> None:
        self.raw: dict[str, bytes] = {}
        self.metrics: dict[str, tuple[dict, dict, int]] = {}
        for role, (src, axes) in ROLES.items():
            font = TTFont(io.BytesIO(_download(src)))
            instantiateVariableFont(font, axes, inplace=True)
            buf = io.BytesIO()
            font.save(buf)
            self.raw[role] = buf.getvalue()
            self.metrics[role] = (
                font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm
            )

    def width(self, role: str, s: str, size: float, tracking: float = 0) -> float:
        cmap, hmtx, upm = self.metrics[role]
        adv = sum(hmtx[cmap.get(ord(c), ".notdef")][0] for c in s)
        return adv * size / upm + tracking * len(s)

    def face(self, role: str, chars: set[str]) -> str:
        font = TTFont(io.BytesIO(self.raw[role]))
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt"]
        opts.hinting = False
        sub = Subsetter(opts)
        sub.populate(text="".join(sorted(chars | {" "})))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        return (f"@font-face{{font-family:hub-{role};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


# ────────────────────────────────────────────────────────────────── svg ──


@dataclass
class Svg:
    fonts: Fonts
    w: int
    h: int
    title: str
    parts: list[str] = field(default_factory=list)
    used: dict[str, set[str]] = field(default_factory=dict)
    css: list[str] = field(default_factory=list)

    def add(self, s: str) -> None:
        self.parts.append(s)

    def text(self, x, y, s, role, size, fill, anchor="start", tracking=0.0,
             extra="") -> None:
        self.used.setdefault(role, set()).update(s)
        ls = f' letter-spacing="{tracking}"' if tracking else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="hub-{role}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}'
                 f'{extra}>{escape(s)}</text>')

    def spans(self, x, y, runs, role, size, theme, anchor="start") -> None:
        """runs = [(text, colour_key), …] drawn as one line."""
        for s, _ in runs:
            self.used.setdefault(role, set()).update(s)
        inner = "".join(f'<tspan fill="{theme[k]}">{escape(s)}</tspan>'
                        for s, k in runs)
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="hub-{role}" '
                 f'font-size="{size}" text-anchor="{anchor}" xml:space="preserve">'
                 f'{inner}</text>')

    def wrap(self, s, role, size, max_w) -> list[str]:
        lines, cur = [], ""
        for word in s.split():
            trial = f"{cur} {word}".strip()
            if cur and self.fonts.width(role, trial, size) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + [cur] if cur else lines

    def render(self) -> str:
        faces = "".join(self.fonts.face(r, c) for r, c in self.used.items())
        style = faces + "".join(self.css)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" '
                f'aria-label="{escape(self.title)}"><title>{escape(self.title)}'
                f'</title><style>{style}</style>{"".join(self.parts)}</svg>')


# ───────────────────────────────────────────────────────────────── hero ──


def hero(fonts: Fonts, t: dict) -> str:
    W, H = 1280, 560
    svg = Svg(fonts, W, H, "The AI Learning Hub: learn AI by understanding "
              "every line you run")
    svg.add(f'<rect width="{W}" height="{H}" rx="28" fill="{t["bg"]}"/>')

    # faint graph-paper grid, the notebook the lessons are written on
    svg.add('<defs><pattern id="g" width="32" height="32" '
            'patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" '
            f'stroke="{t["line"]}" stroke-width="1" opacity=".35"/></pattern>'
            '<clipPath id="c"><rect width="1280" height="560" rx="28"/>'
            '</clipPath></defs>')
    svg.add(f'<rect width="{W}" height="{H}" fill="url(#g)" clip-path="url(#c)"/>')

    # ── left column: words
    x0 = 76
    svg.text(x0, 96, "github.com/the-ai-learning-hub", "mono", 18, t["muted"])
    lines = ["The AI", "Learning Hub"]
    size = 112
    while max(fonts.width("display", s, size, -3) for s in lines) > 620:
        size -= 2
    y = 96 + size * 1.05
    for s in lines:
        svg.text(x0, y, s, "display", size, t["text"], tracking=-3)
        y += size * 0.96
    y += 56 - size * 0.96
    for s in svg.wrap("Free, hands-on lessons that take you from your first "
                      "line of Python to your first neural network.",
                      "text", 25, 560):
        svg.text(x0, y, s, "text", 25, t["muted"])
        y += 36
    svg.spans(x0, H - 62, [(">>> ", "muted"), ("understand", "purple"),
                           ("(", "muted"), ("every_line_you_run", "text"),
                           (")", "muted")], "mono", 21, t)

    # ── right column: the curriculum as a network, "You" as its output
    cols = [(L["short"], L["num"], t[L["color"]], 4 if i else 3, False)
            for i, L in enumerate(LESSONS)]
    cols.append(("Next", NEXT["num"], t["muted"], 3, True))
    cols.append(("You", "", t["text"], 1, False))
    nx0, nx1, ny0, ny1 = 770, 1196, 78, 418
    step = (nx1 - nx0) / (len(cols) - 1)
    # labels shrink as the network grows, so neighbours never touch
    label_size = 19
    while label_size > 11 and max(fonts.width("semi", c[0], label_size)
                                  for c in cols) > step - 10:
        label_size -= 1
    pos = []
    for ci, (_, _, _, n, _) in enumerate(cols):
        x = nx0 + ci * step
        gap = 94 if n > 1 else 0
        top = (ny0 + ny1) / 2 - gap * (n - 1) / 2
        pos.append([(x, top + k * gap) for k in range(n)])

    T, hop = 7.0, 0.75                  # cycle seconds, seconds per layer
    pp = hop / T * 100                  # percent of cycle per layer
    css = svg.css
    edges, pulses = [], []
    for ci in range(len(cols) - 1):
        a, b = ci * pp, (ci + 1) * pp
        css.append(
            f"@keyframes p{ci}{{0%,{a:.2f}%{{stroke-dashoffset:16;opacity:0}}"
            f"{a + .4:.2f}%{{opacity:1}}{b:.2f}%{{stroke-dashoffset:-100;"
            f"opacity:1}}{b + .3:.2f}%,100%{{stroke-dashoffset:-100;opacity:0}}}}"
            f".p{ci}{{animation:p{ci} {T}s linear infinite}}")
        colour = cols[ci][2]
        for (x1, y1) in pos[ci]:
            for (x2, y2) in pos[ci + 1]:
                d = f"M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}"
                dash = ' stroke-dasharray="4 6"' if cols[ci + 1][4] or cols[ci][4] else ""
                edges.append(f'<path d="{d}" stroke="{t["line"]}" '
                             f'stroke-width="1.4"{dash}/>')
                pulses.append(f'<path class="p{ci}" d="{d}" pathLength="100" '
                              f'stroke="{colour}" stroke-width="3" '
                              f'stroke-linecap="round" stroke-dasharray="16 200" '
                              f'stroke-dashoffset="16" opacity="0"/>')
    svg.add(f'<g fill="none">{"".join(edges)}{"".join(pulses)}</g>')

    for ci, (label, num, colour, n, future) in enumerate(cols):
        a = ci * pp
        css.append(
            f"@keyframes n{ci}{{0%,{max(a - .01, 0):.2f}%{{opacity:.18}}"
            f"{a + 1:.2f}%{{opacity:1}}78%{{opacity:1}}90%,100%{{opacity:.18}}}}"
            f".n{ci}{{animation:n{ci} {T}s ease-out infinite}}")
        last = ci == len(cols) - 1
        r = 25 if last else 15
        for (x, y) in pos[ci]:
            dash = ' stroke-dasharray="5 5"' if future else ""
            svg.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{t["bg"]}" '
                    f'stroke="{colour}" stroke-width="3"{dash}/>')
            svg.add(f'<circle class="n{ci}" cx="{x:.1f}" cy="{y:.1f}" '
                    f'r="{r - 7}" fill="{colour}" opacity=".18"/>')
            if last:
                css.append(
                    f"@keyframes ring{{0%,{a:.2f}%{{transform:scale(1);opacity:0}}"
                    f"{a + .5:.2f}%{{opacity:.7}}{a + 14:.2f}%,100%"
                    f"{{transform:scale(2.1);opacity:0}}}}"
                    ".ring{animation:ring 7s ease-out infinite;"
                    "transform-box:fill-box;transform-origin:center}")
                svg.add(f'<circle class="ring" cx="{x:.1f}" cy="{y:.1f}" r="{r}" '
                        f'fill="none" stroke="{colour}" stroke-width="2" '
                        'opacity="0"/>')
        lx = pos[ci][0][0]
        if num:
            svg.text(lx, ny1 + 74, num, "mono", 15, t["muted"], anchor="middle")
        svg.text(lx, ny1 + 98, label, "semi", label_size,
                 t["muted"] if future else colour, anchor="middle")

    css.append("@media (prefers-reduced-motion:reduce){[class]{animation:none"
               "!important}[class^=n]{opacity:1!important}}")
    return svg.render()


# ────────────────────────────────────────────────────────────── stations ──

ROW_W, ROW_H, TRACK_X, STOP_Y = 960, 210, 52, 66


def _track(svg: Svg, t: dict, top: bool, bottom: bool) -> None:
    y0 = 0 if top else STOP_Y
    y1 = ROW_H if bottom else STOP_Y
    dots = []
    y = y0 + 7
    while y < y1:
        dots.append(f'<circle cx="{TRACK_X}" cy="{y}" r="2.6"/>')
        y += 14
    svg.add(f'<g fill="{t["line"]}">{"".join(dots)}</g>')


def station(fonts: Fonts, t: dict, i: int) -> str:
    L = LESSONS[i]
    c = t[L["color"]]
    svg = Svg(fonts, ROW_W, ROW_H, f'Lesson {L["num"]}: {L["title"]}. {L["text"]}')
    _track(svg, t, top=i > 0, bottom=True)
    svg.add(f'<circle cx="{TRACK_X}" cy="{STOP_Y}" r="17" fill="{t["page"]}" '
            f'stroke="{c}" stroke-width="4"/><circle cx="{TRACK_X}" '
            f'cy="{STOP_Y}" r="7" fill="{c}"/>')

    tx = 104
    svg.text(tx, STOP_Y + 10, L["num"], "display", 30, c, tracking=-0.5)
    svg.text(tx + 52, STOP_Y + 10, L["title"], "semi", 30, t["text"],
             tracking=-0.4)

    # code chip, right-aligned
    code = "".join(s for s, _ in L["code"])
    cw = fonts.width("mono", code, 16) + 36
    cx1 = ROW_W - 16
    cx0 = cx1 - cw
    svg.add(f'<rect x="{cx0:.1f}" y="{STOP_Y + 34}" width="{cw:.1f}" height="44" '
            f'rx="10" fill="{t["surface"]}" stroke="{t["line"]}"/>')
    svg.spans(cx0 + 18, STOP_Y + 62, L["code"], "mono", 16, t)

    y = STOP_Y + 52
    for s in svg.wrap(L["text"], "text", 19, cx0 - tx - 52 - 40):
        svg.text(tx + 52, y, s, "text", 19, t["muted"])
        y += 28
    fy = STOP_Y + 106
    for f in L["facts"]:
        svg.text(cx1, fy, f, "text", 16, t["muted"], anchor="end")
        fy += 24
    return svg.render()


def station_next(fonts: Fonts, t: dict) -> str:
    svg = Svg(fonts, ROW_W, 150, f'Lesson {NEXT["num"]}: coming soon')
    global ROW_H
    keep, ROW_H = ROW_H, 150
    _track(svg, t, top=True, bottom=False)
    ROW_H = keep
    svg.add(f'<circle cx="{TRACK_X}" cy="{STOP_Y}" r="17" fill="{t["page"]}" '
            f'stroke="{t["muted"]}" stroke-width="3" stroke-dasharray="5 5"/>')
    tx = 104
    svg.text(tx, STOP_Y + 10, NEXT["num"], "display", 30, t["muted"],
             tracking=-0.5)
    svg.text(tx + 52, STOP_Y + 10, NEXT["title"], "semi", 30, t["muted"],
             tracking=-0.4)
    svg.text(tx + 52, STOP_Y + 46, NEXT["text"], "text", 19, t["muted"])
    return svg.render()


# ────────────────────────────────────────────────────────────── notebook ──


def notebook(fonts: Fonts, t: dict) -> str:
    W, H = 960, 236
    svg = Svg(fonts, W, H, "In 1: code = agent.write('tidy up my files'). "
              "In 2: you.understand(code). Out 2: True")
    svg.add(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="16" '
            f'fill="{t["surface"]}" stroke="{t["line"]}" stroke-width="1.5"/>')
    svg.add(f'<rect x="1" y="1" width="6" height="{H - 2}" rx="3" '
            f'fill="{t["purple"]}"/>')
    gx, cx, size = 34, 150, 19
    rows = [
        ("In [1]:", [("code ", "text"), ("= ", "muted"), ("agent", "text"),
                     (".", "muted"), ("write", "fn"), ("(", "muted"),
                     ('"tidy up my files"', "str"), (")", "muted")],
         "# fast, and always sure"),
        ("In [2]:", [("you", "text"), (".", "muted"), ("understand", "fn"),
                     ("(code)", "text")], "# what these lessons teach"),
        ("Out[2]:", [("True", "teal")], None),
    ]
    y = 74
    for gutter, runs, comment in rows:
        svg.text(gx, y, gutter, "mono", size - 2, t["muted"])
        svg.spans(cx, y, runs, "mono", size, t)
        if comment:
            svg.text(W - 34, y, comment, "mono", size - 2, t["muted"],
                     anchor="end")
        y += 54
    return svg.render()


# ────────────────────────────────────────────────────────────────── main ──


README = ROOT / "profile" / "README.md"


def _picture(name: str, alt: str) -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" '
            f'srcset="{RAW}/{name}-dark.svg"><img alt="{escape(alt)}" '
            f'src="{RAW}/{name}-light.svg" width="100%"></picture>')


def path_block() -> str:
    """The stations, one line each with no blank lines, so the track joins."""
    lines = []
    for L in LESSONS:
        alt = f'Lesson {L["num"]}, {L["title"]}: {L["text"]}'
        lines.append(f'<a href="https://github.com/{ORG}/{L["repo"]}">'
                     f'{_picture("lesson-" + L["num"], alt)}</a>')
    lines.append(_picture("lesson-next", f'Lesson {NEXT["num"]} is being built.'))
    return "<div>\n" + "\n".join(lines) + "\n</div>"


def table_block() -> str:
    rows = ["| Lesson | Slides | Code and notebooks | Run without installing |",
            "| :-- | :-: | :-: | :-: |"]
    for L in LESSONS:
        colab = f'[Google Colab]({L["colab"]})' if L.get("colab") else ""
        rows.append(f'| **{L["num"]}** {L["title"]} '
                    f'| [Open](https://{ORG}.github.io/{L["repo"]}/) '
                    f'| [Repository](https://github.com/{ORG}/{L["repo"]}) '
                    f'| {colab} |')
    return "\n".join(rows)


def update_readme() -> None:
    """Rewrite what sits between <!-- name:start --> and <!-- name:end -->."""
    md = README.read_text(encoding="utf-8")
    for name, body in (("path", path_block()), ("table", table_block())):
        start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
        if start not in md or end not in md:
            raise SystemExit(f"{README}: markers {start} / {end} not found")
        head, rest = md.split(start, 1)
        _, tail = rest.split(end, 1)
        md = f"{head}{start}\n{body}\n{end}{tail}"
    README.write_text(md, encoding="utf-8")
    print(f"  {README.relative_to(ROOT)} updated")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fonts = Fonts()
    for old in OUT.glob("lesson-*.svg"):      # drop stations no longer listed
        old.unlink()
    for name, t in THEMES.items():
        t = dict(t, fn=t["purple"], str=t["orange"])
        files = {
            f"hero-{name}.svg": hero(fonts, t),
            f"notebook-{name}.svg": notebook(fonts, t),
            f"lesson-next-{name}.svg": station_next(fonts, t),
        }
        for i, L in enumerate(LESSONS):
            files[f'lesson-{L["num"]}-{name}.svg'] = station(fonts, t, i)
        for fname, body in files.items():
            (OUT / fname).write_text(body, encoding="utf-8")
            print(f"  {fname:28} {len(body) / 1024:6.1f} KB")
    update_readme()


if __name__ == "__main__":
    main()
