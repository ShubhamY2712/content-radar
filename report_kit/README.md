# Report kit

Builds one self-contained HTML file per report: fonts, icons, styles, script and images are embedded, so the file opens offline and can be sent as a single attachment.

## Parts

| Part | What it is |
|---|---|
| `kit.css` | The look: warm paper, ink text, forest green and ochre accents, serif headings (Fraunces), sans body (IBM Plex Sans, with IBM Plex Sans Devanagari for Hindi). Colour roles are CSS variables at the top. |
| `kit.js` | One-time animations (bars grow, numbers count up, key lines get a highlight), the contents highlight, filters, and opening a linked collapsed section. Everything is off for readers who turn off motion. |
| `kit.py` | `render(layout, context)` builds the page; `icon(name)` inlines an icon; `image_uri(path)` embeds a resized image; `mark(text, phrase)` highlights a phrase; `scatter_map(points, x, y)` draws a two-axis map. |
| `layouts/base.html.j2` | Page shell: sticky contents on the left, reading column on the right. |
| `layouts/components.html.j2` | Building blocks: section head, stat strip, finding card, creative chip, logo or initials, comparison bar, table, idea card, gallery tile. |
| `layouts/content_radar_*.html.j2` | The Content Radar summary and detailed reports, built from the blocks above. |
| `fonts/` | Fraunces and IBM Plex (SIL Open Font License, licence files included). |
| `icons/phosphor-regular/` | 158 Phosphor icons, regular weight (MIT licence). Add more from the Phosphor set when a report needs them. |

## A new report type

1. Write a layout in `layouts/` that extends `base.html.j2` and uses the blocks in `components.html.j2`.
2. Write a small script that loads your data, builds the context (`page_title`, `side_title`, `side_sub`, `toc`, and what your layout needs) and calls `kit.render("<your layout>", context)`.
3. Keep words in a data file and layout in the template, so an agent can write the words and the script can be rerun.

`tools/render_html.py` is the worked example.
