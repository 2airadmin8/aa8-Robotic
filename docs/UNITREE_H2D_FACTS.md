# Unitree H2-D | Product Fact Pack / Manufacturer Media Evidence
Checked: 2026-10-30 JST. State: isolated development candidate, **not** approved for production release.

## Single source of truth
- Manufacturer original: https://www.unitree.com/H2-D/
- Unitree product family: https://www.unitree.com/
- User-specified 2026-10-28 archived manufacturer page: `G:\共有ドライブ\002_PAI_ID009_[PhyicalAI]_AIロボット\03_販売製品資料_カタログ_パンフレット\Unitree\素材\ヒューマノイドRobot\Application Plan\H2-D.html`
- The matching archive Google Drive file: https://drive.google.com/file/d/11CJfRHe1kAhYgUVdxv1LFGT2tqSwxXBC/view
- Media master: `G:\共有ドライブ\002_PAI_ID009_[PhyicalAI]_AIロボット\03_販売製品資料_カタログ_パンフレット\Unitree\素材\ヒューマノイドRobot\Application Plan\H2-D_assets` and shared Drive folder https://drive.google.com/drive/folders/1T7Pf7I-QeKg0SoiNXqxONa3W0Thm31EO.
- Archive contains 25 files: 23 still images/SVG, 1 MP4 and 1 video-URL text. 14 selected still images were copied byte-for-byte and verified by SHA256. The selected original MP4 was HEVC/hvc1 and was converted once to H.264/avc1 for Chromium compatibility; the original file in Drive is unchanged.
- The archived single-file HTML is approximately 8MB of full-page capture, **not** a source template to copy wholesale; this product page reuses the AirAdmin8-approved G1 website components.

## Manufacturer-published SKU comparison (do not conflate with full bipedal H2)
| Specification | H2-D Standard | H2-D Flagship | Conditions |
|---|---|---|---|
| Total DOF (excluding end effector) | 19 | 20 | Config-dependent |
| Arm DOF | 7 each | 7 each | Dual arm |
| Rated / peak arm payload | ~7kg / ~15kg | ~7kg / ~15kg | Heavy posture dependency |
| Dimension minimum / maximum | 1200x576x620mm / 1700x576x620mm | Same published dimensions | Actual configuration |
| With battery weight | ~135kg | ~135kg | Published |
| Vertical lift / speed | 0.5m / up to 200mm/s | Same | Published |
| Reach with 2-finger gripper | ~0.62m | Same | Gripper option |
| Waist pitch | 0–115° | Same | Published |
| Base | Fixed / non-self-driving | Wheeled drive, up to 1.5m/s | No Flagship mobility claim on Standard |
| Chassis sensors | N/A | LiDAR, depth, collision, ultrasonic | Official variant table |
| Base compute | i5 platform + i7 custom development | Same | High-end compute module optional |
| Head & wrist vision | Wide-angle binocular x1; wrist HD x2 | Same | Published |
| Battery | 48V 18Ah (864Wh) | 48V 30Ah (1.44kWh) | Published |
| Power/running | Direct supply / continuous operation | Replaceable / autocharging ~5 hours | No guaranteed SLA |
| End effectors | optional 2-finger / 3-finger / 5-finger | Same | Not all included by default |
| SDK / secondary development | Manufacturer says supported | Manufacturer says supported | Exact API versions/SKU must be reviewed |
| Manufacturer warranty | 12 months | 12 months | NOT AirAdmin8 contract warranty |

Additional caveats: The product design and some features evolve by configuration; some capabilities are under development or roll out gradually. Industrial machinery requires physical safety distance and site-specific assessment. No unsupported claims of Japanese local pricing, current inventory, delivery lead time, domestic service promises or real customer outcome.

## File-by-file provenance: selected official assets from the shared folder
| Local website relative path | Archived file | Use |
|---|---|---|
| `assets/img/products/unitree/h2d/h2d-hero.webp` | `image_016.webp` | H2-D mobile flagship full-body Hero |
| `assets/img/products/unitree/h2d/h2d-factory.webp` | `image_005.webp` | Industrial operation / video poster |
| `assets/img/products/unitree/h2d/h2d-configurations.png` | `image_008.png` | H2 family platform concepts, not all H2-D SKUs |
| `assets/img/products/unitree/h2d/h2d-conveyor.png` | `image_012.png` | Conveyor sorting concept |
| `assets/img/products/unitree/h2d/h2d-warehouse.png` | `image_013.png` | Warehouse context |
| `assets/img/products/unitree/h2d/h2d-workspace.png` | `image_014.png` | Working space scheme |
| `assets/img/products/unitree/h2d/h2d-vision.png` | `image_017.png` | Perception close-up |
| `assets/img/products/unitree/h2d/h2d-transport.png` | `image_018.png` | Mobile transport illustration |
| `assets/img/products/unitree/h2d/h2d-effectors.png` | `image_019.png` | Optional gripper/dexterous hands |
| `assets/img/products/unitree/h2d/h2d-actuators.png` | `image_020.png` | Industrial joints torso closeup |
| `assets/img/products/unitree/h2d/h2d-laboratory.png` | `image_021.png` | Research photo |
| `assets/img/products/unitree/h2d/h2d-assembly.png` | `image_022.png` | Industrial manipulation scene |
| `assets/img/products/unitree/h2d/h2d-service.png` | `image_023.png` | Commercial service concept |
| `assets/img/products/unitree/h2d/h2d-training.png` | `image_024.png` | Embodied-AI training concept |
| `assets/img/products/unitree/h2d/h2d-motion.mp4` | `video_01.mp4` | Manufacturer motion video, explicit controls/no autoplay |

The website may use a subset of the copied evidence assets in the visible layout. CSS and HTML must never substitute H2 or G1 imagery for H2-D.

## Release/rights gates
- User has selected manufacturer's product marketing imagery for promotional product pages, with factory attribution/source preserved. This does not prove a third-party blanket reproduction license or transfer manufacturer warranty to AirAdmin8.
- The page links to Unitree official source; no copied entire manufacturer layout, downloadable copyrighted catalog, invented customer quote, unsupported review, false certifications or price schema.
- SEO: canonical + Japanese title/description, product-specific FAQ and stable URLs; Product JSON-LD without unverified price/review; Preview must carry `X-Robots-Tag: noindex`.
- Final QA on PC1440/SP390/SP360, video response, image sizes, links, CTA prefilling, independent QA and exact SHA; **CEO must view real HTML Preview before merge and manual production deployment**.
