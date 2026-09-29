# Client brief: La Once Mil, Lomas de Chapultepec, Mexico City

## Why this client

I picked this restaurant because the Michelin-star story is compelling: a taqueria — a
category of restaurant normally associated with cheap, fast street food — won a Michelin
star in 2026, the only taquería to hold that distinction. That tension (a $20 wagyu taco next
to a genre built on $1 street tacos) is a strong hook for a "what can I eat here, where is it,
when is it open" public site, and the restaurant's real story (chef César de la Parra
deliberately elevating a street-food format he grew up on) gives the "Our Story" page
something specific to say instead of generic restaurant copy.

**Scope note:** this project models only the flagship location — Monte Everest 780, Lomas
de Chapultepec — the Michelin-starred address. The restaurant also operates a second Mexico
City branch (Roma Norte) and, as of very recently (Sept 2026), a Madrid location; both are
explicitly out of scope. See `notes/restaurant-research.md` for full sourcing and the
naming decision (site uses "La Once Mil," the restaurant's own verified branding; an
earlier draft of this brief used "Tacos La Oncemil," which was corrected on 2026-09-28).

## Who runs the site, and how comfortable are they with computers?

**Proposed assumption, not a verified fact** (I have not contacted the restaurant): the site
is modeled as run by the owner, César de la Parra, posting everything himself. He's a working
chef running a 55-seat, ~80-staff restaurant — comfortable enough to run Instagram and
TikTok accounts personally, but with no patience for a complicated publishing workflow. He
needs to post fast between service, not fight with a CMS. This means the editor UI has to be
simple even though, today, there's only one real user.

The CMS still needs two enforced roles (admin/editor) per the assignment's fixed
requirements — the brief models a plausible future where a manager or social-media hire gets
an editor account without touching user management, permanent-page content (Home, Menu, Our
Story — which includes the address/hours/directions on Home), or publishing.

## Who reads it, and what are they usually trying to find?

Two kinds of visitors, inferred from the restaurant's real profile (no reservations, walk-in
only, high foot traffic from the Michelin attention, no functioning official website today):

- **First-time visitors drawn by the Michelin coverage**, wanting to know: what's the
  signature dish, what does it cost, where exactly is it, when is it open, is a reservation
  needed (no).
- **Repeat/local visitors** wanting quick answers: today's hours, any seasonal menu news,
  confirmation the place hasn't moved.

## What's broken about how they do it now?

Verified from research: the restaurant has no functioning official website (`laoncemil.com`
exists but shows only "under construction"). Its entire online presence is Instagram,
TikTok, and a Linktree — none of which answer "where and when" quickly, and all of which bury
that information under a scrolling feed. Someone who doesn't already follow the account has
no fast way to get the address and hours without digging through an Instagram bio.

## What would make them say "this is better"?

A page that says, in one glance: what the signature dishes are, that it's walk-in only
(setting the right expectation before someone shows up expecting to book), the exact address
and hours, and a way to see it's a real, currently-open, currently-relevant place (recent
announcements) without needing to already follow the Instagram.

## What must not happen

**This site must never imply that Tacos La Oncemil / La Once Mil commissioned, endorsed, or
was involved in building this project.** It is a student prototype built for a class
assignment using publicly available, verified information. Any demonstration content (sample
announcements, seed data) must be clearly labeled as such, not presented as if the restaurant
posted it.

## Confirmed decisions (2026-09-28, in `/grill-with-docs`)

- **Site display name is "La Once Mil"** — the restaurant's own verified branding.
  (Corrects the earlier "Tacos La Oncemil" spelling used when this brief was started;
  that was not an intentional name choice. See `notes/restaurant-research.md`.)
- **Publishing is admin-only.** Only the manager/admin role can publish content live;
  the demo editor can create and edit announcement drafts but cannot publish, cannot
  edit permanent pages (Home, Menu, Our Story), and cannot manage users. The
  admin can do everything. This is a class prototype modeling a hypothetical future
  hire, not real restaurant staff.
- **Demo accounts are fictional, not the real owner.** Seed users are named
  **"Demo Manager"** (admin) and **"Demo Editor"** (editor) — required to demonstrate
  both roles for grading, but explicitly not claiming to be César de la Parra or any
  real staff member.
- **Homepage priority order: address, hours, directions first.** Of the "what/where/when"
  facts a first-time visitor needs, address/hours/directions rank above signature-dish
  or walk-in-only copy on the homepage specifically (those still belong on the page,
  just not the top fold).
- **Contact method is phone only.** No contact form, no email address surfaced to
  customers — a phone number is the one channel offered for reaching the restaurant.
- **Menu is one ordinary Markdown page** (dish names and descriptions), not a
  structured menu/pricing database. No unverified peso prices are included, per
  `notes/restaurant-research.md`'s pricing caveat.
- **News/announcements may include one real, dated item** — the Michelin star
  announcement, since the Michelin Guide page directly confirms the exact distinction
  ("One MICHELIN Star") and attributes it to the Lomas de Chapultepec address
  specifically (see `notes/restaurant-research.md`). Any other seed announcements are
  invented sample content and must be clearly labeled as demo, not real restaurant
  posts.
- **Images: placeholders now, real photos intended for the final version.** Build
  proceeds today with clearly labeled placeholders (e.g. `[PLACEHOLDER: storefront
  photo]`) so nothing blocks on photo access. See "Image tracker" below for what's
  still needed before final.

## Image tracker (placeholders in use until these are supplied)

| Needed for | Status | Notes |
|---|---|---|
| Homepage hero image | Placeholder | Storefront or signature dish shot, Lomas de Chapultepec location only |
| Menu page image(s) | Placeholder | Food shots; no prices, per pricing caveat |
| Our Story image | Placeholder | Chef/kitchen or storefront shot |
| News/announcement images (optional, per post) | Placeholder | Only if a specific post needs one |

Per `notes/restaurant-research.md`: the three photos found in the Michelin article are
credited "© La Once Mil" (editorial credit, not a republishing license) and are **not
cleared for use**. Real photos must come from the user's own Instagram pulls (with
post date/caption/credit noted) or the user's own photography — not these Michelin
article images, and not AI-generated or stock substitutes.

## Page structure (2026-09-28, in `/grill-with-docs`)

- **Home covers visiting information entirely** — verified address, hours, a
  directions link, and a prominent Call button live on Home itself. There is **no
  separate Visit Us page**; the earlier assumption elsewhere in this brief of a
  standalone Visit Us/Hours page is superseded by this decision.
- **Permanent pages are Home, Menu, and Our Story.** Only the admin can edit them.
  **News** is the list of published posts (the "Posts" capability), which the editor
  can draft and the admin can publish.
- **Publishing marks content published in the local CMS only.** The public GitHub
  Pages site does not update automatically — it reflects the new state only after
  `cms publish` exports to `site/` and that export is deployed to Pages. "Published"
  and "live on the public site" are two different moments.
- **Every published page, including Home, must be reachable through navigation.**
  Home is the entry point rather than a separate nav link, but Menu, Our Story, and
  News must all be linked from it (and from each other) so no published content is
  an orphan page.

## Still open

None — `/grill-with-docs` frontier is closed as of 2026-09-28. Proceed to `/to-spec`.
