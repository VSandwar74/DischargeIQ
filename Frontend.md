# DischargeIQ — Frontend Design Principles

**Companion to:** DischargeIQ Product Design Doc v1.0
**Purpose:** Design system reference for Claude Code when building the case manager dashboard and any user-facing UI

---

## 1. Design System: IBM Carbon

DischargeIQ's frontend is built on **IBM Carbon Design System v11** — IBM's open-source design system. This is non-negotiable for two reasons: it signals platform alignment to IBM stakeholders reviewing the capstone, and it gives us production-grade accessible components out of the box.

**Install:**
```bash
npm install @carbon/react @carbon/styles @carbon/icons-react
```

**Font:** IBM Plex (Sans for UI, Mono for data/codes)
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
```

---

## 2. Color System

### Primary Palette — IBM Blue + Neutral Gray

Matches the team's existing presentation deck (blue/dark/white) while staying within Carbon's token system.

| Role | Token | Hex | Usage |
|------|-------|-----|-------|
| **Primary action** | `$interactive` | `#0f62fe` (Blue 60) | Buttons, links, active states, primary CTAs |
| **Primary hover** | `$interactive-hover` | `#0353e9` (Blue 70) | Button hover, link hover |
| **Primary active** | `$interactive-active` | `#002d9c` (Blue 80) | Button pressed state |
| **Background** | `$background` | `#ffffff` (White) | Page background (White theme) |
| **Layer 01** | `$layer-01` | `#f4f4f4` (Gray 10) | Cards, panels, table rows |
| **Layer 02** | `$layer-02` | `#e0e0e0` (Gray 20) | Nested containers, secondary panels |
| **Text primary** | `$text-primary` | `#161616` (Gray 100) | Headings, body text |
| **Text secondary** | `$text-secondary` | `#525252` (Gray 70) | Labels, descriptions, timestamps |
| **Text placeholder** | `$text-placeholder` | `#a8a8a8` (Gray 40) | Input placeholders |
| **Border subtle** | `$border-subtle` | `#e0e0e0` (Gray 20) | Dividers, card borders |
| **Border strong** | `$border-strong` | `#8d8d8d` (Gray 50) | Input borders, table borders |

### Semantic / Status Colors

These map directly to DischargeIQ workflow states:

| Status | Token | Hex | Workflow Meaning |
|--------|-------|-----|------------------|
| **Success** | `$support-success` | `#24a148` (Green 60) | Auth approved, placement confirmed, discharged |
| **Warning** | `$support-warning` | `#f1c21b` (Yellow 30) | Auth pending >24hrs, observation status flag |
| **Error** | `$support-error` | `#da1e28` (Red 60) | Auth denied, placement declined, escalation needed |
| **Info** | `$support-info` | `#0043ce` (Blue 70) | New workflow initiated, status update |

### Agent Identity Colors

Each of the three agents gets a distinct accent for visual differentiation in the dashboard. These are drawn from Carbon's extended palette and match the presentation deck's three-column product slide:

| Agent | Color | Hex | Usage |
|-------|-------|-----|-------|
| **Prior Authorization** | Blue 60 | `#0f62fe` | Agent status badges, timeline markers, card accent borders |
| **Placement Coordinator** | Teal 50 | `#009d9a` | Agent status badges, facility match cards |
| **Compliance & Governance** | Purple 60 | `#8a3ffc` | Audit trail markers, compliance badges |

### CSS Variables (root)

```css
:root {
  /* Core IBM Blue */
  --cds-interactive: #0f62fe;
  --cds-interactive-hover: #0353e9;
  --cds-interactive-active: #002d9c;

  /* Backgrounds */
  --cds-background: #ffffff;
  --cds-layer-01: #f4f4f4;
  --cds-layer-02: #e0e0e0;

  /* Text */
  --cds-text-primary: #161616;
  --cds-text-secondary: #525252;
  --cds-text-placeholder: #a8a8a8;

  /* Borders */
  --cds-border-subtle: #e0e0e0;
  --cds-border-strong: #8d8d8d;

  /* Status */
  --cds-support-success: #24a148;
  --cds-support-warning: #f1c21b;
  --cds-support-error: #da1e28;
  --cds-support-info: #0043ce;

  /* Agent accents */
  --agent-prior-auth: #0f62fe;
  --agent-placement: #009d9a;
  --agent-compliance: #8a3ffc;

  /* Typography */
  --font-sans: 'IBM Plex Sans', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
```

---

## 3. Typography

