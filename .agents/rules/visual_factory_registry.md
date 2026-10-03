# Visual Factory Registry

`assets/visual_library/registry.json` is the canonical discoverable catalog for reusable Manim, Motion Canvas and brand resources. Agents must refresh it before choosing production visuals:

```bash
python3 optional-skills/creative/content-factory/factory_runner.py registry --query manim
python3 optional-skills/creative/content-factory/factory_runner.py registry-preflight --order order.json
```

`factory_runner.py assemble --production` requires `--order` and runs the same preflight before video assembly. Preview work may run without a production order but must remain labelled preview.

The preflight refreshes local source hashes and validates `channel_id`, `template_pack_id`, `template_version`, each required `template_slots` mapping, and every `resource_id`. Catalog presence only means that a resource was found. A production order passes only when its template is `approved` with accountable approval evidence and every requested resource is production eligible or explicitly listed in that template's `approved_resource_ids`.

Use `assets/visual_library/render_static.py` for deterministic SVG and PNG deliverables from a validated scene brief. Preserve NFC Vietnamese text and do not silently substitute a missing template, voice profile, or CTA link.
