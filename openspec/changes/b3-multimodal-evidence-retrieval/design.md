# Design

## Contracts

`Evidence` remains backward compatible. Image evidence adds `page_image_id`, `image_path`, `render_hash`, and optional `region_bbox`/`region_type`; a page-level image has no fabricated bounding box.

`PageImage` records document/page identity, dimensions, DPI, render version, source PDF hash, and image hash. `VisualRetriever` indexes only image-backed evidence and calls the configured encoder on image files during `fit`; query ranking is independent of OCR text.

## Pipeline

```text
PDF -> pdftoppm deterministic page PNG -> PageImage manifest
                                      -> image Evidence IR
question -> text/structured retrieval -> requirement coverage
                                      -> routing TEXT/TABLE/VISUAL/MIXED/UNKNOWN
                                      -> image retrieval -> normalized RRF/weighted fusion
                                      -> evidence qualification -> page/citation metrics
```

The baseline encoder is OpenAI CLIP RN50 when weights are obtainable locally. If unavailable, B3 records the blocker and does not call raw-pixel similarity a visual-model result. A small deterministic pixel descriptor is retained only as a non-model diagnostic and is never included in the headline visual baseline.

## Evaluation

The runner creates one non-overwriting run directory with config, model/render/dataset manifests, per-system rankings, routing and grounding traces, metrics, failure cases, and latency. HSBC cases are mined from actual page images and parsed page evidence; public FinRAGBench queries/qrels are recorded separately and are N/A for page-image scoring unless the required PDF archive is successfully fixed.

## Trust boundaries

Local PDF artifacts are ignored and provenance-only manifests are tracked. Any claimed bbox metric requires gold bbox; page hits do not become bbox grounding. A visual page hit alone never marks a critical requirement satisfied.
