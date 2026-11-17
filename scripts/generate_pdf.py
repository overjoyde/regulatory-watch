#!/usr/bin/env python3
"""Generate requested outputs from one validated report model. Never fetches or sends data."""
import argparse
import copy
import hashlib
import html
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from common import blocks, cli, markdown, output_stem, read_json, word_count
from validate_report import report_errors


def choose_fonts(config, report):
    import reportlab
    style = config["report"]["style"]
    regular, bold = style["font_regular"], style["font_bold"]
    notes = []
    if regular and (not Path(regular).is_file() or not Path(bold).is_file()):
        notes.append("Requested font unavailable; embedded Bitstream Vera substituted.")
        regular = bold = None
    if not regular:
        fonts = Path(reportlab.__file__).parent / "fonts"
        regular, bold = str(fonts / "Vera.ttf"), str(fonts / "VeraBd.ttf")
    if not Path(regular).is_file() or not Path(bold).is_file():
        raise ValueError("No embeddable fonts available. Supply regular and bold TTF paths.")
    for note in notes:
        if note not in report["limitations"]:
            report["limitations"].append(note)
    return regular, bold, notes


def render_pdf(report, config, output, fonts):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
    regular, bold = fonts
    pdfmetrics.registerFont(TTFont("WatchBody", regular))
    pdfmetrics.registerFont(TTFont("WatchBold", bold))
    content = blocks(report)
    for kind, text in content:
        font = pdfmetrics.getFont("WatchBold" if kind.startswith("h") else "WatchBody")
        missing = {c for c in text if not c.isspace() and ord(c) not in font.face.charToGlyph}
        if missing:
            raise ValueError(f"Font lacks glyphs {sorted(missing)!r}; supply appropriate licensed TTF fonts")
    preset = config["report"]["design"]
    style = config["report"]["style"]
    text_color = style["text_color"] if preset == "custom" else "#20252B"
    accent = style["accent_color"] if preset == "custom" else ("#345A70" if preset == "default_light" else "#404040")
    sizes = {"h1": (24, 28), "h2": (13, 17), "h3": (11.5, 15), "p": (10.5, 15), "url": (9, 12)}
    styles = {kind: ParagraphStyle(kind, fontName="WatchBold" if kind.startswith("h") else "WatchBody",
                                  fontSize=size, leading=leading, textColor=colors.HexColor(text_color),
                                  spaceBefore=8 if kind.startswith("h") else 0, spaceAfter=8,
                                  keepWithNext=kind.startswith("h"), alignment=TA_LEFT,
                                  splitLongWords=True, allowWidows=0, allowOrphans=0)
              for kind, (size, leading) in sizes.items()}
    story = []
    for kind, text in content:
        if kind == "url":
            escaped = html.escape(text, quote=True)
            rendered = f'<link href="{escaped}" color="{accent}" underline="1">{escaped}</link>'
        else:
            rendered = html.escape(text)
        story.append(Paragraph(rendered, styles[kind]))
        if kind == "h1":
            story.extend([HRFlowable(width="100%", thickness=0.5, color=colors.HexColor(accent)), Spacer(1, 10)])
    document = SimpleDocTemplate(str(output), pagesize=A4, topMargin=18*mm, bottomMargin=17*mm,
                                 leftMargin=18*mm, rightMargin=18*mm,
                                 title=content[0][1], author="", subject="Regulatory monitoring report")
    document.build(story)


def verify_pdf(path, report):
    from pypdf import PdfReader
    reader = PdfReader(path)
    if not reader.pages:
        raise ValueError("Generated PDF has no pages")
    # Strip whitespace only: catches omitted paragraphs, headings, changed dates and source URLs.
    expected = re.sub(r"\s+", "", "".join(value for _, value in blocks(report)))
    actual = re.sub(r"\s+", "", "".join(page.extract_text() or "" for page in reader.pages))
    if expected != actual:
        raise ValueError("PDF text differs from canonical report; review font or layout")
    links = []
    for page in reader.pages:
        for reference in page.get("/Annots", []):
            annotation = reference.get_object()
            action = annotation.get("/A", {})
            if action.get("/URI"):
                links.append(str(action["/URI"]))
        for reference in page["/Resources"].get("/Font", {}).values():
            font = reference.get_object()
            if font.get("/Subtype") == "/Type0":
                fonts = [f.get_object() for f in font["/DescendantFonts"]]
            else:
                fonts = [font]
            for item in fonts:
                descriptor = item.get("/FontDescriptor")
                if descriptor and not any(key in descriptor.get_object() for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                    raise ValueError("PDF font is not embedded")
    if not {s["url"] for s in report["sources"]} <= set(links):
        raise ValueError("PDF is missing clickable source links")
    return len(reader.pages)


def generate(report, config, directory, previous=None):
    report = copy.deepcopy(report)
    errors = report_errors(report, config, previous)
    if errors:
        raise ValueError("\n".join(errors))
    wants_pdf = "pdf" in config["report"]["formats"]
    notes = []
    fonts = None
    if wants_pdf:
        regular, bold, notes = choose_fonts(config, report)
        fonts = regular, bold
    # Font disclosures must fit the SAME budget and appear in both output formats.
    errors = report_errors(report, config, previous)
    if errors:
        raise ValueError("\n".join(errors))
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stem = output_stem(config, report)
    extensions = ["json"] + (["md"] if "markdown" in config["report"]["formats"] else []) + (["pdf"] if wants_pdf else [])
    paths = {ext: directory / f"{stem}.{ext}" for ext in extensions}
    if any(path.exists() for path in paths.values()):
        raise ValueError("Output already exists; use a new run_id or output directory")
    pages = None
    with TemporaryDirectory(prefix="regulatory-watch-") as staging:
        staged = {ext: Path(staging) / path.name for ext, path in paths.items()}
        staged["json"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if "md" in staged:
            staged["md"].write_text(markdown(report), encoding="utf-8")
        if wants_pdf:
            render_pdf(report, config, staged["pdf"], fonts)
            pages = verify_pdf(staged["pdf"], report)
        # Exclusive creation avoids overwriting earlier reports. Partial writes are disclosed on failure.
        created = []
        try:
            for ext, destination in paths.items():
                with destination.open("xb") as target:
                    created.append(destination)
                    target.write(staged[ext].read_bytes())
        except OSError as exc:
            raise ValueError(f"Output write failed; files created so far: {[str(p) for p in created]}; {exc}") from exc
    return {"files": {ext: str(path) for ext, path in paths.items()}, "pages": pages,
            "sha256": {ext: hashlib.sha256(path.read_bytes()).hexdigest() for ext, path in paths.items()},
            "word_count": word_count(report), "font_substitutions": notes,
            "verification": "text parity, embedded fonts and link annotations checked; render/inspect every page separately",
            "storage": "files_created_in_requested_execution_directory; cloud_storage_and_delivery_not_performed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--previous")
    args = parser.parse_args()
    previous = read_json(args.previous) if args.previous else None
    if previous:
        from common import schema_errors
        errors = schema_errors(previous, "report.schema.json")
        if errors:
            raise ValueError("Invalid previous report: " + "; ".join(errors))
    print(json.dumps(generate(read_json(args.report), read_json(args.config), args.output_dir, previous), indent=2))


if __name__ == "__main__":
    cli(main)
