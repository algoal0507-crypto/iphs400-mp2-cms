# CONTEXT.md glossary

Filled in from the `/grill-with-docs` session, 2026-09-28. See `notes/client-brief.md`
and `notes/restaurant-research.md` for the sourcing and reasoning behind each decision.

| Term | Meaning in this project |
|---|---|
| **La Once Mil** | The site's display name — the restaurant's own verified branding. Supersedes the earlier "Tacos La Oncemil" spelling used before this session, which was not an intentional name choice. |
| **Flagship location** | The one restaurant location this project models: Monte Everest 780, Lomas de Chapultepec, Mexico City — the Michelin-starred address. Roma Norte and Madrid locations are explicitly out of scope and must never appear on the site. |
| **Demo Manager** | The seeded **admin** account for grading. Fictional — does not represent the real owner (César de la Parra) or any real staff. Can edit permanent pages, manage users, and publish. |
| **Demo Editor** | The seeded **editor** account for grading. Fictional. Can create and edit **News** drafts only — cannot publish, cannot edit permanent pages, cannot manage users. |
| **Permanent pages** | Home, Menu, and Our Story — the site's "Pages" capability. Admin-only to edit. Appear in public navigation (except Home, which is implicit). |
| **News** | The site's "Posts" capability — draft/published announcements with title, slug, Markdown body, author, timestamps. Editor drafts; admin publishes. |
| **Publish** | The admin-only action that marks a draft (News post or a permanent page edit) as published **in the local CMS**. The editor role cannot perform this action under any content type. Publishing is not the same as the public site updating — the GitHub Pages site only reflects the change after `cms publish` exports to `site/` and that export is deployed. |
| **Navigation reachability** | Every published page, including Home, must be reachable by clicking through the public site's navigation — no published page is an orphan with no link pointing to it. |
| **Visiting information** | Verified address, hours, a directions link, and a prominent Call button — lives entirely on Home. There is no separate Visit Us page. |
| **Menu (page)** | One ordinary Markdown permanent page listing dish names and descriptions. No prices (no verified peso pricing exists) and no structured menu/pricing database — deliberately out of scope. |
| **Placeholder image** | A clearly labeled stand-in image (e.g. `[PLACEHOLDER: storefront photo]`) used until a real, rights-cleared photo is supplied. Tracked in `notes/client-brief.md`'s image tracker. Never substituted with AI-generated or stock images. |
| **Michelin item** | The one real, dated news item seed content may include — the Michelin star announcement — because the Michelin Guide page directly confirms the exact distinction ("One MICHELIN Star") and attributes it to the flagship (Lomas de Chapultepec) address specifically. Any other seeded News content is invented sample content and must be clearly labeled as demo. |
