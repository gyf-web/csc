import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".deps" / "pdf"))

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "文献调研"
OUT_DIR = PDF_DIR / "_extracted"
OUT_DIR.mkdir(exist_ok=True)

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)

KEYWORDS = [
    "abstract", "study area", "study site", "methods", "materials",
    "gedi", "l2a", "l2b", "l4a", "quality", "sensitivity",
    "degrade", "rh95", "rh98", "relative height", "footprint",
    "structural complexity", "canopy structural complexity",
    "foliage height diversity", "fhd", "pavd", "pai",
    "resolution", "spatial resolution", "temporal", "time period",
    "random forest", "xgboost", "model", "validation", "r2", "rmse",
    "auc", "accuracy", "conclusion", "limitations",
    "研究区", "研究方法", "数据", "gedi", "复杂性", "分辨率", "结论", "局限",
]


def normalize(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_meta(path):
    try:
        reader = PdfReader(str(path))
        meta = reader.metadata or {}
        return {
            "pages": len(reader.pages),
            "pdf_title": getattr(meta, "title", None) or meta.get("/Title"),
            "pdf_author": getattr(meta, "author", None) or meta.get("/Author"),
            "pdf_subject": getattr(meta, "subject", None) or meta.get("/Subject"),
        }
    except Exception as exc:
        return {"pages": None, "pdf_error": repr(exc)}


def extract_text(path):
    pages = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                pages.append(f"\n\n--- Page {i} ---\n{text}")
    except Exception as exc:
        return "", repr(exc)
    return normalize("".join(pages)), None


def keyword_windows(text, max_windows=90):
    lower = text.lower()
    windows = []
    seen = set()
    for kw in KEYWORDS:
        start = 0
        kw_lower = kw.lower()
        while True:
            pos = lower.find(kw_lower, start)
            if pos < 0:
                break
            a = max(0, pos - 450)
            b = min(len(text), pos + 900)
            snippet = normalize(text[a:b])
            key = snippet[:160]
            if key not in seen:
                windows.append({"keyword": kw, "snippet": snippet})
                seen.add(key)
            start = pos + len(kw_lower)
            if len(windows) >= max_windows:
                return windows
    return windows


def main():
    manifest = []
    for path in sorted(PDF_DIR.glob("*.pdf")):
        meta = safe_meta(path)
        text, error = extract_text(path)
        dois = sorted({m.group(0).rstrip(").,;]") for m in DOI_RE.finditer(text)})
        first_pages = "\n".join(text.split("--- Page ")[1:4])
        record = {
            "file": path.name,
            "path": str(path),
            **meta,
            "text_chars": len(text),
            "text_error": error,
            "doi_candidates": dois[:10],
            "first_pages": normalize(first_pages[:12000]),
            "keyword_windows": keyword_windows(text),
        }
        txt_path = OUT_DIR / f"{path.stem}.txt"
        json_path = OUT_DIR / f"{path.stem}.json"
        txt_path.write_text(text, encoding="utf-8", errors="ignore")
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest.append({k: record.get(k) for k in ["file", "path", "pages", "text_chars", "text_error", "doi_candidates"]})
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
