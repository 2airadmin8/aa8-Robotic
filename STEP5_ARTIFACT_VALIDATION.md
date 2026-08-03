# Step 5: Final Artifact Validation

The release gate validates the generated `_site` artifact rather than editable source HTML.

Required checks:

- every publishable HTML contains exactly one shared header and one shared footer;
- normalized Header/Footer hashes match `includes/site-header.html` and `includes/site-footer.html`;
- TOP and lower pages use the same PC/SP logo markup;
- legacy `brand-picture`, text `brand-mark`, and TOP-only sync markers are absent;
- shared CSS and both logo SVG assets exist and are non-empty;
- any mismatch fails PR CI before deployment.
