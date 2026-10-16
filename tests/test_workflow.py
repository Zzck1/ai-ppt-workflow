import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_workflow", ROOT / "scripts/check_workflow.py")
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class PlanChecks(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / "examples/course-report.plan.json").read_text(encoding="utf-8"))

    def test_example(self):
        self.assertEqual(workflow.check_plan(self.plan), [])

    def test_chart_drift(self):
        self.plan["slides"][1]["chart"]["values"][0] = 13
        self.assertTrue(any("differs from F01" in e for e in workflow.check_plan(self.plan)))

    def test_unknown_fact_and_count(self):
        self.plan["slide_count"] = 4
        self.plan["slides"][0]["fact_ids"] = ["F99"]
        errors = workflow.check_plan(self.plan)
        self.assertTrue(any("unknown fact" in e for e in errors))
        self.assertTrue(any("slide_count" in e for e in errors))

    def test_unit_and_duplicate_id(self):
        self.plan["slides"][1]["chart"]["unit"] = "秒"
        self.plan["facts"].append(copy.deepcopy(self.plan["facts"][0]))
        errors = workflow.check_plan(self.plan)
        self.assertTrue(any("duplicate id" in e for e in errors))
        self.assertTrue(any("value/unit differs" in e for e in errors))

    def test_malformed_types_do_not_crash(self):
        for bad in (None, [], {"facts": [None], "slides": [None]},
                    {**self.plan, "design": {"font": [], "title_pt": True}}):
            with self.subTest(bad=bad):
                self.assertTrue(workflow.check_plan(bad))
        self.plan["slides"][1]["chart"]["fact_ids"] = [["F01"], None]
        self.assertTrue(workflow.check_plan(self.plan))

    def test_non_finite_data(self):
        self.plan["facts"][0]["value"] = float("nan")
        self.assertTrue(any("finite" in e for e in workflow.check_plan(self.plan)))

    def test_chart_lengths(self):
        self.plan["slides"][1]["chart"]["values"].pop()
        self.assertTrue(any("point counts" in e for e in workflow.check_plan(self.plan)))

    def test_cli_bad_json_and_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "有 空格.json"
            for data, code in (("{", 1), (json.dumps(self.plan), 0)):
                path.write_text(data, encoding="utf-8-sig")
                run = subprocess.run([sys.executable, str(ROOT / "scripts/check_workflow.py"), "plan", str(path)], capture_output=True, text=True)
                self.assertEqual(run.returncode, code, run.stdout + run.stderr)
                self.assertIn("errors", json.loads(run.stdout))


class PackageChecks(unittest.TestCase):
    def make_fixture(self, path, missing=False, malformed=False):
        # Deliberately small XML/ZIP fixture, not a PowerPoint deliverable.
        p, r, rel, a = [workflow.NS[k] for k in ("p", "r", "rel", "a")]
        files = {
            "[Content_Types].xml": "<Types/>",
            "ppt/presentation.xml": f'<p:presentation xmlns:p="{p}" xmlns:r="{r}"><p:sldIdLst><p:sldId id="256" r:id="rId2"/><p:sldId id="257" r:id="rId1"/></p:sldIdLst></p:presentation>',
            "ppt/_rels/presentation.xml.rels": f'<Relationships xmlns="{rel}"><Relationship Id="rId1" Target="slides/slide1.xml"/><Relationship Id="rId2" Target="slides/slide2.xml"/></Relationships>',
            "ppt/slides/slide1.xml": f'<p:sld xmlns:p="{p}" xmlns:a="{a}"><a:t>A</a:t></p:sld>',
            "ppt/slides/slide2.xml": f'<p:sld xmlns:p="{p}"/>',
            "ppt/slides/slide99.xml": f'<p:sld xmlns:p="{p}"/>',
            "ppt/slides/_rels/slide1.xml.rels": f'<Relationships xmlns="{rel}"><Relationship Id="image" Target="../media/picture%20one.png"/><Relationship Id="url" Target="https://example.invalid/image" TargetMode="External"/></Relationships>',
            "ppt/media/picture one.png": "fixture-only",
        }
        if missing:
            del files["ppt/media/picture one.png"]
        if malformed:
            files["ppt/slides/slide1.xml"] = "<unclosed"
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)

    def test_published_order_and_orphan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.zip"
            self.make_fixture(path)
            result = workflow.inspect_pptx(path, 2)
            self.assertEqual(result["errors"], [])
            self.assertEqual([s["part"] for s in result["slides"]], ["ppt/slides/slide2.xml", "ppt/slides/slide1.xml"])
            self.assertEqual(result["visual_review"], "not_performed")
            self.assertEqual(len(result["sha256"]), 64)
            self.assertTrue(workflow.inspect_pptx(path, 3)["errors"])

    def test_missing_internal_media(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.zip"
            self.make_fixture(path, missing=True)
            self.assertTrue(any("Missing relationship target" in e for e in workflow.inspect_pptx(path)["errors"]))

    def test_malformed_xml_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.zip"
            self.make_fixture(path, malformed=True)
            run = subprocess.run([sys.executable, str(ROOT / "scripts/check_workflow.py"), "pptx", str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertTrue(json.loads(run.stdout)["errors"])


class RepositoryChecks(unittest.TestCase):
    def test_relative_markdown_links(self):
        for path in ROOT.rglob("*.md"):
            if ".git" in path.parts:
                continue
            for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                target = raw.split("#")[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                with self.subTest(file=path, target=target):
                    self.assertTrue((path.parent / unquote(target)).exists())

    def test_skill_frontmatter_and_interface(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        frontmatter = skill.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^name: ai-ppt-workflow$")
        self.assertRegex(frontmatter, r'(?m)^description: ".+"$')
        self.assertIn("$ai-ppt-workflow", (ROOT / "agents/openai.yaml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
