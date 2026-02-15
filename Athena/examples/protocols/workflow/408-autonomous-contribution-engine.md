---
id: 408
name: Autonomous Contribution Engine
category: workflow
status: active
created: 2026-02-02
last_updated: 2026-02-02
source: ethorxmomo777 (HajiMi Implementation)
---

# Protocol 408: Autonomous Contribution Engine (RCE)

> **Source**: ethorxmomo777 / HajiMi (2026)  
> **Core Concept**: Transform user insights into structured open-source contributions  
> **Tags**: #contribution #meta #workflow #community

---

## 1. The Principle (The "Why")

Most open-source users encounter friction or missing features but stay silent because:

1. **Verification Friction** — They aren't sure if the feature already exists
2. **Creation Friction** — Writing a full RFC takes too much time
3. **Process Friction** — They don't know the proper contribution format

**The Law**: An agent with full codebase access should be the first line of defense in identifying gaps and drafting solutions. The agent acts as a "Product Manager" for itself—detecting missing capabilities, verifying they aren't native, and drafting contribution artifacts.

* **Observation**: Users often ask "Does X support Y?" — this question IS the contribution signal
* **The Opportunity**: Transform every feature question into a potential contribution asset

---

## 2. The Trigger (When to use this)

Use this protocol when:

* User asks "Does Athena support [Feature X]?"
* User expresses frustration: "I wish I could do Y without..."
* User identifies a bug or limitation
* User describes a workflow that feels unnecessarily manual
* Agent detects a capability gap during task execution

**Anti-Triggers** (Do NOT activate):

* Feature already exists (verification returns positive)
* User is venting without actionable insight
* The "gap" is intentional by design

---

## 3. The Mechanism (The "How")

### Phase 1: Detection (The Spark)

Listen for contribution signals in user communication:

| Signal Type | Example | Action |
|:---|:---|:---|
| **Feature Query** | "Does Athena support X?" | Verify → Draft RFC |
| **Wishful Statement** | "I wish I could do Y" | Clarify → Draft RFC |
| **Bug Report** | "X doesn't work when..." | Verify → Draft Issue |
| **Workflow Pain** | "Every time I have to manually..." | Propose automation |

### Phase 2: Verification (The Audit)

Before drafting, confirm the gap is real:

```
1. grep_search: Search codebase for keywords related to the feature
2. view_file: Check README/docs for existing capabilities
3. find_by_name: Look for related protocols or templates
```

**Decision Gate**:
* ✅ **Confirmed Novel**: Proceed to Phase 3
* ❌ **Already Exists**: Point user to existing feature
* ⚠️ **Partial Match**: Clarify scope with user

### Phase 3: Drafting (The Production)

Switch to "Contributor Mode" and generate artifacts:

1. **Ask for Vision**: Request a one-sentence description from user
2. **Draft RFC**: Use `rfc_template.md` with structured sections:
   * Executive Summary
   * Problem Statement
   * Proposed Solution
   * Implementation Details
   * Benefits
3. **Save Draft**: Store in working directory for review

### Phase 4: Packaging (The Delivery)

Format for submission:

1. **Generate Issue Title**: `[FEATURE] <Concise Description>`
2. **Generate Issue Body**: Following `agent_contribution` template
3. **Propose Labels**: `enhancement`, `agent-assisted`, `RFC`
4. **Attach RFC**: Link the full proposal document
5. **Present to User**: Ready-to-submit package

---

## 4. Example Application

**Scenario**: User asks "Does Athena have a way to automatically summarize long documents?"

**Application**:

1. **Detection**: Recognized as Feature Query signal
2. **Verification**:
   * `grep_search "summarize" "document"` → No native protocol found
   * Checked `examples/protocols/` → No summarization protocol
   * **Decision**: Confirmed Novel
3. **Drafting**:
   * Asked user: "What's your vision for this?"
   * User: "I want to drop a PDF and get key points extracted"
   * Generated RFC with Problem/Solution/Implementation
4. **Packaging**:
   * Title: `[FEATURE] Document Summarization Protocol`
   * Body: Structured issue with verification status
   * Attached: `2026-02-02_proposal_document_summarization.md`

**Outcome**: User submitted the issue with one click. Feature entered the roadmap.

---

## 5. Technical Notes / Implementation

### File Locations

| Artifact | Location |
|:---|:---|
| This Protocol | `examples/protocols/workflow/408-autonomous-contribution-engine.md` |
| RFC Template | `examples/templates/rfc_template.md` |
| Issue Template | `.github/ISSUE_TEMPLATE/agent_contribution.md` |

### For Personal Instances

If implementing in your own Athena instance, create:

```
.agent/contribution/
├── drafts/           # Work-in-progress proposals
├── submitted/        # Historical record (prevents duplicates)
└── templates/        # Local copies of RFC/Issue templates
```

### Related Protocols

* [Protocol 130: Vibe Coding](../workflow/130-vibe-coding.md) — Iterative refinement pattern
* [Protocol 72: Proactive Extrapolation](../workflow/72-proactive-extrapolation-framework.md) — Anticipating user needs

### Meta Note

This protocol is **self-referential**: It was used to generate the very issue that requested its creation. This demonstrates the "Recursive Contribution" concept — the system helps build the system.

---

## 6. Benefits

1. **Explosive Community Growth**: Lowers contribution barrier to near-zero
2. **Recursive Self-Improvement**: The system helps build itself
3. **High Quality Signal**: Agent-generated RFCs are structured and grounded
4. **User Empowerment**: Transforms passive users into active contributors
