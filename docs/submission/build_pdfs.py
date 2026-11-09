"""Render the submission one-pagers to PDF. Usage: python build_pdfs.py [LIVE_URL] [REPO_URL]"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
live = sys.argv[1] if len(sys.argv) > 1 else "(link added after deploy)"
repo = sys.argv[2] if len(sys.argv) > 2 else "(link added after deploy)"

with sync_playwright() as p:
    b = p.chromium.launch()
    for name in ["project_description", "judges_quickstart"]:
        src = HERE / f"{name}.html"
        if not src.exists():
            continue
        tmp = HERE / f".{name}.render.html"
        tmp.write_text(src.read_text().replace("{{LIVE_URL}}", live).replace("{{REPO_URL}}", repo))
        page = b.new_page()
        page.goto(tmp.as_uri())
        page.wait_for_load_state("networkidle")
        h = page.evaluate("document.querySelector('.page').scrollHeight")
        page.pdf(path=str(HERE / f"HemoLink-{name.replace('_', '-')}.pdf"), format="A4", print_background=True,
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        page.close()
        tmp.unlink()
        print(name, "content height px:", h, "(A4 = 1123)")
    b.close()