Carbon's type scale using IBM Plex. All sizes in rem (base 16px).

| Token | Size | Weight | Line Height | Use |
|-------|------|--------|-------------|-----|
| `heading-05` | 2rem (32px) | 400 | 40px | Page titles ("Discharge Dashboard") |
| `heading-04` | 1.75rem (28px) | 400 | 36px | Section headers |
| `heading-03` | 1.25rem (20px) | 400 | 28px | Card titles, panel headers |
| `heading-02` | 1rem (16px) | 600 | 22px | Subsection labels |
| `body-long-01` | 0.875rem (14px) | 400 | 20px | Primary body text, descriptions |
| `body-compact-01` | 0.875rem (14px) | 400 | 18px | Table cells, dense lists |
| `label-01` | 0.75rem (12px) | 400 | 16px | Form labels, metadata, timestamps |
| `code-01` | 0.75rem (12px) | 400 Mono | 16px | Tracking numbers, IDs, FHIR refs |

### Rules
- **Never use Arial, Inter, Roboto, or system fonts.** IBM Plex Sans only.
- Patient names and IDs: `IBM Plex Sans 600` (semibold)
- Tracking numbers, auth IDs, FHIR references: `IBM Plex Mono 400`
- Status labels: `IBM Plex Sans 500` (medium), uppercase, `label-01` size
- Numerical data (days, scores, dollar amounts): `IBM Plex Sans 600`, slightly larger than surrounding body text for scanability

---

## 4. Layout & Spacing

### Grid
Carbon 16-column grid with responsive breakpoints:

| Breakpoint | Width | Columns | Margin | Gutter |
|------------|-------|---------|--------|--------|
| `sm` | 320px | 4 | 16px | 16px |
| `md` | 672px | 8 | 16px | 16px |
| `lg` | 1056px | 16 | 16px | 16px |
| `xlg` | 1312px | 16 | 16px | 16px |
| `max` | 1584px | 16 | 24px | 16px |

### Spacing Scale (Carbon)
Use Carbon's spacing tokens — do not use arbitrary pixel values:

| Token | Value | Use |
|-------|-------|-----|
| `$spacing-01` | 2px | Micro adjustments |
| `$spacing-02` | 4px | Inline icon gaps |
| `$spacing-03` | 8px | Tight padding (badges, tags) |
| `$spacing-04` | 12px | Component internal padding |
| `$spacing-05` | 16px | Standard padding, card padding, form field spacing |
| `$spacing-06` | 24px | Section spacing, card margins |
| `$spacing-07` | 32px | Panel padding, major section gaps |
| `$spacing-08` | 40px | Page-level vertical rhythm |
| `$spacing-09` | 48px | Large section separators |

### Dashboard Layout

```
┌──────────────────────────────────────────────────────┐
│  UI Shell (Header)                          Blue 80  │
│  Logo: DischargeIQ    Nav: Dashboard | Patients      │
├────────┬─────────────────────────────────────────────┤
│ Side   │  Main Content Area                          │
│ Panel  │                                             │
│        │  ┌─────────────────────────────────────┐    │
│ Patient│  │  Summary Cards (3-up)               │    │
│ List   │  │  Auth Pending | Placed | Discharged │    │
│        │  └─────────────────────────────────────┘    │
│ Filter │  ┌─────────────────────────────────────┐    │
│ by:    │  │  Active Workflows Table             │    │
│ Status │  │  Patient | Status | Auth | Facility │    │
│ Payer  │  │  ... sortable, filterable ...       │    │
│ Agent  │  └─────────────────────────────────────┘    │
│        │  ┌─────────────────────────────────────┐    │
│        │  │  Detail Panel (selected patient)    │    │
│        │  │  Timeline | Agent Actions | Docs    │    │
│        │  └─────────────────────────────────────┘    │
└────────┴─────────────────────────────────────────────┘
```

