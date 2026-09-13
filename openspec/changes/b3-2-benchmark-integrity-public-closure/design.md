# Design

## Frozen inputs

`HSBCVisualStress-v1`, the B3.1 CLIP RN50 model, the HSBC PDF/render manifests, and the FinRAGBench-V revision `d0d65255c94e687caa81ac9da7758ed25ff046a5` remain immutable inputs. B3.2 writes new audit/control outputs and does not rewrite historical B3.1 runs.

## Benchmark integrity

The stress audit selects two cases per stress category from case order only. It records T0 rankings at K `{1,5,10,50}`, query/source overlap, source block identity, gold mapping, and construction provenance. Attribution is an auditable deterministic classification with an explicit inference status, not a claim of causal proof.

The natural control selection is frozen from a SHA-256 ordering of eligible HSBC corpus pages, with stress candidate pages excluded before any T0/V0 result is read. Its cases, manifest, and metrics are reported independently from the stress set.

## Public closure

The official Hugging Face single-file archive is requested at the frozen commit through a cache/resume-capable client. Each attempt records transport, revision, file identity, timestamps, and full exception evidence. Only a verified archive can enable the existing public page evaluator.

## Acceptance

- Stress construction bias is explicitly accepted, rejected, or unresolved from a fixed 20-case audit sample.
- Natural control selection has 60–100 real HSBC cases and a pre-performance freeze manifest.
- Stress and natural metrics are separate.
- T0 @10 is reproducibly explained with @1/@5/@10/@50 evidence.
- Public metrics are either complete on the frozen slice or remain N/A with an auditable blocker.
