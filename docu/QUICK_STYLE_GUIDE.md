# NormScout Quick Style Guide

**Colors:** Use `#3869FA` (brand), `#2048D5` (headings), `#448CF7` (buttons/hover), `#666666` (body text).

**Spacing:** `16px` (default), `24px` (sections), `48px` (major gaps) - or use `var(--spacing-sm/md/xl)`.

**Page Setup:** Extend `base.html` for app pages, use standalone HTML for legal/contact pages, wrap content in `<div class="dashboard-container"><div class="container">`.

**Buttons:** `btn btn-accent` (primary CTA), `btn btn-primary` (secondary), `btn btn-danger` (delete), `btn btn-outline` (cancel).

**Cards:** Use `dashboard-section` for sections, `workspace-card` for grid items, `step-card` for features.

**Grids:** `workspaces-grid` (auto-fit cards), `steps-grid` (2-4 columns), add hover: `transform: translateY(-2px)` + `box-shadow: var(--shadow-md)`.

**Forms:** `input-field` class for inputs/textareas, wrap in `input-group` with button for inline layout.

**States:** `loading-state` (spinner), `empty-state` (icon + text + CTA), `error-state` (error icon + message).

**Responsive:** Mobile-first, breakpoints at `768px` (tablet) and `1024px` (desktop), grids auto-stack.
