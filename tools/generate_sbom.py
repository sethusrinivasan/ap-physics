#!/usr/bin/env python3
"""Generate standard-compliant SBOM artifacts (SPDX 2.3 JSON and CycloneDX 1.6 JSON)

Covers:
- Application package metadata and licensing (MIT)
- Python dependency ecosystem (Pillow, qrcode, pytest, playwright, pyee, greenlet)
- System tools (poppler-utils, pdftoppm, pdftotext)
- Front-end math & font assets (KaTeX)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Package definition registry
PACKAGES = [
    {
        "name": "ap-physics",
        "version": "1.2.0",
        "description": "Step-by-step interactive audio solutions and authoring skill for AP Physics C",
        "license": "MIT",
        "supplier": "Person: Sethu Srinivasan",
        "homepage": "https://sethusrinivasan.github.io/ap-physics/",
        "purl": "pkg:github/sethusrinivasan/ap-physics@1.2.0",
        "type": "application",
    },
    {
        "name": "playwright",
        "version": "1.64.1",
        "description": "Chromium, Firefox, and WebKit browser automation library",
        "license": "Apache-2.0",
        "supplier": "Organization: Microsoft",
        "homepage": "https://playwright.dev",
        "purl": "pkg:pypi/playwright@1.64.1",
        "type": "library",
    },
    {
        "name": "pytest",
        "version": "9.1.1",
        "description": "pytest: simple powerful testing with Python",
        "license": "MIT",
        "supplier": "Organization: pytest-dev",
        "homepage": "https://pytest.org",
        "purl": "pkg:pypi/pytest@9.1.1",
        "type": "library",
    },
    {
        "name": "Pillow",
        "version": "12.1.1",
        "description": "Python Imaging Library (Fork)",
        "license": "HPND",
        "supplier": "Organization: Jeffrey A. Clark (Alex) and contributors",
        "homepage": "https://python-pillow.org",
        "purl": "pkg:pypi/pillow@12.1.1",
        "type": "library",
    },
    {
        "name": "qrcode",
        "version": "8.2",
        "description": "QR Code image generator with SVG and PNG output",
        "license": "BSD-3-Clause",
        "supplier": "Person: Lincoln Loop",
        "homepage": "https://github.com/lincolnloop/python-qrcode",
        "purl": "pkg:pypi/qrcode@8.2",
        "type": "library",
    },
    {
        "name": "poppler-utils",
        "version": "26.01.0",
        "description": "PDF rendering and text extraction utilities (pdftoppm, pdftotext)",
        "license": "GPL-2.0-or-later",
        "supplier": "Organization: freedesktop.org",
        "homepage": "https://poppler.freedesktop.org/",
        "purl": "pkg:deb/debian/poppler-utils@26.01.0",
        "type": "operating-system",
    },
    {
        "name": "katex",
        "version": "0.16.11",
        "description": "Fast math typesetting library for the web",
        "license": "MIT",
        "supplier": "Organization: KaTeX Team",
        "homepage": "https://katex.org/",
        "purl": "pkg:npm/katex@0.16.11",
        "type": "library",
    },
]


def generate_spdx(output_path: Path) -> dict:
    """Generate SPDX 2.3 JSON standard SBOM."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_namespace = f"https://github.com/sethusrinivasan/ap-physics/spdx/{uuid.uuid4()}"

    spdx_packages = []
    relationships = []

    for idx, pkg in enumerate(PACKAGES):
        spdx_id = f"SPDXRef-Package-{idx+1}-{pkg['name'].replace('.', '-').replace('_', '-')}"
        spdx_packages.append({
            "SPDXID": spdx_id,
            "name": pkg["name"],
            "versionInfo": pkg["version"],
            "summary": pkg["description"],
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "homepage": pkg["homepage"],
            "licenseConcluded": pkg["license"],
            "licenseDeclared": pkg["license"],
            "supplier": pkg["supplier"],
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": pkg["purl"],
                }
            ],
        })

        if idx == 0:
            relationships.append({
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": spdx_id,
            })
        else:
            relationships.append({
                "spdxElementId": "SPDXRef-Package-1-ap-physics",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": spdx_id,
            })

    spdx_doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "ap-physics-sbom",
        "documentNamespace": doc_namespace,
        "creationInfo": {
            "created": now,
            "creators": [
                "Tool: ap-physics-sbom-generator-1.0",
                "Organization: Google Gemini / DeepMind Antigravity Pair",
            ],
            "licenseListVersion": "3.23",
        },
        "packages": spdx_packages,
        "relationships": relationships,
    }

    output_path.write_text(json.dumps(spdx_doc, indent=2) + "\n", encoding="utf-8")
    return spdx_doc


def generate_cyclonedx(output_path: Path) -> dict:
    """Generate CycloneDX 1.6 JSON standard SBOM."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    serial_number = f"urn:uuid:{uuid.uuid4()}"

    components = []
    for pkg in PACKAGES[1:]:  # Primary component in metadata
        components.append({
            "type": pkg["type"],
            "name": pkg["name"],
            "version": pkg["version"],
            "description": pkg["description"],
            "purl": pkg["purl"],
            "licenses": [{"license": {"id": pkg["license"]}}],
            "externalReferences": [{"type": "website", "url": pkg["homepage"]}],
        })

    root_pkg = PACKAGES[0]
    cdx_doc = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": now,
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": "ap-physics-sbom-generator",
                        "version": "1.0",
                    }
                ]
            },
            "component": {
                "type": root_pkg["type"],
                "name": root_pkg["name"],
                "version": root_pkg["version"],
                "description": root_pkg["description"],
                "purl": root_pkg["purl"],
                "licenses": [{"license": {"id": root_pkg["license"]}}],
            },
        },
        "components": components,
    }

    output_path.write_text(json.dumps(cdx_doc, indent=2) + "\n", encoding="utf-8")
    return cdx_doc


def main() -> None:
    spdx_file = REPO_ROOT / "sbom.spdx.json"
    cdx_file = REPO_ROOT / "sbom.cdx.json"

    print("▶ Generating SPDX 2.3 SBOM...")
    generate_spdx(spdx_file)
    print(f"  ✔ Saved SPDX 2.3 SBOM: {spdx_file.name} ({spdx_file.stat().st_size} bytes)")

    print("▶ Generating CycloneDX 1.6 SBOM...")
    generate_cyclonedx(cdx_file)
    print(f"  ✔ Saved CycloneDX 1.6 SBOM: {cdx_file.name} ({cdx_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
