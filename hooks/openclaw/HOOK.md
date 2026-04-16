---
name: sci-literature
description: "Injects literature review reminder during agent bootstrap"
metadata: {"openclaw":{"emoji":"📚","events":["agent:bootstrap"]}}
---

# Sci-Literature Hook

Injects a reminder to apply literature review skills during agent bootstrap.

## What It Does

- Fires on `agent:bootstrap` (before workspace files are injected)
- Adds a reminder block to apply the 12 literature review skills
- Prompts the agent to trace citations, validate evidence, build KG

## Configuration

No configuration needed. Enable with:

```bash
openclaw hooks enable sci-literature
```

## The 12 Skills Reminder

When reviewing literature, apply these skills:

1. Source Type Identification → Tag papers as Primary/Review/Meta
2. Claim-Level Reading → Extract claim/evidence/citation
3. Review → Primary Trace → Always trace review citations to originals
4. Citation Chaining → Backward + Forward search
5. Anti-Citation Pollution → Replace reviews with primaries
6. Structured Extraction → Extract question/method/findings/limitations
7. Cross-Paper Synthesis → Group by claims/methods/gaps
8. Evidence Mapping → Build evidence structure table
9. Citation Validation → Verify original supports claim
10. Knowledge Graph → Build network of claims/papers/methods
11. Embedding-Aware Retrieval → Use claim-based similarity search
12. Citation-Controlled Writing → One claim + multiple primary citations