# PsCafe Management System — Design System

## Overview

This document defines the standardized color palette and design tokens for the PsCafe Management System UI. All UI elements should use these tokens instead of hardcoded hex values.

The design is based on **Material Design** color palette, with a dark-first approach. Semantic colors (green=go, red=stop, blue=info) remain consistent across both themes.

---

## Color Tokens

### Theme-Dependent Colors (change between dark/light)

| Token | Dark Mode | Light Mode | Usage |
|-------|-----------|------------|-------|
| `bg_page` | `#1E272C` | `#F5F5F5` | Dialog backgrounds, scroll areas |
| `bg_surface` | `#263238` | `#FFFFFF` | Cards, boxes, panels, summary frames |
| `bg_input` | `#37474F` | `#F0F0F0` | SpinBox, ComboBox, DateEdit, input fields |
| `text_primary` | `#ECEFF1` | `#212121` | Headers, primary labels, device names |
| `text_secondary` | `#B0BEC5` | `#616161` | Secondary labels, prices, session types |
| `text_muted` | `#78909C` | `#9E9E9E` | Notes, empty states, helper text |
| `text_tertiary` | `#90A4AE` | `#757575` | Time labels, tertiary info |
| `border_card` | `#37474F` | `#E0E0E0` | Card borders, box borders |
| `bg_disabled_card` | `#424242` | `#EEEEEE` | Disabled device card background |
| `bg_overdue_card` | `#3E2727` | `#FFEBEE` | Overdue device card background |
| `bg_overdue_badge` | `#5C2B2B` | `#FFCDD2` | Overdue "OVERDUE!" label background |
| `text_credits` | `#546E7A` | `#9E9E9E` | Footer/credits text |
| `bg_hover_overlay` | `#DDDDDD` | `#E0E0E0` | Mute button hover |

### Semantic Colors (same in both themes)

| Token | Color | Usage |
|-------|-------|-------|
| `accent_green` | `#4CAF50` | Available status, Start button, Save button, Add button, success indicators, revenue |
| `accent_green_hover` | `#43A047` | Start/Save/Add button hover |
| `accent_blue` | `#2196F3` | In-use status, summary stats |
| `accent_blue_dark` | `#1976D2` | Edit button, Refresh button, total label |
| `accent_blue_hover` | `#1565C0` | Edit/Refresh button hover |
| `accent_red` | `#F44336` | Overdue status, overdue border, session card overdue border |
| `accent_red_dark` | `#D32F2F` | End Session button, Remove button |
| `accent_red_hover` | `#C62828` | Remove button hover |
| `accent_red_end_hover` | `#DA190B` | End Session button hover |
| `accent_orange` | `#FF9800` | Extend button, cancelled sessions, avg duration stat |
| `accent_orange_hover` | `#F57C00` | Extend button hover |
| `accent_purple` | `#9C27B0` | Reports button |
| `accent_purple_hover` | `#7B1FA2` | Reports button hover |
| `accent_slate` | `#607D8B` | Manage Devices button |
| `accent_slate_hover` | `#546E7A` | Manage Devices button hover |
| `accent_gray` | `#9E9E9E` | Disabled status, Cancel button (session/extend dialogs) |
| `accent_gray_hover` | `#757575` | Cancel button hover (simple) |
| `accent_cancel` | `#546E7A` | Cancel button (end session, device dialogs) |
| `accent_cancel_hover` | `#455A64` | Cancel button hover |
| `accent_warning` | `#FF5722` | Warning labels, validation errors |
| `bg_btn_disabled` | `#CCCCCC` | Disabled button background |

---

## Component Styles

### Device Card (Main Window)

```css
/* Base card */
background-color: bg_surface;
border: 2px solid border_card;
border-radius: 8px;

/* Status left border */
[status="available"]  { border-left: 5px solid accent_green; }
[status="in_use"]     { border-left: 5px solid accent_blue; }
[status="overdue"]    { border-left: 5px solid accent_red; background-color: bg_overdue_card; }
[status="disabled"]   { border-left: 5px solid accent_gray; background-color: bg_disabled_card; }
```

### Device Card (Device Manager)

