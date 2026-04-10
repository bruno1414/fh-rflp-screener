# Front-end Production Grade Upgrade TODO

## 1) Base layout and design system hardening
- [ ] Refactor `app/templates/base.html` CSS into production-grade utility/component styles.
- [ ] Add consistent spacing scale, typography scale, and semantic color tokens.
- [ ] Improve responsive nav behavior for smaller screens.
- [ ] Add accessibility-focused focus states, hover states, and reduced-motion support.
- [ ] Replace repeated inline styles via reusable classes.

## 2) Home page (`index.html`) production polish
- [ ] Replace inline styles with reusable classes.
- [ ] Improve semantic structure (hero, stats, feature cards, process steps).
- [ ] Tighten typography hierarchy and spacing.
- [ ] Improve CTA visual consistency and responsive behavior.

## 3) Panel page (`panel.html`) robustness and UX
- [ ] Replace inline style usage with reusable classes.
- [ ] Improve table responsiveness and readability on narrow screens.
- [ ] Harden JS state handling for search/detail flows (loading/error/empty states).
- [ ] Improve detail panel layout for mobile.
- [ ] Add safer fetch error handling and status checks.

## 4) Analyze page (`analyze.html`) robustness and UX
- [ ] Replace inline styles with reusable classes.
- [ ] Improve form spacing, input affordance, and result card structure.
- [ ] Harden run flow with better button loading states/disable during request.
- [ ] Add stricter client-side validation feedback.
- [ ] Improve loading and error states consistency.

## 5) QA pass
- [ ] Check keyboard accessibility and visible focus across pages.
- [ ] Verify nav active state behavior.
- [ ] Verify responsive behavior for ~900px and smaller widths.
- [ ] Verify no template regressions in Jinja rendering.

## 6) Progress
- [x] Plan approved by user ("and proffesiona;lconfirm")
- [x] Started implementation with `app/templates/base.html`
