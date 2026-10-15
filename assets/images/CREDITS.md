# Image sources and credits

Written 2026-10-13. This file says only what the repo can show. Where something is
unknown it says **not recorded**; nothing here claims a permission that was not given.

## The three photos

| File (original, kept untouched) | What it shows | File date | Web copies (published) |
|---|---|---|---|
| `IMG_8489.jpg` | A person in a white t-shirt and maroon apron holding a tray of six tacos of sliced grilled beef and a plate of sautéed mushrooms | 2026-10-13 | `web/home-{480,800,1200}.jpg`, used in the Home hero |
| `IMG_8452.jpg` | Overhead view of one beef taco on a patterned plate | 2026-09-28 | `web/menu-{480,800,1200}.jpg`, used on the Menu page |
| `portrait.png` | A portrait of a man with dark wavy hair and a beard, in an olive-green henley sweater | 2026-10-13 | `web/our-story-{480,800,1176}.jpg`, used on the Our Story page |

## Where they came from

- **Supplied by the project author** and placed in `assets/images/` on 2026-10-13.
- All three are **phone screenshots** (1206 px wide). Interface controls are visible at
  their edges (a sound icon on `IMG_8452.jpg`, a round control on `IMG_8489.jpg`, a scroll
  handle on `portrait.png`), which is consistent with a capture from a social-media app.
  That is an observation, not a confirmed source.
- **Source (author's statement, 2026-10-15):** I found the photos on Instagram and supplied
  screenshots of them.
- **Not recorded:** which Instagram account or post, the post URL, the post date, the caption, and
  the photographer's name or credit line. The author should add them below.
- **Permission: not recorded.** Nothing in the repo shows that La Once Mil or any
  photographer gave permission to republish these photos. The author directed their use
  on this student prototype (not affiliated with La Once Mil; see the site footer). If
  permission cannot be confirmed, remove the photos and the `[PHOTO: ...]` lines and
  the site falls back to labelled placeholders. `notes/restaurant-research.md` records
  why public visibility is not reuse rights.
- **Not generated and not stock:** none of these images was created by an AI tool or
  taken from a stock library.

## People in the photos

- Nobody is identified. The person in `portrait.png` is **not identified from
  appearance**, and the site's caption says "Portrait; subject not identified." Do not
  add a name or a job title unless the original post or the person confirms it.
- The person in `IMG_8489.jpg` is partly out of frame in the original and is likewise not
  identified. The alt text describes only what is visible.

## How the web copies were made

`scripts/make_web_images.sh` (macOS `sips`, no new dependency) crops each screenshot
so its controls fall outside the picture, then saves JPEG copies at several widths. A crop
only removes pixels (no one-sided scaling), so nothing is stretched. Crop boxes, measured
on the original (height × width, from the top-left offset):

| Original | Crop | What was cut |
|---|---|---|
| `IMG_8489.jpg` | 1456 × 1206 from (0, 0) | bottom 50 px (round control) |
| `IMG_8452.jpg` | 1190 × 1206 from y = 290 | top 290 px (edge of two small bowls) and bottom 123 px (sound icon) |
| `portrait.png` | 1330 × 1176 from y = 20 | top 20 px (bar), bottom 63 px (control), right 30 px (scroll handle) |

The originals are never published; `cms publish` copies only `assets/images/web/`.

## To fill in (author)

- [ ] `IMG_8489.jpg`: post URL / date / caption / credit: ______
- [ ] `IMG_8452.jpg`: post URL / date / caption / credit: ______
- [ ] `portrait.png`: post URL / date / caption / credit, and whether the source names the person: ______
- [ ] Permission to use each photo, and from whom: ______
