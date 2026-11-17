# Neutral, configurable report design

No organization branding, logos, proprietary fonts or user-specific styling is included. Presets:

| Setting | `default_light` | `minimal_gray` |
|---|---|---|
| Page | A4 portrait, white | Same |
| Margins | 18 mm top/left/right, 17 mm bottom | Same |
| Body/text | 10.5/15 pt, `#20252B` | Same |
| Title | 24/28 pt bold | Same |
| Section | 13/17 pt bold | Same |
| Finding heading | 11.5/15 pt bold | Same |
| Source URLs | 9/12 pt, `#345A70` | 9/12 pt, `#404040` |
| Accents | Thin divider, `#345A70` | Thin divider, `#404040` |

`custom` uses `report.style.text_color` and `accent_color` for text/dividers/links; page geometry and type hierarchy remain consistent. Supply regular and bold `.ttf` font paths for a custom licensed font; no font files are distributed. ReportLab's available bundled Bitstream Vera is the default embedded font. If requested font paths are missing, both fonts fall back together, a disclosure is added to the canonical report and the word budget is checked again. Invalid/corrupt TTFs fail explicitly; choose valid fonts rather than reporting success.

No shadows, gradients, decorative buttons or color-only statuses. Single column, explicit status text, conservative spacing. Keep headings with the next paragraph, allow text to continue onto further pages, wrap long URLs and preserve links. Custom fonts must cover every used glyph. License checking for user-provided fonts remains the user's responsibility; only use embeddable licensed fonts.

## PDF QA

The generator checks PDF text against the canonical text ignoring whitespace, source link annotations and font embedding. These checks do **not** prove no visual clipping or online URL reachability. Render every output PDF page using an available renderer, for example:

```sh
pdftoppm -scale-to 1400 -png REPORT.pdf PAGE_PREFIX
```

Inspect all pages for clipping, overlap, square missing glyphs, awkward headings, small links and whitespace. If changing layout, regenerate all outputs from the same canonical model and rerun checks. Do not report visual QA as complete if rendering/image inspection was unavailable. Disclose material deviations or unsupported language shaping. Validate direct legal links by opening them during research, separately from annotation checks.
