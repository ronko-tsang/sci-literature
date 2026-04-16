#!/usr/bin/env python3
"""
SCI Literature Deep-Read Toolkit for Biomedical Research v4.0

A professional-grade SCI paper analysis toolkit for biomedical literature,
with bioinformatics depth, statistical rigor, and cross-paper synthesis.
"""
import os
import sys
import json
import yaml
import click
import glob
import time
import re
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

import fitz
import requests

VERSION = "4.0"

IS_TTY = sys.stdout.isatty()
DEBUG = os.getenv("DEBUG", "0") == "1"


def log(*args, **kwargs):
    """Safe print in tqdm environment to avoid progress bar conflicts."""
    msg = " ".join(str(a) for a in args)
    if IS_TTY:
        try:
            tqdm.write(msg)
        except Exception:
            print(msg, **kwargs)
    else:
        print(msg, **kwargs)


def debug(*args):
    """Debug-level logging (only when DEBUG=1)."""
    if DEBUG:
        log("[DEBUG]", *args)


# =============================================================================
# Configuration
# =============================================================================

API_PROVIDERS = {
    "minimax": {
        "base_url": "https://api.minimaxi.com/v1",
        "model": "MiniMax-M2.7-highspeed",
        "description": "MiniMax",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "model": "glm-4-plus",
        "description": "Zhipu GLM-4",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "description": "DeepSeek",
    },
    "tongyi": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-max",
        "description": "Tongyi Qwen",
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-128k",
        "description": "Moonshot Kimi",
    },
}


