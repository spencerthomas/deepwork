# Research: langchain-ai/docs design language (agent a2b8ef2d9a6596ca5, completed 2026-07-21)

Local clone of langchain-ai/docs: /tmp/claude-0/-home-user-deepwork/90ba5e0f-b1b7-5eb0-89f9-06836b29d757/scratchpad/lc-docs
Live captures in scratchpad: lc-home.html, lc-doc.html, 313ebeaa2aedc920.css

## Platform
- Mintlify, theme **"aspen"**, config `src/docs.json`. Site "Docs by LangChain".
- **Brand is BLUE now** (2025 rebrand): primary `#161F34`, light `#7FC8FF`, dark `#006DDD`; bg `#FFFFFF` / `#030710`. NOT the legacy green.
- Icons: **Tabler outline v3.44.0** (`icons.library: "tabler"`), 16px, CSS mask-image.
- Fonts: headings **TWK Lausanne** (self-hosted, COMMERCIAL — do not redistribute; h1 700, h2-h4 600), body **Inter 400**, mono **IBM Plex Mono** (brand guidelines name Aeonik Mono as true secondary, Plex Mono fallback).
- Code: catppuccin-latte (`#eff1f5`) / catppuccin-mocha (`#1e1e2e`), framed rounded-2xl outer + 14px inner, text-sm leading-6.
- Custom overrides: `src/style.css` (~26KB): callout palette (8 types w/ hexes), dark border fix `#4f5d73`, forced text colors.
- `.github/brand-guidelines.md` in repo = official palette: Dark Blue family #030710/#0D1322/#161F34/#2F4B68/#40668D, Blue #006DDD; Light Blue tints #7FC8FF→#F2FAFF; extended Plum #885270, Purple #504B5F, Peach #634643, Green #6E8900; 3 permitted gradients; "never pure black/white".

## Layout anatomy (all CONFIRMED from live HTML)
- Shell max-w **92rem**; content max-w **72rem**; navbar **h-14 (56px)** + tab row **h-10 (40px)** = 96px header; sidebar **18rem (288px)**; TOC rail **19rem** (incl 2.5rem gutter); column gap 48px (gap-x-12); content pad lg:pl-[5.5rem] pt-10.
- Navbar: logo h-6, product dropdown (h-8 rounded-xl), center search pill (h-9 max-w-sm rounded-full bg-gray-950/[0.03], ⌘K), right "Ask AI"/"GitHub" links, CTA `bg-primary-dark rounded-xl text-white text-sm font-medium`.
- Sidebar items: text-sm py-1.5 rounded-xl; hover bg-gray-600/5; **active: bg-primary/10 text-primary (dark: primary-light variants) + faux-bold text-shadow** `[-0.2px_0_0_currentColor,0.2px_0_0_currentColor]`.
- Links in prose: font-weight 600, 1px primary border-bottom (no text-decoration).
- Banner: min-h-10, bg-primary-dark, dismissible, `--banner-height` var.
- Radii: icon tile 8px, interactive 12px (rounded-xl), selector 13.6px, code inner 14px, frames 16px (rounded-2xl), search pill full.
- Gray scale (Mintlify machine-derived from primary — regenerate if hue changes): 50 #F3F3F4, 100 #EEEEEF, 200 #DFDFE0, 300 #CECECF, 400 #9F9FA0, 500 #707071, 600 #505051, 700 #3F3F40, 800 #262626, 900 #171718, 950 #0A0B0B.
- RGB-triplet CSS vars pattern: `--primary: 22 31 52` used as `rgb(var(--primary) / <alpha>)`.

## Full token set + Tailwind snippet
(See agent report — complete CSS custom properties + tailwind.config captured; reproduce in UI spec doc. Includes navbar/tabs/sidebar/main/search/CTA class recipes.)

## Trademark / licensing cautions
- LANGCHAIN = USPTO reg. 7657514 (Jan 2025, LangChain Inc.). Do NOT reuse name/wordmark/logos in unaffiliated OSS. Layout + token structure freely copyable.
- TWK Lausanne + Aeonik Mono commercial. Safe OFL stack: Inter 600/700 (or Instrument Sans / Public Sans) headings + Inter body + IBM Plex Mono code.
- Distinct brand hues advisable; keep the structure (primary/light/dark triplets + gray scale + bg pair).

## Signature details worth copying
RGB-triplet vars w/ alpha; faux-bold active states; bg-primary/10 active pills; rounded-full search; 1px border-bottom links; scroll-fade masks on tabs/sidebar; dismissible banner w/ height var; navigation.products → menu (icon+description) → tabs/dropdowns → groups → pages model; Python↔TS dropdown w/ sessionStorage page-equivalent switching; contextual "Copy page" menu (md/llms.txt/claude/cursor).

## Open questions
- Aspen theme internals (drilldown anim, search modal) need browser inspection for pixel-exact copy.
- Regenerate grays if primary hue changes.
- Dark elevated-surface values beyond #0D1322/#161F34 — use brand guidelines.
