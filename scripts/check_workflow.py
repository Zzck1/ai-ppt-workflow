"""Portable planning and PPTX package checks. Does not render or certify design."""

import argparse
import hashlib
import importlib.util
import json
import math
import posixpath
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def check_plan(plan):
    errors = []
    if not isinstance(plan, dict):
        return ["Plan must be a JSON object"]
    if type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        errors.append("schema_version must be 1")
    for key in ("topic", "audience", "goal", "delivery"):
        if not nonempty(plan.get(key)):
            errors.append(f"Missing text: {key}")
    slides, facts, design = plan.get("slides"), plan.get("facts"), plan.get("design")
    if not isinstance(slides, list) or not slides:
        errors.append("slides must be a non-empty list")
        slides = []
    count = plan.get("slide_count")
    if type(count) is not int or count < 1 or count != len(slides):
        errors.append("slide_count must equal the total number of slides")
    if not isinstance(design, dict):
        errors.append("design must be an object")
        design = {}
    for key in ("aspect_ratio", "font"):
        if not nonempty(design.get(key)):
            errors.append(f"Missing design text: {key}")
    for key in ("title_pt", "body_pt", "caption_pt"):
        if not number(design.get(key)) or design[key] <= 0:
            errors.append(f"design.{key} must be a positive number in pt")
    for key in ("background", "text", "accent"):
        if not isinstance(design.get(key), str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", design[key]):
            errors.append(f"design.{key} must be #RRGGBB")
    if not isinstance(facts, list):
        errors.append("facts must be a list (may be empty)")
        facts = []
    by_id = {}
    for i, fact in enumerate(facts, 1):
        if not isinstance(fact, dict):
            errors.append(f"Fact {i} must be an object")
            continue
        fid = fact.get("id")
        if not nonempty(fid) or fid in by_id:
            errors.append(f"Fact {i}: missing or duplicate id")
            continue
        by_id[fid] = fact
        if fact.get("status") not in ("fact", "plan", "scenario", "pending"):
            errors.append(f"{fid}: invalid status")
        for key in ("label", "source", "scope", "period"):
            if not nonempty(fact.get(key)):
                errors.append(f"{fid}: missing {key}")
        if "value" in fact and (not number(fact["value"]) or not nonempty(fact.get("unit"))):
            errors.append(f"{fid}: numeric value needs a finite number and unit")
    ids = set()
    for i, slide in enumerate(slides, 1):
        prefix = f"Slide {i}"
        if not isinstance(slide, dict):
            errors.append(f"{prefix} must be an object")
            continue
        sid = slide.get("id")
        if not nonempty(sid) or sid in ids:
            errors.append(f"{prefix}: missing or duplicate id")
        else:
            ids.add(sid)
        for key in ("title", "message", "visual"):
            if not nonempty(slide.get(key)):
                errors.append(f"{prefix}: missing {key}")
        body = slide.get("body")
        if not isinstance(body, list) or not body or not all(nonempty(s) for s in body):
            errors.append(f"{prefix}: body must contain visible text")
        refs = slide.get("fact_ids")
        if not isinstance(refs, list) or not all(nonempty(r) for r in refs):
            errors.append(f"{prefix}: fact_ids must be a list of strings")
            refs = []
        for ref in refs:
            if ref not in by_id:
                errors.append(f"{prefix}: unknown fact {ref}")
        chart = slide.get("chart")
        if chart is None:
            continue
        if not isinstance(chart, dict):
            errors.append(f"{prefix}: chart must be an object")
            continue
        # This intentionally small contract supports one category series only.
        if chart.get("type") not in ("column", "bar", "line"):
            errors.append(f"{prefix}: supported chart types are column, bar, line")
        cats, vals, chart_refs = [chart.get(k) for k in ("categories", "values", "fact_ids")]
        if not all(isinstance(v, list) for v in (cats, vals, chart_refs)):
            errors.append(f"{prefix}: chart categories/values/fact_ids must be lists")
            continue
        if not cats or len(cats) != len(vals) or len(vals) != len(chart_refs):
            errors.append(f"{prefix}: chart point counts differ or are empty")
        if not all(nonempty(c) for c in cats) or not nonempty(chart.get("unit")):
            errors.append(f"{prefix}: chart categories and unit need text")
        for value, ref in zip(vals, chart_refs):
            fact = by_id.get(ref) if isinstance(ref, str) else None
            if not number(value) or not fact or not number(fact.get("value")):
                errors.append(f"{prefix}: chart point needs a numeric fact")
            elif value != fact["value"] or chart.get("unit") != fact.get("unit"):
                errors.append(f"{prefix}: chart value/unit differs from {ref}")
            if ref not in refs:
                errors.append(f"{prefix}: chart fact must also be a page fact")
    return errors


def inspect_pptx(path, expected_slides=None):
    """Read the published slide order and internal relationship targets, not filenames."""
    result = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "errors": [], "slides": [],
              "visual_review": "not_performed", "editability": "requires_object_or_application_review"}
    errors = result["errors"]
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        if len(names) != len(package.namelist()):
            errors.append("Duplicate ZIP part names")
        bad = package.testzip()
        if bad:
            errors.append(f"ZIP CRC failure: {bad}")
        roots = {}
        for name in names:
            if name.endswith((".xml", ".rels")):
                roots[name] = ET.fromstring(package.read(name))
        for required in ("[Content_Types].xml", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"):
            if required not in roots:
                errors.append(f"Missing part: {required}")
        # Internal relationships resolve relative to the owning part's directory.
        targets = {}
        for name, root in roots.items():
            if not name.endswith(".rels"):
                continue
            owner_dir = posixpath.dirname(posixpath.dirname(name))
            links = {}
            for rel in root:
                if rel.get("TargetMode") == "External":
                    continue
                target = unquote(rel.get("Target", "").split("#")[0])
                resolved = posixpath.normpath(target.lstrip("/") if target.startswith("/") else posixpath.join(owner_dir, target))
                links[rel.get("Id")] = resolved
                if resolved not in names:
                    errors.append(f"Missing relationship target: {name} -> {resolved}")
            targets[name] = links
        presentation = roots.get("ppt/presentation.xml")
        if presentation is not None:
            links = targets.get("ppt/_rels/presentation.xml.rels", {})
            for slide_id in presentation.findall("p:sldIdLst/p:sldId", NS):
                target = links.get(slide_id.get("{" + NS["r"] + "}id"))
                slide = roots.get(target)
                if slide is None or slide.tag != "{" + NS["p"] + "}sld":
                    errors.append("Published slide has no valid slide part")
                    continue
                texts = slide.findall(".//a:t", NS)
                result["slides"].append({"part": target, "text_runs": len(texts),
                    "pictures": len(slide.findall(".//p:pic", NS)),
                    "graphic_frames": len(slide.findall(".//p:graphicFrame", NS))})
        count = len(result["slides"])
        if not count:
            errors.append("No published slides")
        if expected_slides is not None and count != expected_slides:
            errors.append(f"Expected {expected_slides} slides, found {count}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Report local capabilities without installing anything")
    plan = sub.add_parser("plan", help="Check the optional JSON planning contract")
    plan.add_argument("path", type=Path)
    pptx = sub.add_parser("pptx", help="Inspect PPTX package; no rendering or visual pass")
    pptx.add_argument("path", type=Path)
    pptx.add_argument("--expected-slides", type=int)
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            result = {"python": sys.version.split()[0], "python_pptx": bool(importlib.util.find_spec("pptx")),
                      "node": shutil.which("node"), "soffice_on_path": shutil.which("soffice"),
                      "note": "Detection only. Installed libraries do not prove a working authoring/rendering route. Check app tools separately."}
        elif args.command == "plan":
            data = args.path.read_bytes()
            result = {"sha256": hashlib.sha256(data).hexdigest(), "errors": check_plan(json.loads(data.decode("utf-8-sig")))}
        else:
            if args.expected_slides is not None and args.expected_slides < 1:
                parser.error("--expected-slides must be positive")
            result = inspect_pptx(args.path, args.expected_slides)
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        result = {"errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
