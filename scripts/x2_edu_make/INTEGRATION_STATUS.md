# X2 EDU — Figma Make 原版ソース（隔離開発）

- Source of truth: https://www.figma.com/make/PjYrDDSNMZnmzvkYOSDqbo/
- Design reference: https://www.figma.com/design/qaygzloGf9JrpHAqwUvbnh/?node-id=4-2
- PC approved layout: HP構成-pc.png (10 sections)
- Run: `npm ci`, `npm run build`, `npm run dev` in this folder.
- Existing static page at `/products/agibot-x2-edu.html` is untouched.
- This is a source import and isolated build verification, NOT production integration, V3 copy completion or final PC/SP visual QA.
- Remaining: replace Make's original three-card sections with the approved 4/4/5 PC structure; apply Japanese V3 copy, use only manufacturer-approved specs; static SEO prerender, actual CTA/download targets, responsive screenshots and asset usage-right checks. No merge / deploy without approval.
- Do not copy the Vite `dist/index.html` over the production product page without SEO prerender and layout QA.