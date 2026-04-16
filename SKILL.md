---
name: sci-literature
description: >
  Deep-read SCI literature with rigorous citation tracing and evidence audit.
  Use when: analyzing academic papers, literature review, systematic review,
  cross-paper synthesis, knowledge graph construction, citation chain validation,
  research gap analysis, or evidence mapping.

  Triggers: "精读文献" "对比分析" "知识图谱" "跨文献矛盾" "论文总结"
  "deep read" "compare literature" "build knowledge graph"
  "cross-paper contradiction" "literature review" "systematic review"
  "citation tracing" "evidence audit" "research gap"
  "statistical power" "reproducibility" "bioinformatics"

  This skill implements 12 core literature review skills:
  source identification, claim-level reading, review-to-primary tracing,
  citation chaining, anti-pollution, structured extraction, cross-paper
  synthesis, evidence mapping, citation validation, knowledge graph,
  embedding-aware retrieval, and citation-controlled writing.
user-invocable: true
author: Ronko
version: 1.0.0
---

# SCI Literature — Master Literature Review System v1.0

## Mental Model

```
Review paper = MAP
Primary paper = GROUND TRUTH
Embedding = SEARCH
Citation = EVIDENCE LINK
Graph = KNOWLEDGE STRUCTURE
```

**Your role**: NOT summarizer, BUT evidence auditor, knowledge architect, citation controller.

## Core Principles

1. **NEVER cite what you have not read**
2. **PRIORITIZE primary sources over secondary sources**
3. **REVIEW papers are ENTRY POINTS, not FINAL EVIDENCE**

```
Rule:
  If a claim is specific → cite ORIGINAL paper
  If a claim is general → cite REVIEW (sparingly)
```

---

# ==============================
# THE 12 LITERATURE REVIEW SKILLS
# ==============================

## SKILL 1: Source Type Identification

**Goal**: Tag each paper as Primary | Review | Meta-analysis

For each paper:
```
Tag = {Primary | Review | Meta}
```

---

## SKILL 2: Claim-Level Reading

**Goal**: Read by "claim" not by "article"

For each paragraph, extract:
- **Claim** — what the author is asserting
- **Evidence** — where the evidence comes from
- **Citation** — who is cited

Format:
```
Claim:
Supported by:
Citation:
```

**RULE**: ❌ No content understanding only ✅ Evidence location required

---

## SKILL 3: Review → Primary Trace (Core Skill 🔥)

**Goal**: Trace backwards from review citations to original papers

Workflow:
```
For each statement in REVIEW:

  Step 1: Identify citation number [X]
  Step 2: Jump to reference list
  Step 3: Retrieve ORIGINAL paper
  Step 4: Verify — does original REALLY support this claim?
  Step 5: Replace citation

  ❌ Review (wrong for evidence)
  ✅ Original paper (correct)
```

**Exception**: If citing interpretation/framework → cite BOTH (Original + Review)

---

## SKILL 4: Citation Chaining System

**Two directions**:

| Direction | Method | Goal |
|-----------|--------|------|
| **Backward** | Paper → References → older studies | Trace intellectual lineage |
| **Forward** | Paper → "Cited by" → newer studies | Find current impact |

**RULE**: Key claims must trace back to at least one layer of primary literature.

---

## SKILL 5: Anti-"Citation Pollution"

**Problem**:
```
❌ Same review cited 10+ times
❌ All evidence from reviews
❌ Citation堆砌 without primary evidence
```

**Solution**:
```
For each citation:
  IF source == review:
    → trace to primary
    → replace
```

**Rule**: Max review citation ratio: < 20%

---

## SKILL 6: Structured Extraction

**Goal**: Convert literature to structured information, not text understanding

For each PRIMARY paper extract:
```
- Research Question
- Method
- Key Findings
- Evidence Strength
- Limitations
```

Format:
```
Question:
Method:
Findings:
Evidence Strength:
Limitation:
```

**RULE**: ❌ No summary-only ✅ Must structurally拆解

---

## SKILL 7: Cross-Paper Synthesis

**Goal**: Move from single-paper reading to cross-literature integration

Group papers by:
- Similar claims
- Similar methods
- Same research question

Then analyze:
```
- Agreement (共识)
- Contradiction (冲突)
- Gap (缺口)
```

Format:
```
Claim X:
  Supporting:
    - Paper A
    - Paper B
  Contradicting:
    - Paper C
  Gap:
    - Missing / limited evidence
```

**RULE**: ❌ No paper-by-paper summary ✅ Must cross-reference integration

---

## SKILL 8: Evidence Mapping