def load_config() -> dict:
    """Load configuration from config.yaml or config.example.yaml."""
    skill_root = Path(__file__).parent.parent
    config_path = skill_root / "config.yaml"
    if not config_path.exists():
        config_path = skill_root / "assets" / "config.example.yaml"
        debug(f"config.yaml not found, using config.example.yaml")
    else:
        debug(f"Using config: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm_config(config: dict) -> dict:
    """Get LLM configuration from config dict."""
    provider = config.get("api", {}).get("provider", "minimax")
    api_key = config.get("api", {}).get("api_key", "")
    base_url = config.get("api", {}).get("base_url", "")
    model = config.get("api", {}).get("model", "")

    provider_config = API_PROVIDERS.get(provider, API_PROVIDERS["minimax"])
    base_url = base_url or provider_config["base_url"]
    model = model or provider_config["model"]

    return {
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "provider": provider,
        "provider_description": provider_config["description"],
    }


# =============================================================================
# LLM API Calls
# =============================================================================

def call_llm(
    config: dict, prompt: str, temperature: float = 0.1, max_tokens: int = 8000
) -> str:
    """Call LLM API with given prompt. Returns response text or empty string on failure."""
    cfg = get_llm_config(config)

    if not cfg["api_key"]:
        log("    ERROR: API key not configured. Check config.yaml")
        return ""

    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    data = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        debug(f"    [API] Provider: {cfg['provider']} ({cfg['provider_description']})")
        debug(f"    [API] Model: {cfg['model']}")
        debug(f"    [API] Endpoint: {cfg['base_url']}/chat/completions")

        response = requests.post(
            f"{cfg['base_url']}/chat/completions",
            headers=headers,
            json=data,
            timeout=120,
        )

        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            if "</think>" in content:
                parts = content.split("
</think>

")
                content = parts[-1].strip()
            return content
        elif response.status_code == 401:
            log(f"    API Error [401]: Invalid or expired API key")
            log(f"    Check api_key in config.yaml")
            return ""
        elif response.status_code == 403:
            log(f"    API Error [403]: Access denied. Check API key permissions")
            return ""
        elif response.status_code == 429:
            log(f"    API Error [429]: Rate limited. Please retry later")
            return ""
        elif response.status_code >= 500:
            log(f"    API Error [{response.status_code}]: Server error. Retry later")
            return ""
        else:
            log(f"    API Error: {response.status_code} - {response.text[:200]}")
            return ""

    except requests.exceptions.Timeout:
        log(f"    Request timeout: API did not respond within 120 seconds")
        return ""
    except requests.exceptions.ConnectionError as e:
        log(f"    Connection failed: Unable to reach API endpoint")
        debug(f"    Error detail: {e}")
        return ""
    except Exception as e:
        log(f"    Request failed: {e}")
        return ""


def fix_json(text: str) -> str:
    """Fix common JSON errors from truncated LLM responses."""
    text = text.strip()

    # Fix truncated JSON (missing closing } or ])
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    if open_braces > 0:
        text += "}" * open_braces
    if open_brackets > 0:
        text += "]" * open_brackets

    # Remove trailing comma before } or ]
    text = text.rstrip().rstrip(",")
    if not text.endswith("}") and not text.endswith("]"):
        last_valid_pos = max(text.rfind("}"), text.rfind("]"))
        if last_valid_pos > 0:
            text = text[: last_valid_pos + 1]

    # Fix quote issues
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        if line.count('"') % 2 != 0:
            line = line.rstrip().rstrip('",')
        fixed_lines.append(line)
    text = "\n".join(fixed_lines)

    return text


def extract_json_objects(text: str) -> list:
    """Extract all complete JSON objects from text using depth tracking."""
    objects = []
    depth = 0
    start = -1

    for i, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj_text = text[start : i + 1]
                    obj = json.loads(obj_text)
                    objects.append(obj)
                    start = -1
                except json.JSONDecodeError:
                    start = -1
    return objects


def call_llm_json(config: dict, prompt: str) -> dict:
    """Call LLM and parse JSON response with automatic repair."""
    text = call_llm(config, prompt, max_tokens=12000)
    if not text:
        return {"error": "API call failed"}

    try:
        text = text.strip()
        if "```json" in text:
            parts = text.split("```json")
            text = parts[-1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            text = parts[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        debug(f"    Direct JSON parse failed, attempting repair...")

    fixed = fix_json(text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        debug(f"    JSON repair failed, extracting partial objects...")

    objects = extract_json_objects(text)
    if objects:
        for obj in objects:
            if any(k in obj for k in ("method", "conclusion", "limitation", "bioinformatics")):
                debug(f"    Successfully extracted partial JSON object")
                return obj

    log(f"    JSON parse failed. Raw response (first 300 chars): {text[:300]}...")
    return {"error": text[:500]}


# =============================================================================
# PDF Processing
# =============================================================================

def extract_text(pdf_path: str) -> str:
    """Extract text content from PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_metadata(pdf_path: str) -> dict:
    """Extract metadata from PDF. Falls back to filename if no metadata."""
    doc = fitz.open(pdf_path)
    meta = doc.metadata
    doc.close()

    title = meta.get("title", "").strip()
    author = meta.get("author", "").strip()
    subject = meta.get("subject", "").strip()

    # Try to extract year from subject (sometimes contains "2024")
    year = None
    year_match = re.search(r'\b(19|20)\d{2}\b', subject)
    if year_match:
        year = int(year_match.group())

    # Fallback: extract from filename
    if not title:
        title = os.path.basename(pdf_path).replace(".pdf", "").replace("_copy", "")

    # Parse author list
    authors = []
    if author:
        # Split by common delimiters
        parts = re.split(r'[,;]|\band\b', author)
        authors = [a.strip() for a in parts if a.strip()]

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "subject": subject,
    }


def generate_bib_key(title: str, authors: list, year: int = None) -> str:
    """
    Generate a unique bibliography key from paper metadata.

    Format: {first_author_last_name}{year}_{first_letters_of_title}
    Example: smith2024_deep
    """
    author_part = ""
    if authors and authors[0]:
        name = authors[0].split()[-1] if authors else ""
        author_part = re.sub(r"[^a-zA-Z]", "", name).lower()[:10]

    title_part = re.sub(r"[^a-zA-Z]", "", title).lower()[:10]

    # Use provided year or current year as fallback
    year_str = str(year) if year else time.strftime("%Y")

    return f"{author_part}{year_str}_{title_part}"


def extract_paper_info(config: dict, pdf_path: str, delay: float = 1.0) -> dict:
    """
    Extract structured information from a scientific paper PDF.

    Uses domain-specific prompting for biomedical/bioinformatics papers
    to capture: methods, findings, statistical rigor, reproducibility,
    and bioinformatics-specific fields.
    """
    filename = os.path.basename(pdf_path)
    log(f"  Processing: {filename[:50]}...")

    for attempt in range(2):
        try:
            text = extract_text(pdf_path)
            metadata = extract_metadata(pdf_path)

            if len(text) < 100:
                log(f"    WARNING: Text too short ({len(text)} chars) for {filename}")
                return None

            bib_key = generate_bib_key(
                metadata["title"],
                metadata["authors"],
                metadata["year"]
            )

            # Domain-specific extraction prompt for biomedical/bioinformatics research
            prompt = f"""You are a senior biomedical researcher specializing in bioinformatics and computational biology.
Extract structured information from the following scientific paper. Return ONLY valid JSON.

Paper Title: {metadata["title"]}
Authors: {", ".join(metadata["authors"]) if metadata["authors"] else "Unknown"}
Year: {metadata["year"] or "Unknown"}

Paper Content (truncated to 8000 chars):
{text[:8000]}

Extract the following information and return standard JSON:

{{
  "method": {{
    "research_method": "Detailed description of the research methodology",
    "approach_type": "experimental|computational|hybrid|review|meta-analysis",
    "data_sources": "public_dataset|private_data|simulated|mixed",
    "sample_size": {{
      "n": "number or 'not reported' or 'N/A'",
      "description": "brief description of cohort/sample"
    }},
    "statistical_power": "percentage (e.g. '80%') or 'not reported' or 'N/A'",
    "effect_size_reported": true,
    "confidence_intervals": true,
    "bioinformatics": {{
      "sequencing_platform": "e.g. Illumina NovaSeq, Oxford Nanopore, PacBio, not applicable",
      "sequencing_depth": "e.g. '30M reads per sample' or 'not applicable'",
      "pipeline_version": "e.g. Seurat v5.1, CellRanger 7.1, or 'not applicable'",
      "database_versions": ["e.g. Ensembl 104", "UCSC hg38"],
      "software_versions": {{"key": "value"}},
      "code_available": true,
      "data_availability": "e.g. GEO GSE123456, PRIDE PXD123456, or 'not available'"
    }}
  }},
  "conclusion": {{
    "main_findings": ["Finding 1", "Finding 2", "Finding 3"],
    "novelty": "What is genuinely new vs incremental contributions",
    "comparison_prior_art": "How findings compare with prior literature"
  }},
  "limitation": {{
    "limitations": ["Limitation 1", "Limitation 2", "Limitation 3"],
    "suggested_remedies": ["How to address each limitation"],
    "reproducibility_concerns": ["What would make reproduction difficult"]
  }},
  "reproducibility": {{
    "code_available": true,
    "data_available": true,
    "public_dataset": "Accession number if available",
    "software_open_source": true
  }}
}}

Requirements:
1. Return ONLY JSON, no explanations or comments
2. Ensure JSON is valid and parseable by json.loads()
3. If a field is not applicable or not mentioned, use null or empty array
4. For bioinformatics papers, fill the 'bioinformatics' section
5. For non-bioinformatics papers, set bioinformatics fields to null or 'not applicable'
6. Include at least 3 findings in main_findings if available"""

            result = call_llm_json(config, prompt)
            time.sleep(delay)

            if result.get("error"):
                debug(f"    Error response: {str(result.get('error'))[:200]}")
                if attempt == 0:
                    log(f"    Retrying...")
                    continue
                log(f"    Extraction failed")
                return None

            # Normalize nested fields
            method = result.get("method", {})
            conclusion = result.get("conclusion", {})
            limitation = result.get("limitation", {})
            reproducibility = result.get("reproducibility", {})
            bioinfo = method.get("bioinformatics", {})

            # Normalize finding field names
            if "main_findings" not in conclusion:
                conclusion["main_findings"] = result.get(
                    "findings",
                    result.get("key_findings", conclusion.get("main_findings", []))
                )

            # Normalize limitation field names
            if "limitations" not in limitation:
                limitation["limitations"] = result.get(
                    "limit", result.get("limits", limitation.get("limitations", []))
                )

            # Normalize method field names
            method.setdefault(
                "research_method",
                method.get("technique", method.get("methodology", ""))
            )
            method.setdefault(
                "approach_type",
                method.get("method_type", method.get("approach", ""))
            )
            method.setdefault("data_sources", method.get("data_source", ""))

            # Ensure bioinformatics section exists
            if "bioinformatics" not in method:
                method["bioinformatics"] = bioinfo if bioinfo else {}

            return {
                "bib_key": bib_key,
                "title": metadata["title"],
                "authors": metadata["authors"],
                "year": metadata["year"],
                "pdf_path": pdf_path,
                "method": method,
                "conclusion": conclusion,
                "limitation": limitation,
                "reproducibility": reproducibility,
                "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as e:
            log(f"    Processing failed for {filename}: {e}")
            return None

    return None


# =============================================================================
# Storage (JSONL - memory efficient)
# =============================================================================

def save_papers_jsonl(papers: list, output_dir: str):
    """
    Save papers to JSONL format (one JSON object per line).

    This is memory-efficient compared to JSON array - papers are streamed
    to disk and can be processed incrementally without loading all into memory.
    """
    os.makedirs(output_dir, exist_ok=True)
    jsonl_path = f"{output_dir}/papers.jsonl"

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for paper in papers:
            # Don't save full_text to JSONL - it's too large
            paper_copy = {k: v for k, v in paper.items() if k != "full_text"}
            f.write(json.dumps(paper_copy, ensure_ascii=False) + "\n")

    # Also save individual JSON files for each paper (useful for Obsidian)
    for paper in papers:
        bib_key = paper.get("bib_key", "unknown")
        paper_copy = {k: v for k, v in paper.items() if k != "full_text"}
        with open(f"{output_dir}/{bib_key}.json", "w", encoding="utf-8") as f:
            json.dump(paper_copy, f, ensure_ascii=False, indent=2)


def load_papers_jsonl(output_dir: str) -> list:
    """
    Load papers from JSONL format.

    For large collections, consider using iter_papers_jsonl() instead
    to process papers incrementally.
    """
    jsonl_path = f"{output_dir}/papers.jsonl"
    papers = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                papers.append(json.loads(line))
    return papers


def iter_papers_jsonl(output_dir: str):
    """
    Iterate over papers in JSONL format without loading all into memory.

    Yields one paper dict at a time.
    """
    jsonl_path = f"{output_dir}/papers.jsonl"
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


# =============================================================================
# Knowledge Graph Builder
# =============================================================================

def build_knowledge_graph(papers: list, output_dir: str) -> dict:
    """
    Build a knowledge graph from extracted papers.

    Nodes: papers, authors, methods, findings, concepts, pathways, research gaps
    Edges: authored, uses_method, has_finding, relates_to, addresses, contradicts, supports, extends
    """
    os.makedirs(output_dir, exist_ok=True)
    obsidian_dir = f"{output_dir}/obsidian_notes"
    os.makedirs(obsidian_dir, exist_ok=True)

    kg_data = {"nodes": [], "edges": []}
    node_ids = {}  # Track existing nodes to avoid duplicates

    def get_node_id(node_type: str, name: str) -> str:
        """Get or create a unique node ID for a given type and name."""
        key = f"{node_type}:{name}"
        if key not in node_ids:
            node_id = f"{node_type}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
            node_ids[key] = node_id
            kg_data["nodes"].append({"id": node_id, "type": node_type, "name": name})
        return node_ids[key]

    for paper in papers:
        bib_key = paper.get("bib_key", "")
        title = paper.get("title", "")
        authors = paper.get("authors", [])
        method = paper.get("method", {})
        conclusion = paper.get("conclusion", {})
        limitation = paper.get("limitation", {})

        # Paper node
        paper_node_id = f"paper_{bib_key}"
        kg_data["nodes"].append({
            "id": paper_node_id,
            "type": "paper",
            "title": title,
            "year": paper.get("year")
        })

        # Author nodes
        for author in authors:
            if author:
                author_id = get_node_id("author", author)
                kg_data["edges"].append({
                    "source": author_id,
                    "target": paper_node_id,
                    "relation": "authored"
                })

        # Method node
        method_type = method.get("approach_type", "")
        if method_type:
            method_id = get_node_id("method", method_type)
            kg_data["edges"].append({
                "source": paper_node_id,
                "target": method_id,
                "relation": "uses_method"
            })

            # Research method detail
            research_method = method.get("research_method", "")
            if research_method and research_method != method_type:
                rm_id = get_node_id("technique", research_method[:50])
                kg_data["edges"].append({
                    "source": method_id,
                    "target": rm_id,
                    "relation": "has_technique"
                })

        # Bioinformatics-specific nodes
        bioinfo = method.get("bioinformatics", {})
        if bioinfo:
            seq_platform = bioinfo.get("sequencing_platform", "")
            if seq_platform and seq_platform != "not applicable":
                platform_id = get_node_id("platform", seq_platform)
                kg_data["edges"].append({
                    "source": paper_node_id,
                    "target": platform_id,
                    "relation": "uses_platform"
                })

        # Finding nodes
        for i, finding in enumerate(conclusion.get("main_findings", [])[:5]):
            finding_id = f"finding_{bib_key}_{i}"
            kg_data["nodes"].append({
                "id": finding_id,
                "type": "finding",
                "content": finding[:200]  # Truncate for KG
            })
            kg_data["edges"].append({
                "source": paper_node_id,
                "target": finding_id,
                "relation": "has_finding"
            })

        # Limitation nodes
        for i, limitation_text in enumerate(limitation.get("limitations", [])[:3]):
            limitation_id = f"limitation_{bib_key}_{i}"
            kg_data["nodes"].append({
                "id": limitation_id,
                "type": "limitation",
                "content": limitation_text[:200]
            })
            kg_data["edges"].append({
                "source": paper_node_id,
                "target": limitation_id,
                "relation": "has_limitation"
            })

        # Generate Obsidian note for this paper
        md_content = f"""# {title}

## Metadata
- **BibKey**: {bib_key}
- **Authors**: {", ".join(authors) if authors else "Unknown"}
- **Year**: {paper.get("year", "Unknown")}
- **PDF**: {paper.get("pdf_path", "")}

## Research Method
- **Type**: {method.get("approach_type", "Unknown")}
- **Method**: {method.get("research_method", "Unknown")}
- **Data Sources**: {method.get("data_sources", "Unknown")}
- **Sample Size**: {method.get("sample_size", {}).get("n", "Not reported")}

## Bioinformatics Details
{_format_bioinfo(bioinfo)}

## Main Findings
{chr(10).join(f"- {f}" for f in conclusion.get("main_findings", [])[:5])}

## Novelty
{conclusion.get("novelty", "Not assessed")}

## Limitations
{chr(10).join(f"- {l}" for l in limitation.get("limitations", [])[:3])}

## Suggested Remedies
{chr(10).join(f"- {r}" for r in limitation.get("suggested_remedies", [])[:3])}

## Reproducibility
- **Code Available**: {reproducibility.get("code_available", "Unknown")}
- **Data Available**: {reproducibility.get("data_available", "Unknown")}
- **Public Dataset**: {reproducibility.get("public_dataset", "Not available")}

## Extracted
{_format_bioinfo(paper.get("extracted_at", ""))}
"""

        with open(f"{obsidian_dir}/{bib_key}.md", "w", encoding="utf-8") as f:
            f.write(md_content)

    # Add cross-paper comparison edges (contradictions, supports)
    _add_comparison_edges(kg_data, papers)

    # Save knowledge graph
    with open(f"{output_dir}/knowledge_graph.json", "w", encoding="utf-8") as f:
        json.dump(kg_data, f, ensure_ascii=False, indent=2)

    # Save Obsidian index
    with open(f"{obsidian_dir}/INDEX.md", "w", encoding="utf-8") as f:
        f.write("# Literature Notes Index\n\n")
        for paper in papers:
            f.write(f"- [[{paper.get('bib_key', '')}]] — {paper.get('title', '')}\n")

    return kg_data


def _format_bioinfo(bioinfo: dict) -> str:
    """Format bioinformatics details for Obsidian note."""
    if not bioinfo:
        return "_No bioinformatics details available_"

    lines = []
    if bioinfo.get("sequencing_platform"):
        lines.append(f"  - **Platform**: {bioinfo['sequencing_platform']}")
    if bioinfo.get("sequencing_depth"):
        lines.append(f"  - **Depth**: {bioinfo['sequencing_depth']}")
    if bioinfo.get("pipeline_version"):
        lines.append(f"  - **Pipeline**: {bioinfo['pipeline_version']}")
    if bioinfo.get("database_versions"):
        lines.append(f"  - **Databases**: {', '.join(bioinfo['database_versions'])}")
    if bioinfo.get("code_available") is not None:
        lines.append(f"  - **Code Available**: {'Yes' if bioinfo['code_available'] else 'No'}")
    if bioinfo.get("data_availability"):
        lines.append(f"  - **Data**: {bioinfo['data_availability']}")

    return "\n".join(lines) if lines else "_No bioinformatics details available_"


def _add_comparison_edges(kg_data: dict, papers: list):
    """
    Add cross-paper comparison edges to knowledge graph.

    Analyzes paper pairs for contradictions and support relationships.
    Note: This is a simplified version. For production, consider using
    LLM-based comparison for more accurate relationship detection.
    """
    # Build finding index
    paper_findings = {}
    for paper in papers:
        bib_key = paper.get("bib_key", "")
        findings = paper.get("conclusion", {}).get("main_findings", [])
        paper_findings[bib_key] = findings

    # Track added edges to avoid duplicates
    added_edges = set()

    # Simple keyword-based contradiction detection
    # In production, use LLM for accurate comparison
    contradiction_keywords = [
        ("increase", "decrease"),
        ("upregulate", "downregulate"),
        ("activate", "inhibit"),
        ("significant", "not significant"),
        ("positive", "negative"),
    ]

    for i, (bib_a, findings_a) in enumerate(paper_findings.items()):
        for j, (bib_b, findings_b) in enumerate(paper_findings.items()):
            if i >= j:
                continue

            paper_a_id = f"paper_{bib_a}"
            paper_b_id = f"paper_{bib_b}"

            edge_key = tuple(sorted([paper_a_id, paper_b_id]))
            if edge_key in added_edges:
                continue

            # Check for contradictions
            for kw1, kw2 in contradiction_keywords:
                found_kw1_a = any(kw1.lower() in str(f).lower() for f in findings_a)
                found_kw2_a = any(kw2.lower() in str(f).lower() for f in findings_a)
                found_kw1_b = any(kw1.lower() in str(f).lower() for f in findings_b)
                found_kw2_b = any(kw2.lower() in str(f).lower() for f in findings_b)

                if (found_kw1_a and found_kw2_b) or (found_kw2_a and found_kw1_b):
                    kg_data["edges"].append({
                        "source": paper_a_id,
                        "target": paper_b_id,
                        "relation": "contradicts"
                    })
                    added_edges.add(edge_key)
                    break
            else:
                # If no contradiction found but both papers have findings, mark as related
                if findings_a and findings_b:
                    kg_data["edges"].append({
                        "source": paper_a_id,
                        "target": paper_b_id,
                        "relation": "related"
                    })
                    added_edges.add(edge_key)


# =============================================================================
# CLI Commands
# =============================================================================

@click.group()
@click.version_option(version=VERSION, prog_name="sci-literature")
def cli():
    """SCI Literature Deep-Read Toolkit v{version}

    A professional-grade SCI paper analysis toolkit for biomedical literature,
    with bioinformatics depth, statistical rigor, and cross-paper synthesis.
    """.format(version=VERSION)


@cli.command()
@click.option("--folder", "-f", default="./my_pdfs", help="PDF folder path")
@click.option("--output", "-o", default="./extracted", help="Output directory")
@click.option("--workers", "-w", default=2, help="Parallel workers (macOS: use 1-2)")
def extract(folder: str, output: str, workers: int):
    """Extract structured information from PDFs."""
    config = load_config()
    pdf_files = glob.glob(os.path.join(folder, "*.pdf"))

    if not pdf_files:
        log(f"No PDF files found in: {folder}")
        return

    log(f"Found {len(pdf_files)} PDF files")
    papers = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(extract_paper_info, config, pdf): pdf for pdf in pdf_files
        }
        pbar = tqdm(
            total=len(futures),
            desc="Extracting papers",
            position=0,
            leave=True,
            dynamic_ncols=IS_TTY,
            unit="paper",
        )
        for future in as_completed(futures):
            result = future.result()
            if result:
                papers.append(result)
            pbar.update(1)
        pbar.close()

    log(f"\nSuccessfully extracted {len(papers)} papers")

    # Save as JSONL (memory-efficient)
    save_papers_jsonl(papers, output)

    log(f"\nData saved to: {output}/papers.jsonl")
    log(f"Individual papers: {output}/<bib_key>.json")


@cli.command()
@click.option("--output", "-o", default="./extracted", help="Output directory")
def compare(output: str):
    """Cross-paper comparative analysis: consensus, contradictions, gaps."""
    config = load_config()
    papers_file = f"{output}/papers.jsonl"

    if not os.path.exists(papers_file):
        log(f"No data found. Run extract first: {papers_file}")
        return

    log("Loading papers for comparison...")
    papers = load_papers_jsonl(output)
    log(f"Loaded {len(papers)} papers for comparison")

    findings = []
    limitations = []
    methods = []
    bioinfo_methods = []  # Track bioinformatics-specific methods

    for paper in papers:
        bib = paper.get("bib_key", "")
        conclusion = paper.get("conclusion", {})
        limitation = paper.get("limitation", {})
        method = paper.get("method", {})

        findings.append(
            f"[{bib}] {json.dumps(conclusion.get('main_findings', []), ensure_ascii=False)}"
        )
        limitations.append(
            f"[{bib}] {json.dumps(limitation.get('limitations', []), ensure_ascii=False)}"
        )

        method_str = method.get("research_method", method.get("approach_type", ''))
        methods.append(f"[{bib}] {method_str}")

        # Track bioinformatics details
        bioinfo = method.get("bioinformatics", {})
        if bioinfo and bioinfo.get("sequencing_platform"):
            bioinfo_methods.append(
                f"[{bib}] {bioinfo.get('sequencing_platform', 'N/A')} - "
                f"{bioinfo.get('pipeline_version', 'N/A')}"
            )

    # Build comparison prompt in English
    prompt = f"""You are a senior biomedical researcher. Perform deep comparative analysis of {len(papers)} SCI papers.

 PAPERS' FINDINGS
{chr(10).join(findings[:30])}

 PAPERS' METHODS
{chr(10).join(methods[:30])}

 PAPERS' LIMITATIONS
{chr(10).join(limitations[:30])}

BIOINFORMATICS METHODS (for computational papers)
{chr(10).join(bioinfo_methods[:20]) if bioinfo_methods else "No bioinformatics-specific details"}

Generate a Markdown comparative analysis report with these sections:

## 1. Research Consensus
What conclusions are supported across multiple papers? Cite specific papers using [bib_key].

## 2. Research Contradictions
Where do findings diverge or conflict? Analyze root causes.

## 3. Research Gaps
What areas or questions remain underexplored? Identify specific gaps.

## 4. Methodological Review
What are the strengths and weaknesses of each approach? Which methods are most rigorous?

## 5. Future Research Directions
Based on the analysis, what specific studies would advance the field?

Requirements:
1. Use English throughout
2. Cite papers using [bib_key] format
3. Be specific and analytical, not descriptive
4. Identify contradictions and tensions, not just summarize"""

    log("Generating comparative analysis report...")
    report = call_llm(config, prompt, temperature=0.2)

    os.makedirs(output, exist_ok=True)
    report_file = f"{output}/compare_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Comparative Analysis Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(report)

    log(f"\nReport saved to: {report_file}")
    log("\n=== Report Preview ===")
    log(report[:1500] + "...")


@cli.command()
@click.option("--output", "-o", default="./extracted", help="Output directory")
def build_kg(output: str):
    """Build knowledge graph and export Obsidian notes."""
    config = load_config()
    papers_file = f"{output}/papers.jsonl"

    if not os.path.exists(papers_file):
        log(f"No data found. Run extract first")
        return

    log("Loading papers for knowledge graph...")
    papers = load_papers_jsonl(output)
    log(f"Building knowledge graph for {len(papers)} papers...")

    kg_data = build_knowledge_graph(papers, output)

    log(f"\nKnowledge graph: {output}/knowledge_graph.json")
    log(f"Obsidian notes: {output}/obsidian_notes/")
    log(f"Nodes: {len(kg_data['nodes'])}, Edges: {len(kg_data['edges'])}")


@cli.command()
@click.argument("question")
@click.option("--output", "-o", default="./extracted", help="Output directory")
@click.option("--top-k", "-k", default=10, help="Number of papers to consider")
def ask(question: str, output: str, top_k: int):
    """Answer questions based on literature using RAG."""
    config = load_config()
    papers_file = f"{output}/papers.jsonl"

    if not os.path.exists(papers_file):
        log(f"No data found. Run extract first")
        return

    log(f"Searching through papers for answer...")

    # Stream papers and build context
    rag_context = ""
    paper_count = 0

    for paper in iter_papers_jsonl(output):
        if paper_count >= top_k:
            break

        rag_context += f"""
---
Paper {paper_count + 1}: {paper.get("title", "")}
Authors: {", ".join(paper.get("authors", [])[:3])}
Year: {paper.get("year", "Unknown")}
Method: {json.dumps(paper.get("method", {}), ensure_ascii=False)}
Findings: {json.dumps(paper.get("conclusion", {}), ensure_ascii=False)}
Limitations: {json.dumps(paper.get("limitation", {}), ensure_ascii=False)}
---"""
        paper_count += 1

    prompt = f"""You are a senior biomedical researcher. Answer the question based on the provided literature.

Question: {question}

{rag_context}

Requirements:
1. Answer in English
2. Cite specific papers using [bib_key] format
3. Be precise and accurate - don't add information not in the literature
4. Distinguish between strong evidence and speculative findings"""

    answer = call_llm(config, prompt, temperature=0.2)

    sep = "=" * 60
    log(f"\n{sep}")
    log(f"Question: {question}")
    log(f"{sep}")
    log(f"\nAnswer:\n{answer}")
    log(f"\n{sep}")

    os.makedirs(output, exist_ok=True)
    answer_file = f"{output}/ask_{int(time.time())}.md"
    with open(answer_file, "w", encoding="utf-8") as f:
        f.write(f"# Q&A Result\n\n**Question**: {question}\n\n**Answer**:\n{answer}\n\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    log(f"\nAnswer saved to: {answer_file}")


@cli.command()
@click.option("--folder", "-f", default="./my_pdfs", help="PDF folder path")
@click.option("--output", "-o", default="./extracted", help="Output directory")
@click.option("--workers", "-w", default=2, help="Parallel workers")
def all(folder: str, output: str, workers: int):
    """Run full pipeline: extract + compare + knowledge graph."""
    sep = "=" * 50
    log(sep)
    log("Full Deep-Read Pipeline")
    log(sep)

    config = load_config()
    pdf_files = glob.glob(os.path.join(folder, "*.pdf"))

    if not pdf_files:
        log(f"No PDF files found: {folder}")
        return

    # Step 1: Extract
    log(f"\n[1/3] Found {len(pdf_files)} PDFs, extracting...")
    papers = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(extract_paper_info, config, pdf): pdf for pdf in pdf_files
        }
        pbar = tqdm(
            total=len(futures),
            desc="Extracting papers",
            position=0,
            leave=True,
            dynamic_ncols=IS_TTY,
            unit="paper",
        )
        for future in as_completed(futures):
            result = future.result()
            if result:
                papers.append(result)
            pbar.update(1)
        pbar.close()

    log(f"\nSuccessfully extracted {len(papers)} papers")
    save_papers_jsonl(papers, output)

    # Step 2: Compare
    log(f"\n[2/3] Generating comparative analysis...")
    papers_file = f"{output}/papers.jsonl"

    if os.path.exists(papers_file):
        papers_data = load_papers_jsonl(output)

        findings = []
        limitations = []
        methods = []
        bioinfo_methods = []

        for paper in papers_data:
            bib = paper.get("bib_key", "")
            conclusion = paper.get("conclusion", {})
            limitation = paper.get("limitation", {})
            method = paper.get("method", {})

            findings.append(
                f"[{bib}] {json.dumps(conclusion.get('main_findings', []), ensure_ascii=False)}"
            )
            limitations.append(
                f"[{bib}] {json.dumps(limitation.get('limitations', []), ensure_ascii=False)}"
            )
            methods.append(
                f"[{bib}] {method.get('research_method', method.get('approach_type', ''))}"
            )

            bioinfo = method.get("bioinformatics", {})
            if bioinfo and bioinfo.get("sequencing_platform"):
                bioinfo_methods.append(
                    f"[{bib}] {bioinfo.get('sequencing_platform', 'N/A')} - "
                    f"{bioinfo.get('pipeline_version', 'N/A')}"
                )

        prompt = f"""You are a senior biomedical researcher. Perform deep comparative analysis of {len(papers_data)} SCI papers.

 PAPERS' FINDINGS
{chr(10).join(findings[:30])}

 PAPERS' METHODS
{chr(10).join(methods[:30])}

 PAPERS' LIMITATIONS
{chr(10).join(limitations[:30])}

BIOINFORMATICS METHODS
{chr(10).join(bioinfo_methods[:20]) if bioinfo_methods else "No bioinformatics-specific details"}

Generate a Markdown comparative analysis report with these sections:

## 1. Research Consensus
What conclusions are supported across multiple papers? Cite specific papers using [bib_key].

## 2. Research Contradictions
Where do findings diverge or conflict? Analyze root causes.

## 3. Research Gaps
What areas remain underexplored?

## 4. Methodological Review
Strengths and weaknesses of each approach.

## 5. Future Research Directions
Specific studies to advance the field.

Requirements:
1. Use English
2. Cite papers using [bib_key] format
3. Be analytical, not just descriptive"""

        log("Generating report...")
        report = call_llm(config, prompt, temperature=0.2)

        os.makedirs(output, exist_ok=True)
        report_file = f"{output}/compare_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"# Comparative Analysis Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(report)
        log(f"Report saved: {report_file}")

    # Step 3: Build KG
    log(f"\n[3/3] Building knowledge graph...")
    kg_data = build_knowledge_graph(papers, output)
    log(f"Knowledge graph: {output}/knowledge_graph.json")
    log(f"Obsidian notes: {output}/obsidian_notes/")

    log("\n" + sep)
    log("Pipeline complete!")
    log(f"Output directory: {output}")
    log(sep)


if __name__ == "__main__":
    cli()
