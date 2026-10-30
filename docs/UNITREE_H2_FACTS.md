# Unitree H2｜产品事实与素材来源 SSOT
Date: 2026-10-30 JST. Status: Draft, not authorized for production deployment.

## Product identity
- H2 is a full-body bipedal humanoid, NOT H2-D mobile manipulation, NOT H2-X.
- Manufacturer canonical: https://www.unitree.com/H2/ (also https://www.unitree.com/mobile/H2/)
- Official shop clarifies only H2 EDU supports secondary development: https://shop.unitree.com/collections/humanoid-robot/products/unitree-h2
- User designated material folder: https://drive.google.com/drive/folders/1_ErrDClSRDPIWFXkKTwtZ4ASKsQHq8xM
- Drive folder includes images and 3 video_0x.mp4 files; source file counts and identities were inspected via connected Google Drive, not assumed to be on local G:.

## Manufacturer fact boundaries
- Standard H2 and H2 EDU both 31 DoF, dimension 1820 × 456 × 218mm, approx 70kg.
- 6 DoF per leg, 7 per arm, waist 3, head 2.
- Maximum leg torque 360 N·m, arm torque 120 N·m; rated arm load ~7kg, peak ~15kg (posture/conditions vary).
- Standard H2 not for secondary development; EDU supports development with SKU-dependent SDK, optional dexterous hands and computing.
- Never claim optional 2070 TOPS as standard configuration.
- Domestic price, tax, delivery, warranty, authorization and installed SDK remain to verify individually.

## Material provenance
- `assets/img/products/unitree/h2/h2-humanoid-hero.jpg`: manufacturer official store thumbnail, https://shop.unitree.com/cdn/shop/files/1_b121bcb1-25af-459f-a39f-34215cda1fd6.jpg?v=1769743112
- `assets/img/products/unitree/h2/h2-dance-drive.webp`: exact bytes from user provided Google Drive file `image_005.webp` ID `1yX3cVfsScNA2Cna6YUsxaVXdZ00XSOfh` (260480 bytes, SHA256 E16F6FECBC1516E09FDFD4F94E5FBEA7A7A0EA15C0833EE2422148BB70A9C200).
- Three videos remain **staged in the original Drive**. Not embedded in this first candidate until H.264/H.265 compatibility, poster, content appropriateness and real Chrome decoding are verified. No false video-playback claim.
- Official manufacturer attribution retained. Use in promotional page per owner's previously decided policy; this does not certify a blanket content license.

## Release gates
Draft PR -> independent QA + exact SHA CI -> real noindex HTML Preview -> CEO review -> only afterward separate approved merge + manual GitHub Pages release and production SHA/PC/SP/CTA regression. Do not treat the current branch as published.
