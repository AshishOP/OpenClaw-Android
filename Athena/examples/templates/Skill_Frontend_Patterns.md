# Skill: Frontend Patterns (Stolen from Claude Insider)

> **Source**: [Claude Insider CLAUDE.md](https://github.com/siliconyouth/claude-insider/blob/main/CLAUDE.md)  
> **Last Updated**: 2026-01-11

---

## 1. Seven Pillars UX Checklist

> **Rule**: All new frontend components MUST implement these pillars.

| Pillar | Purpose | Implementation |
|--------|---------|----------------|
| **Design System** | Visual consistency | Use design tokens, never hardcode colors |
| **Optimistic UI** | Instant feedback | Update UI immediately, sync in background |
| **Content-Aware Loading** | Lazy loading | IntersectionObserver for offscreen content |
| **Smart Prefetching** | Preload before click | Prefetch on hover/focus |
| **Error Boundaries** | Graceful errors | Wrap components with error fallbacks |
| **Micro-interactions** | Animations | GPU-optimized (transform, opacity only) |
| **Accessibility** | WCAG 2.1 AA | Focus traps, aria-live regions |

---

## 2. New Feature Checklist (Pre-Ship)

- [ ] Uses design tokens (no hardcoded colors)
- [ ] Async operations show instant feedback (toast/skeleton)
- [ ] Heavy content uses lazy loading
- [ ] Navigation uses prefetch
- [ ] Wrapped with ErrorBoundary
- [ ] Loading skeletons match page design
- [ ] Fixed-bottom elements account for mobile nav
- [ ] No horizontal scrolling on mobile (`width: 100%` not `100vw`)
- [ ] Square elements use `flex-shrink: 0; aspect-ratio: 1`

---

## 3. Dark-First Design Tokens

> **Philosophy**: Design for dark mode first, then adapt for light.

### Color Palette (Vercel-inspired)

| Purpose | Value |
|---------|-------|
| Background (darkest) | `#0a0a0a` |
| Background (card) | `#111111` |
| Background (elevated) | `#1a1a1a` |
| Border | `rgba(255, 255, 255, 0.1)` |

### Gradient System

| Type | Classes (Tailwind) |
|------|-------------------|
| Primary Gradient | `from-violet-600 via-blue-600 to-cyan-600` |
| Text Gradient | `from-violet-400 via-blue-400 to-cyan-400` |
| Glow Effect | `shadow-[color]-500/25` |

### Color Rules

- **PROHIBITED** for decorative: `orange-*`, `amber-*`, `yellow-*`
- **ALLOWED** for semantic only: warnings, ratings, status indicators

---

## 4. Optimistic UI Pattern

> **Rule**: Never block the UI waiting for server response.

```
1. User action → Generate temp ID
2. Update UI IMMEDIATELY (optimistic state)
3. Clear input (user can continue)
4. Sync with server in background (non-blocking)
5. Replace temp ID with real ID on success
6. Rollback on failure + show error toast
```

**Prohibited**:

- `await serverCall()` before updating UI
- Spinner/loader during server wait for user-initiated actions
- Blocking input until server confirms

---

## 5. Mobile Navigation Awareness

> **Problem**: Fixed bottom elements get hidden by mobile nav bars.

**Solution**: Use CSS variable for safe area:

```css
:root {
  --mobile-nav-height: calc(4rem + env(safe-area-inset-bottom));
}

/* For fixed bottom elements */
.fixed-bottom-button {
  bottom: calc(1.5rem + var(--mobile-nav-height, 0px));
}

/* For modals */
.modal-content {
  padding-bottom: calc(1rem + var(--mobile-nav-height, 0px));
}
```

---

## 6. GPU-Optimized Animations

> **Rule**: Only animate `transform` and `opacity` for smooth 60fps.

**Allowed**:

- `transform: translate(), scale(), rotate()`
- `opacity`

**Prohibited** (causes repaints):

- `width`, `height`
- `top`, `left`, `right`, `bottom`
- `margin`, `padding`
- `border-radius`

---

# frontend #ux #design-system #stolen