**Goal**: Transform "literature list" into "evidence structure"

| Claim | Primary Study | Method | Result | Consistency |
|-------|--------------|--------|--------|------------|
| ... | ... | ... | ... | ... |

**Outcome**: Answer:
- Which claims are strongly supported?
- Which are controversial?
- Which lack evidence?

---

## SKILL 9: Citation Validation (Advanced)

**Goal**: Prevent "citation chain errors"

**Problem**:
```
Review A → Review B → Review C → Primary D
→ Primary D may NOT support claim
```

**Action**: For key claims: ALWAYS read the primary paper.

**RULE**: 引用 ≠ 复制 引用 = 验证

---

## SKILL 10: Knowledge Graph Construction

**Goal**: Upgrade literature from "list" to "network"

**Node Types**:
- Paper
- Claim
- Method
- Concept

**Edge Types**:
- supports
- contradicts
- extends

**RULE**: ❌ Literature = list ✅ Literature = network

---

## SKILL 11: Embedding-Aware Retrieval

**Goal**: Improve literature search and evidence location efficiency

**Principle**: embedding = semantic retrieval (not storage)

**Best Practice**:
```
Use:
  claim → embedding → similarity search
NOT:
  full paper → embedding
```

**Use Cases**:
- Find similar claims
- Find supporting evidence
- Find conflicting evidence

---

## SKILL 12: Writing With Citation Control

**Rule 1**: Each sentence = ONE claim + MULTIPLE primary citations

**Rule 2**: Avoid:
```
"X is associated with Y (Review1, Review2...)"
```

**Rule 3**: Cluster citation:
```
Multiple studies show... (A–C)
```

**Rule 4**: Citation must map to claim, not paragraph

---

# ==============================
# WORKFLOW: Literature Deep-Read
# ==============================

## Phase 1: Source Identification

1. Tag each paper (Primary | Review | Meta)
2. For reviews → activate SKILL 3 (trace to primary)
3. For primary → activate SKILL 6 (structured extraction)

## Phase 2: Evidence Extraction

For each paper:
1. Apply SKILL 2 (claim-level reading)
2. Extract claims → evidence → citations
3. Apply SKILL 9 (validate citations)
4. Apply SKILL 3 (trace reviews to primaries)

## Phase 3: Cross-Paper Synthesis

1. Apply SKILL 7 (group by claims/methods/questions)
2. Apply SKILL 8 (build evidence map)
3. Identify: consensus, contradictions, gaps

## Phase 4: Knowledge Graph

1. Apply SKILL 10 (build KG nodes + edges)
2. Label edges: supports / contradicts / extends
3. Export for visualization

## Phase 5: Citation Audit

Before final output:
```
[ ] Each key conclusion → at least 1 primary source
[ ] No "review-only" key claims
[ ] All important citations → verified original
[ ] No citation chain errors
[ ] Review only for background/framework
[ ] Evidence comparison exists
```

---

# ==============================
# TOOL INTEGRATION
# ==============================

## CLI Tool (tool.py)

```bash
# Full pipeline: extract + compare + KG
python scripts/tool.py all --folder ./pdfs --output ./results

# Extract only
python scripts/tool.py extract --folder ./pdfs --output ./results

# Compare analysis
python scripts/tool.py compare --output ./results

# Knowledge graph
python scripts/tool.py build-kg --output ./results

# RAG Q&A
python scripts/tool.py ask "What are the research gaps?" --output ./results
```

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

---

# ==============================
# OPENCLAW INTEGRATION
# ==============================

## Workspace Files

OpenClaw injects these for literature work:

```
~/.openclaw/workspace/
├── LITERATURE.md          # Literature review guidelines (this skill)
├── papers/                # Downloaded paper summaries
│   └── <arxiv-id>.md
├── literature/
│   ├── papers.jsonl      # Extracted structured data
│   ├── compare_report.md # Cross-paper analysis
│   └── knowledge_graph.json
└── .learnings/          # Capture literature insights
```

## Hook Events

| Event | Use |
|-------|-----|
| `agent:bootstrap` | Remind to apply literature skills |
| `command:new` | New literature review session |

---

# ==============================
# OUTPUT CHECKLIST
# ==============================

Before submission:

- [ ] Every key conclusion → ≥1 primary source
- [ ] No "only review" key claims
- [ ] All important citations → verified original text
- [ ] No citation chain errors
- [ ] Reviews used only for background/framework
- [ ] Evidence comparison exists
- [ ] Knowledge graph built for visualization

---

*Version 1.0 — Evidence Auditor, Knowledge Architect, Citation Controller*