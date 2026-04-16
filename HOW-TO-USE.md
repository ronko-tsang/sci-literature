# How to Use Sci-Literature

## For OpenCode / Claude Code

### Installation

```bash
# Copy skill to opencode skills directory
cp -r sci-literature ~/.opencode/skills/sci-literature

# Or create symlink
ln -s /path/to/sci-literature ~/.opencode/skills/sci-literature
```

### Usage

After installation, the skill auto-loads when you ask literature-related questions.

**Direct triggers**:
```
> 精读这篇PDF: /path/to/paper.pdf
> 对比分析这些文献: ./papers.json
> 帮我做知识图谱
> 找出研究空白
> 追踪这个引用链
> 帮我审计证据
```

**Workflow**:
1. Provide paper PDFs or arXiv IDs
2. Agent applies 12 literature review skills
3. Structured data extracted → papers.jsonl
4. Cross-paper analysis generated
5. Knowledge graph built

### Tool Commands

```bash
# Extract from PDFs
python scripts/tool.py extract --folder ./pdfs --output ./results

# Full pipeline
python scripts/tool.py all --folder ./pdfs --output ./results

# Compare papers
python scripts/tool.py compare --output ./results

# Build knowledge graph
python scripts/tool.py build-kg --output ./results

# Ask questions
python scripts/tool.py ask "研究空白有哪些？" --output ./results
```

---

## For OpenClaw

### Installation

```bash
# Install skill
cp -r sci-literature ~/.openclaw/skills/sci-literature

# Enable hook (optional)
cp -r hooks/openclaw ~/.openclaw/hooks/sci-literature
openclaw hooks enable sci-literature
```

### Workspace Structure

OpenClaw creates these for literature work:

```
~/.openclaw/workspace/
├── LITERATURE.md          # This skill
├── papers/                # Paper summaries
├── literature/
│   ├── papers.jsonl      # Extracted data
│   ├── compare_report.md # Analysis
│   └── knowledge_graph.json
└── .learnings/           # Insights
```

### Direct Triggers

```
> analyze this paper: 10.1038/s41586-024-12345-6
> compare these two: paper1.pdf, paper2.pdf
> find research gaps in my literature
> build knowledge graph from papers.jsonl
> trace this citation: [15]
```

### Hook Events

- `agent:bootstrap` → Reminds to apply literature skills
- `command:new` → Fresh literature session

---

## Multi-Agent Literature Review

For complex literature reviews, use multiple agents:

### Agent 1: Paper Fetcher
- Downloads papers from arXiv, PubMed, PDF URLs
- Extracts text and metadata
- Saves to papers/

### Agent 2: Evidence Auditor
- Applies SKILL 1-6 (source ID, claim extraction, citation tracing)
- Builds papers.jsonl
- Validates evidence quality

### Agent 3: Synthesizer
- Applies SKILL 7-9 (cross-paper synthesis, evidence mapping)
- Generates compare_report.md
- Identifies gaps

### Agent 4: Knowledge Architect
- Applies SKILL 10-11 (knowledge graph, retrieval)
- Builds knowledge_graph.json
- Creates obsidian_notes/

---

## Citation Format

Use `[bib_key]` for citations:

```
Smith et al. [smith2024_ml] showed...
Multiple studies [smith2024_ml, jones2023_rna] confirm...
```

**bib_key format**: `{first_author_last_name}{year}_{title_abbrev}`

Example: `smith2024_deep` for "Smith et al. 2024 - Deep Learning in Genomics"

---

## Evidence Standards

| Level | Source | Use For |
|-------|--------|---------|
| ++ | RCT, Meta-analysis | Strong claims |
| + | Cohort, longitudinal | Moderate claims |
| - | Case-control, cross-sectional | Weak claims |
| ? | Opinion, non-peer-reviewed | Avoid |

---

## Common Workflows

### Systematic Review
1. Define research question
2. Apply SKILL 4 (citation chaining) for search
3. Apply SKILL 6 (structured extraction) to each paper
4. Apply SKILL 8 (evidence mapping)
5. Apply SKILL 12 (citation-controlled writing)

### Research Gap Analysis
1. Extract all papers → papers.jsonl
2. Apply SKILL 7 (cross-paper synthesis)
3. Identify where claims lack supporting evidence
4. Generate gap report

### Citation Audit
1. Load papers.jsonl
2. Apply SKILL 9 (citation validation)
3. Flag review-only citations
4. Apply SKILL 3 (trace to primary)
5. Generate cleaned citation report