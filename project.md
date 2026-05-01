---
project: ProjectsMD Dashboard
status: build
created: 2026-04-30
updated: 2026-04-30
owner: Adam Manning
agent: ''
tags: []
---

## What This Is

Production-ready Hermes Agent dashboard plugin for ProjectsMD — visual project
browser with mutation UI, agent orchestration, quality gates, and GitHub integration.
42+ API routes, 74 tests, CI-passing. 23 production polish gaps identified in
readiness review (2026-04-30).

## Core Value

Agentic project management

## Context

<!-- Who needs this? What's the current situation? Any prior attempts? -->

## Constraints

- **Tech Stack**: 
- **Performance**: 
- **Compatibility**: 

## Requirements

### Validated

<!-- Confirmed requirements with version tracking -->
<!-- Format: - ✓ Description — v0.1 -->

### Active

<!-- Current requirements being worked on -->
<!-- Format: - [ ] Description -->

### Out of Scope

<!-- Explicitly excluded items with rationale -->
<!-- Format: - Description — reason -->

## Current State

**Phase:** build
**Last completed:** 36/36 implementation milestones + CI fix
**In progress:** Production readiness review — 23 gaps identified
**Next action:** Fix XSS on line 234 (highest severity)
**Blockers:** none
**Notes:** 74 tests green, ruff clean, CI passing. Frontend needs polish pass.
## Architecture

<!-- High-level design, data flow, file structure -->

## Key Decisions

| Decision                                                                                                            | Rationale                                                                                                  | Outcome     |
|---------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|-------------|
| Production readiness baseline: 74/74 tests, ruff clean, CI green, but 23 UX/branding/safety gaps identified         | Tests pass but frontend has no production polish — alert() UX, XSS vector, no accessibility, no branding   | — Pending   |
| Phase coloring strategy: use 5 distinct badge colors for DEFINE/DESIGN/BUILD/VERIFY/SHIP instead of generic outline | Users scan phases visually; color coding is free cognitive speedup. Matches Hermes design system           | — Pending   |
| Orchestrator runs need live polling panel, not alert() — show status badge, last N lines, kill button               | Orchestrator is the killer feature. alert() is a death sentence for YC-quality perception                  | — Pending   |
| Use SDK.theme or CSS variables for all colors — never hardcode Tailwind classes                                     | Hermes supports theming. Hardcoded colors break in dark mode and violate Nous branding guidelines          | — Pending   |
## Tasks

### Phase: DEFINE

- [ ] Identify target users and use cases
- [ ] Define requirements
- [ ] Identify constraints

### Phase: DESIGN

- [ ] Choose technology stack
- [ ] Design architecture
- [ ] Define data models

### Phase: BUILD

- [ ] Project setup
- [ ] Core implementation
- [ ] Error handling


- [ ] Task 2: No loading states on action buttons — no spinner/disabled state during API calls


- [ ] Task 3: Queue list uses innerHTML string concatenation — XSS vector on line 234
- [ ] Task 1: Mutation UX is fragile — alert() + location.reload() on every action instead of inline feedback


- [ ] Task 5: No aria labels or keyboard navigation — accessibility gap
- [ ] Task 4: No input validation on prompt() dialogs — should use modal forms


- [ ] Task 7: No rate limiting or debounce on rapid mutation clicks — can spam backend
- [ ] Task 6: No mobile/tablet responsive testing — only xl: breakpoints


- [ ] Task 9: No backend healthcheck integration — UI shows generic error when backend down
- [ ] Task 8: Error boundary is barebones — no stack trace toggle, no copy-to-clipboard, no report option


- [ ] Task 11: API_BASE variable uses hardcoded /api/plugins/projectsmd — should use SDK-provided prefix
- [ ] Task 10: Plugin manifest missing min Hermes version declaration


- [ ] Task 13: No Hermes logo or brand color in the UI header
- [ ] Task 12: No plugin configuration schema declared for Hermes plugin registry


- [ ] Task 15: Color tokens should inherit from Hermes theme system, not hardcoded CSS classes
- [ ] Task 14: Header says 'Projects' not 'Hermes Projects' — no brand association


- [ ] Task 17: No project completion badge — only percentage bar, no 'Complete' or 'Shipped' visual indicator
- [ ] Task 16: No link to Hermes docs/settings from dashboard UI


- [ ] Task 19: No subagent completion tracking in UI — no concept of subagent hierarchy
- [ ] Task 18: No orchestrator run status panel — no live output, no status indicator, launch just alerts


- [ ] Task 21: Task done/blocked use only text markers (✓/○) — no color coding, no icons, no progress animation
- [ ] Task 20: Phase badges all look the same — outline variant used for all, no color distinction (SHIP vs BUILD vs DEFINE)


- [ ] Task 23: No run history or timeline view — can't see past orchestrator runs
- [ ] Task 22: No transition animations for state changes — full page reload feels jarring
### Phase: VERIFY

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing

### Phase: SHIP

- [ ] Documentation
- [ ] Release packaging
- [ ] Tag release
## Discoveries

<!-- New information discovered during development -->

- XSS vector on line 234: queue list builds innerHTML from user-provided diff content with no escaping
- Hermes SDK provides SDK.theme, SDK.icons, SDK.components.Toast — none are used. Toast would replace alert() UX
- Hermes SDK has polling primitives — should use SDK.createPoller() instead of fetch loop, would enable live run status
- Phase colors: Hermes design uses indigo(DEFINE), amber(DESIGN), emerald(BUILD), sky(VERIFY), violet(SHIP). These map to 5 Badge variants.
- Hermes plugin registration: __HERMES_PLUGINS__.register() supports priority, metadata, and min_version — only name is provided currently
## References

<!-- Links to documentation, examples, related projects -->

## Session Log

<!-- Date-stamped development entries -->
<!-- Format: - **YYYY-MM-DD** — Description. (duration) -->
