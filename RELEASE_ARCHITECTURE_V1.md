# Physical AI Site Release Architecture v1.0.0 Candidate

## Source of truth
- Header: `includes/site-header.html`
- Footer: `includes/site-footer.html`
- Shared responsive layout: `assets/css/shared-layout.css`
- Site generation: `scripts/build_site.py`
- Approved asset references: `scripts/apply_site_assets.py`
- Release validation: `scripts/verify_release.py`

## Workflows kept
1. `.github/workflows/ci.yml` — build and verify pull requests only.
2. `.github/workflows/pages.yml` — manual production deployment from verified `main` only.
3. `.github/workflows/production-check.yml` — read-only production evidence check.

## Forbidden behavior
- Workflows must not commit generated changes back to `main`.
- Workflows must not rewrite source HTML, CSS, header, footer, or logo files.
- Pushes to `main` must not automatically deploy production.
- Release verification must never modify the artifact it validates.
- Legacy logo hiding rules, PNG logo references, `brand-picture`, and `/aa8-Robotic/` production URLs are forbidden.

## Release sequence
1. Open pull request.
2. PR CI builds the exact release candidate.
3. `scripts/verify_release.py` passes.
4. Merge to `main`.
5. Manually run Pages deployment.
6. Production Release Check passes.
7. Create Git tag `v1.0.0`.