```css
background-color: bg_surface;
border: 1px solid border_card;
border-radius: 8px;
padding: 10px;
```

### Buttons

| Button Type | Normal | Hover |
|-------------|--------|-------|
| Start / Save / Add | `accent_green` (#4CAF50) | `accent_green_hover` (#43A047) |
| End Session | `accent_red_dark` (#D32F2F) | `accent_red_end_hover` (#DA190B) |
| Extend | `accent_orange` (#FF9800) | `accent_orange_hover` (#F57C00) |
| Edit / Refresh | `accent_blue_dark` (#1976D2) | `accent_blue_hover` (#1565C0) |
| Remove | `accent_red_dark` (#D32F2F) | `accent_red_hover` (#C62828) |
| Manage Devices | `accent_slate` (#607D8B) | `accent_slate_hover` (#546E7A) |
| Reports | `accent_purple` (#9C27B0) | `accent_purple_hover` (#7B1FA2) |
| Cancel (neutral) | `accent_cancel` (#546E7A) | `accent_cancel_hover` (#455A64) |
| Cancel (simple) | `accent_gray` (#9E9E9E) | `accent_gray_hover` (#757575) |
| Disabled | `bg_btn_disabled` (#CCCCCC) | — |

### Text Hierarchy

| Level | Dark | Light | Usage |
|-------|------|-------|-------|
| Primary | `#ECEFF1` | `#212121` | Headers, device names, important values |
| Secondary | `#B0BEC5` | `#616161` | Labels, prices, session types |
| Muted | `#78909C` | `#9E9E9E` | Helper text, empty states, notes |
| Tertiary | `#90A4AE` | `#757575` | Time labels, timestamps |

---

## QPalette Mapping (for theme auto-detection)

When implementing OS theme detection, map tokens to QPalette roles:

| QPalette Role | Dark Mode | Light Mode |
|---------------|-----------|------------|
| `Window` | `#1E272C` | `#F5F5F5` |
| `WindowText` | `#ECEFF1` | `#212121` |
| `Base` | `#263238` | `#FFFFFF` |
| `AlternateBase` | `#37474F` | `#F0F0F0` |
| `Text` | `#ECEFF1` | `#212121` |
| `Button` | `#37474F` | `#E0E0E0` |
| `ButtonText` | `#ECEFF1` | `#212121` |
| `Highlight` | `#1976D2` | `#1976D2` |
| `HighlightedText` | `#FFFFFF` | `#FFFFFF` |
| `Mid` | `#37474F` | `#E0E0E0` |
| `Dark` | `#1A2327` | `#BDBDBD` |
| `PlaceholderText` | `#78909C` | `#9E9E9E` |

---

## Known Inconsistencies (to fix during theme refactor)

| Issue | Current Values | Should Be |
|-------|---------------|-----------|
| Primary text | `#ECEFF1` and `#ffffff` used interchangeably | `#ECEFF1` (dark) / `#212121` (light) |
| Muted text | `#666` and `#78909C` used for same purpose | `#78909C` (dark) / `#9E9E9E` (light) |
| Card border | `#ddd` in main_window, `#37474F` in device_dialog | `#37474F` (dark) / `#E0E0E0` (light) |
| Green hover | `#45a049` and `#43A047` used | `#43A047` consistently |
| Red hover (end) | `#da190b` used inconsistently | `#DA190B` consistently for End Session |
| Red hover (remove) | `#C62828` used | `#C62828` consistently for Remove |
| Summary bar | `#e3f2fd` in dark theme (light blue) | Keep `#e3f2fd` or use theme-aware variant |

---

## Font Conventions

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Window title | Arial | 20px | Bold |
| Card/device name | Arial | 14px | Bold |
| Section header | Arial | 16-18px | Bold |
| Status label | Arial | 12px | Bold |
| Body text | Arial | 12px | Normal |
| Secondary info | Arial | 10-11px | Normal |
| Footer/credits | Arial | 9px | Normal |

---

## Notes

- All colors use Material Design palette values
- Semantic colors (green/blue/red/orange) stay the same in both themes — they convey meaning, not theme
- Theme-dependent colors (backgrounds, text) swap between dark and light palettes
- Future UI additions should reference tokens from this document, not hardcoded hex values
