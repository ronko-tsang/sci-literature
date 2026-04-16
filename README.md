# Sci-Literature — Master Literature Review System v1.0

Deep-read SCI literature with rigorous citation tracing and evidence audit.

## Core Value

- **12 Literature Review Skills**: From source identification to citation-controlled writing
- **Evidence Auditor**: Trace every claim to primary source
- **Knowledge Architect**: Build literature networks, not lists
- **Citation Controller**: Prevent citation pollution

## Mental Model

```
Review paper = MAP
Primary paper = GROUND TRUTH
Embedding = SEARCH
Citation = EVIDENCE LINK
Graph = KNOWLEDGE STRUCTURE
```

**Your role**: NOT summarizer, BUT evidence auditor, knowledge architect, citation controller.

## Quick Start

### Installation

```bash
git clone https://github.com/ronko-tsang/sci-literature.git
cd sci-literature
bash setup.sh
```

### For Claude Code

```bash
cp -r sci-literature ~/.claude/skills/sci-literature
```

### For OpenCode

OpenCode supports `~/.claude/skills/` for Claude compatibility:

```bash
cp -r sci-literature ~/.claude/skills/sci-literature
```

Or use the OpenCode skills CLI (recommended):

```bash
npx skills add ronko-tsang/sci-literature -y
```

Or install manually to OpenCode's own path:

```bash
cp -r sci-literature ~/.config/opencode/skill/sci-literature
```

### For OpenClaw

```bash
cp -r sci-literature ~/.openclaw/skills/sci-literature
openclaw hooks enable sci-literature  # Optional hook
```

## Usage

### Direct Triggers

```
> 精读这篇PDF: /path/to/paper.pdf
> 对比分析这些文献
> 找出研究空白
> 追踪这个引用链
> 帮我做知识图谱
> 审计证据
```

### CLI Commands

```bash
# Full pipeline
python scripts/tool.py all --folder ./pdfs --output ./results

# Extract only
python scripts/tool.py extract --folder ./pdfs --output ./results

# Compare analysis
python scripts/tool.py compare --output ./results

# Knowledge graph
python scripts/tool.py build-kg --output ./results

# RAG Q&A
python scripts/tool.py ask "研究空白有哪些？" --output ./results
```

## The 12 Literature Review Skills

| # | Skill | Purpose |
|---|-------|---------|
| 1 | Source Type Identification | Tag papers: Primary \| Review \| Meta |
| 2 | Claim-Level Reading | Extract claim/evidence/citation per paragraph |
| 3 | Review → Primary Trace | Trace review citations to original papers |
| 4 | Citation Chaining | Backward + Forward search |
| 5 | Anti-Citation Pollution | Replace reviews with primary sources |
| 6 | Structured Extraction | Extract question/method/findings/limitations |
| 7 | Cross-Paper Synthesis | Group by claims, methods, gaps |
| 8 | Evidence Mapping | Build evidence structure table |
| 9 | Citation Validation | Verify original supports claim |
| 10 | Knowledge Graph | Build network of papers/claims/methods |
| 11 | Embedding-Aware Retrieval | Claim-based similarity search |
| 12 | Citation-Controlled Writing | One claim + multiple primary citations |

## Pipeline

```
PDFs → extract → papers.jsonl (streamed, one line per paper)
                    ↓
          compare → compare_report.md
                    ↓
          build-kg → knowledge_graph.json + obsidian_notes/*.md
                    ↓
             ask → Q&A with [bib_key] citations
```

## Citation Standards

| Level | Source | Use For |
|-------|--------|---------|
| ++ | RCT, Meta-analysis | Strong claims |
| + | Cohort, longitudinal | Moderate claims |
| - | Case-control, cross-sectional | Weak claims |
| ? | Opinion, non-peer-reviewed | Avoid |

**Rule**: Max 20% review citations. Everything else must be primary.

## Configuration

Edit `config.yaml`:

```yaml
api:
  provider: "minimax"      # minimax | zhipu | deepseek | tongyi | moonshot
  api_key: "YOUR_API_KEY"
  model: "MiniMax-M2.7-highspeed"
  base_url: "https://api.minimaxi.com/v1"
```

## Project Structure

```
sci-literature/
├── _meta.json              # Skill metadata
├── SKILL.md                # Agent-facing skill guide
├── HOW-TO-USE.md           # Platform-specific usage
├── setup.sh                # Installation script
├── README.md               # This file
├── LICENSE                 # MIT License
│
├── assets/
│   ├── requirements.txt    # Python dependencies
│   └── config.example.yaml # Config template
│
├── scripts/
│   └── tool.py             # Main CLI tool
│
├── references/
│   ├── citation-tracing-guide.md
│   └── evidence-audit-guide.md
│
└── hooks/
    └── openclaw/
        ├── HOOK.md
        └── handler.js
```

## Version History

- **v1.0**: 12 literature review skills, opencode/claude/openclaw support, hook integration

---

*Evidence Auditor | Knowledge Architect | Citation Controller*