- **UI Shell:** Carbon `<HeaderGlobal>` component, background `Blue 80` (#002d9c) — matches IBM product look
- **Side Panel:** `Gray 10` background (#f4f4f4), 256px width, collapsible
- **Main Content:** `White` background, 16-col grid
- **Cards:** `White` background, `$border-subtle` border, `$spacing-05` padding, 4px border-radius

---

## 5. Component Patterns

### 5.1 Workflow Status Tags

Use Carbon's `<Tag>` component with semantic colors:

| Workflow State | Tag Type | Color |
|----------------|----------|-------|
| `INITIATED` | Blue | `#0f62fe` bg, white text |
| `AUTH_PENDING` | Yellow/Warning | `#f1c21b` bg, `#161616` text |
| `AUTH_APPROVED` | Green/Success | `#24a148` bg, white text |
| `AUTH_DENIED` | Red/Error | `#da1e28` bg, white text |
| `PLACEMENT_SEARCHING` | Teal | `#009d9a` bg, white text |
| `PLACEMENT_CONFIRMED` | Green | `#24a148` bg, white text |
| `ESCALATED` | Purple/High contrast | `#8a3ffc` bg, white text |
| `DISCHARGED` | Gray | `#525252` bg, white text |

### 5.2 Patient Workflow Card

```jsx
<Tile className="workflow-card">
  <div className="card-header">
    <h4 className="patient-name">Jane Smith</h4>
    <Tag type="blue">AUTH_PENDING</Tag>
  </div>
  <div className="card-meta">
    <span className="label">MRN:</span>
    <code>12345678</code>
    <span className="label">Payer:</span>
    <span>Aetna Medicare</span>
    <span className="label">LOS:</span>
    <span className="highlight">4 days</span>
  </div>
  <div className="agent-status">
    <StatusIcon agent="prior-auth" status="pending" />
    <StatusIcon agent="placement" status="searching" />
    <StatusIcon agent="compliance" status="ok" />
  </div>
  <div className="card-actions">
    <Button kind="primary" size="sm">View Details</Button>
    <Button kind="ghost" size="sm">Escalate</Button>
  </div>
</Tile>
```

### 5.3 Agent Timeline

A vertical timeline showing agent actions on a patient's discharge workflow. Each entry is color-coded by agent.

```
  ●─── Prior Auth Agent submitted PA to Aetna Medicare     10:32 AM
  │    via Availity X12 278 • Tracking #AET-2026-04891
  │
  ●─── Placement Agent sent referrals to 3 SNFs            10:33 AM
  │    Maple Grove (accepted) • Sunrise (pending) • Oak...
  │
  ●─── Compliance Agent flagged observation status          10:35 AM
  │    ⚠ Patient is observation — traditional Medicare
  │    SNF benefit does not apply. Notify UR team.
  │
  ○─── Awaiting PA response from Aetna Medicare             Now
       Estimated: 24-72 hrs based on historical data
```

- Blue dots for Prior Auth events
- Teal dots for Placement events
- Purple dots for Compliance events
- Hollow dot for pending/awaiting states
- Timestamps right-aligned in `label-01` style, `$text-secondary` color
- Tracking numbers in `IBM Plex Mono`

### 5.4 Summary Stat Cards (Top of Dashboard)

Three large KPI cards at the top:

```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Auth Pending     │  │  Placed Today    │  │  Avg Delay       │
│       12          │  │       7          │  │     1.8 days     │
│  ▲ 3 from yday    │  │  ▼ 2 from yday   │  │  ▼ 0.4 from last │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

- Big number: `heading-04` (28px), `$text-primary`, `IBM Plex Sans 300` (light weight for large numerals)
- Label: `label-01`, `$text-secondary`
- Delta indicator: Green arrow down (improvement) or red arrow up (regression), `body-compact-01`
- Card: `White` bg, `$border-subtle` border, `$spacing-06` padding

### 5.5 Data Table

Use Carbon's `<DataTable>` with sorting and filtering:

| Column | Width | Alignment | Format |
|--------|-------|-----------|--------|
| Patient Name | 20% | Left | Semibold, linked |
| MRN | 10% | Left | `IBM Plex Mono` |
| Payer | 15% | Left | Normal |
| Status | 12% | Left | `<Tag>` component |
| Auth Submitted | 12% | Left | Relative ("2h ago") |
| Facility Match | 18% | Left | Facility name or "Searching..." |
| Avoidable Days | 8% | Right | Number, red if >2 |
| Actions | 5% | Center | Overflow menu |

---

## 6. Interaction Patterns

### Human-in-the-Loop Surfaces

DischargeIQ is a decision-support tool, not an autonomous system. Every agent action that affects a patient requires case manager confirmation. The UI must make this clear:

1. **Agent recommendations appear as suggestions, not completed actions.** Use language like "Recommended next step" with explicit Approve / Modify / Reject buttons.

2. **Critical alerts use Carbon's `<InlineNotification>` (error kind)** for observation status flags, denials, and escalations. These must be dismissable only after acknowledgment.

3. **Approval confirmations use Carbon's `<Modal>`** with a summary of what the agent will do. Case manager must click "Confirm" before the agent proceeds.

### Notification Priority

| Priority | Treatment | Example |
|----------|-----------|---------|
| **Urgent** | Red banner, persist until dismissed | Auth denied — appeal window closes in 48hrs |
| **Action needed** | Yellow inline notification | PA pending >24hrs — consider follow-up |
| **Informational** | Blue toast, auto-dismiss 8s | Referral accepted by Maple Grove SNF |
| **Success** | Green toast, auto-dismiss 5s | Patient discharged successfully |

---

## 7. Accessibility

Carbon is WCAG 2.1 AA compliant by default. Maintain this by following these rules:

- **Color contrast:** All text meets 4.5:1 (normal) or 3:1 (large text) against its background. The palette above is pre-validated for this.
- **Don't use color alone** to convey status — always pair with text labels, icons, or patterns.
- **Keyboard navigation:** All interactive elements reachable via Tab. Focus ring: 2px `$focus` border (Blue 60).
- **Screen reader:** Use Carbon's built-in ARIA attributes. Add `aria-live="polite"` regions for agent status updates.
- **Motion:** Respect `prefers-reduced-motion`. All animations should be optional.

---

## 8. Dark Theme (Optional — Post-MVP)

If the team wants a dark mode for presentations or demo environments, Carbon's `Gray 100` theme maps cleanly:

| Token | Light (White) | Dark (Gray 100) |
|-------|---------------|-----------------|
| `$background` | `#ffffff` | `#161616` |
| `$layer-01` | `#f4f4f4` | `#262626` |
| `$text-primary` | `#161616` | `#f4f4f4` |
| `$text-secondary` | `#525252` | `#c6c6c6` |
| `$interactive` | `#0f62fe` | `#4589ff` (Blue 50) |
| `$border-subtle` | `#e0e0e0` | `#393939` |

Switch via Carbon's inline theming:
```jsx
import { Theme } from '@carbon/react';
<Theme theme="g100">{/* dark content */}</Theme>
```

---

## 9. Presentation Alignment

The dashboard design intentionally mirrors the existing capstone deck aesthetics:

| Deck Element | Dashboard Equivalent |
|-------------|---------------------|
| Blue header bar on slides | `Blue 80` UI Shell header |
| White slide backgrounds | `White` main content area |
| Gray info boxes | `Gray 10` side panel and cards |
| Three-column product slide (blue/teal/purple agents) | Agent accent colors on timeline, badges, status indicators |
| Calibri body text on slides | IBM Plex Sans (Carbon standard, visually similar weight and proportions) |
| Dark footer with slide numbers | `Gray 100` footer bar with navigation context |

When demoing the product alongside the pitch deck, the visual language should feel like a single cohesive experience — the deck introduces the concept, the dashboard proves it works.

---

## 10. File Structure for Claude Code

```
src/
├── styles/
│   ├── _tokens.scss          # CSS custom properties (Section 2)
│   ├── _typography.scss      # IBM Plex imports + type scale
│   └── global.scss           # Carbon imports + overrides
├── components/
│   ├── Shell/                # UI Shell (header, sidenav)
│   ├── Dashboard/
│   │   ├── SummaryCards.jsx   # KPI cards (Section 5.4)
│   │   ├── WorkflowTable.jsx  # DataTable (Section 5.5)
│   │   └── PatientDetail.jsx  # Detail panel + timeline
│   ├── Workflow/
│   │   ├── StatusTag.jsx      # Semantic status tags (Section 5.1)
│   │   ├── AgentTimeline.jsx  # Agent action timeline (Section 5.3)
│   │   └── WorkflowCard.jsx   # Patient workflow card (Section 5.2)
│   ├── Notifications/
│   │   └── AlertBanner.jsx    # InlineNotification wrappers
│   └── Modals/
│       └── ConfirmAction.jsx  # Human-in-the-loop confirmation
├── pages/
│   ├── DashboardPage.jsx      # Main dashboard view
│   ├── PatientPage.jsx        # Single patient detail
│   └── AuditLogPage.jsx       # Compliance audit trail
└── utils/
    ├── agentColors.js         # Agent color mapping
    └── statusMapping.js       # Workflow state → tag props
```

---

*Use `@carbon/react` components wherever possible. Only build custom components when Carbon doesn't have an equivalent. Every custom component must use Carbon tokens for color, spacing, and typography — no hardcoded hex values outside of the agent accent colors defined above.*
