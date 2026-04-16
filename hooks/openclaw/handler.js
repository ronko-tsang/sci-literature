/**
 * Sci-Literature Hook for OpenClaw
 *
 * Injects a reminder to apply literature review skills during agent bootstrap.
 * Fires on agent:bootstrap event before workspace files are injected.
 */

const REMINDER_CONTENT = `
## Sci-Literature Reminder

Before analyzing literature, apply the 12 literature review skills:

**Source Identification**:
- Tag each paper: Primary | Review | Meta-analysis

**Claim-Level Reading**:
- For each paragraph: extract Claim + Evidence + Citation

**Citation Tracing (CORE)**:
- Reviews are MAPS, primaries are GROUND TRUTH
- Always trace review citations to original papers

**Anti-Pollution**:
- Replace review citations with primary sources
- Target: >80% primary citations

**Structured Extraction**:
- Question / Method / Findings / Limitations

**Cross-Paper Synthesis**:
- Group by: claims, methods, research questions
- Identify: consensus, contradictions, gaps

**Evidence Mapping**:
- Build evidence table: Claim | Study | Method | Result | Consistency

**Citation Validation**:
- Verify original paper REALLY supports the claim
- 引用 ≠ 复制 引用 = 验证

**Knowledge Graph**:
- Nodes: papers, claims, methods, concepts
- Edges: supports, contradicts, extends

**Final Audit**:
- [ ] Every key conclusion → primary source
- [ ] No review-only key claims
- [ ] Citation chain verified
- [ ] Evidence comparison exists
`.trim();

const handler = async (event) => {
  if (!event || typeof event !== 'object') {
    return;
  }

  if (event.type !== 'agent' || event.action !== 'bootstrap') {
    return;
  }

  if (!event.context || typeof event.context !== 'object') {
    return;
  }

  const sessionKey = event.sessionKey || '';
  if (sessionKey.includes(':subagent:')) {
    return;
  }

  if (Array.isArray(event.context.bootstrapFiles)) {
    event.context.bootstrapFiles.push({
      path: 'SCI_LITERATURE_REMINDER.md',
      content: REMINDER_CONTENT,
      virtual: true,
    });
  }
};

module.exports = handler;
module.exports.default = handler;