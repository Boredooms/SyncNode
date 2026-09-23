# PROMPT: Generate `DOCUMENT_FILE_AUTOMATION.md` Technical Specification

You are a **Principal Document Automation Architect and Local Systems Engineer** specializing in deterministic office-document generation, structured file transformation, local artifact pipelines, filesystem safety, document verification, and production-grade Python automation.

Your objective is to ingest the provided **`idea.md` architecture document** and author an **exhaustive, implementation-ready technical specification** titled:

> `DOCUMENT_FILE_AUTOMATION.md`

This specification governs the **SyncNode Document & File Automation Subsystem**: the deterministic runtime layer responsible for discovering, reading, creating, transforming, validating, versioning, hashing, and verifying local files and office artifacts used by agent workflows.

The subsystem must support the document/file capabilities defined by SyncNode, including:

- filesystem discovery
- safe file access
- document extraction
- DOCX generation and modification
- XLSX generation and modification
- PPTX generation and modification
- local PDF processing
- artifact metadata extraction
- SHA-256 hashing
- atomic writes
- temporary-file based commits
- artifact verification
- workspace-bound path enforcement
- diff generation
- integration with Context Engine
- integration with Computer Runtime for visible application verification
- integration with Planner / Agent Runtime
- integration with Tool Registry
- integration with Verification / Recovery
- persistence/audit

The design must remain **local-first and air-gapped**.

Do not turn this into a generic document-processing tutorial. This is a deterministic SyncNode runtime subsystem.

---

# 0. SOURCE-OF-TRUTH RULE

Treat `idea.md` as the primary source of truth.

Before producing the final specification:

1. Read the complete `idea.md`.
2. Extract:
   - document/file runtime responsibilities
   - allowed workspace roots
   - supported file formats
   - database mappings
   - artifact requirements
   - security constraints
   - verification rules
   - computer-runtime integration
   - phase-1 scope
3. Preserve SyncNode terminology wherever possible.
4. Do not silently contradict `idea.md`.
5. Do not introduce cloud storage or cloud document APIs.
6. Do not assume unrestricted shell execution.
7. Do not allow model-generated paths to bypass workspace controls.
8. Where implementation details are unspecified, make a concrete engineering choice and label it:
   > **Implementation Decision**
9. Clearly distinguish:
   - requested artifact
   - source file
   - sanitized input
   - generated content
   - temporary file
   - committed artifact
   - verification evidence
   - immutable digest
   - model-generated interpretation
   - verified filesystem state

The final `DOCUMENT_FILE_AUTOMATION.md` must be detailed enough for another engineer to implement the subsystem directly.

---

# 1. EXECUTIVE SUBSYSTEM BOUNDARY & FILE AUTOMATION PHILOSOPHY

Position the subsystem precisely:

```text
                Planner / Agent Runtime
                         ↓
                    Tool Registry
                         ↓
              Document/File Runtime
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Filesystem       Parsers        Generators
          │              │              │
          └──────────────┼──────────────┘
                         ↓
               Artifact Verification
                         ↓
                 Context Engine
                         ↓
                Computer Runtime
              (optional visible check)
                         ↓
                  Audit / Persistence
```

The Document/File Automation subsystem SHALL own:

- safe path resolution
- file discovery
- metadata extraction
- format detection
- local content extraction
- document creation
- document modification
- spreadsheet creation/modification
- presentation generation/modification
- PDF extraction/transformation where supported
- atomic artifact writes
- backup/version handling
- artifact hashing
- structural validation
- diff generation
- output verification
- temporary-file cleanup

It SHALL NOT own:

- task planning
- intent extraction
- model routing
- tool authorization
- human approval
- raw Windows UI manipulation
- unrestricted shell execution

---

# 1.1 Core principles

### Local-first

All document processing must run locally.

No mandatory:

- cloud OCR
- cloud embeddings
- cloud document APIs
- cloud file storage
- remote conversion service

### Workspace isolation

All file operations must remain within authorized workspace roots unless an explicit source-architecture exception exists.

### Atomicity

Never overwrite an existing artifact directly when a transactional temporary-file strategy can be used.

Preferred pattern:

```text
validate destination
→ create temp artifact
→ write
→ flush
→ fsync where supported
→ reopen
→ verify
→ atomic replace
→ hash final artifact
```

### Deterministic output

Given identical:

- input files
- structured content
- tool configuration
- document template
- locale/options

the generated artifact should be reproducible where the selected format/library permits deterministic generation.

### Verification

A successful write is not equivalent to a valid artifact.

Every generated artifact must pass structural checks before being reported successful.

---

# 1.2 Required architecture diagram

Include Mermaid and ASCII diagrams for:

```text
File/Artifact Request
       ↓
Path Canonicalization
       ↓
Workspace Boundary Check
       ↓
Format / MIME Detection
       ↓
Input Sanitization
       ↓
Parser / Generator Selection
       ↓
Temporary Artifact Creation
       ↓
Structured Write / Transform
       ↓
Flush + Atomic Commit
       ↓
SHA-256
       ↓
Structural Verification
       ↓
Artifact Record
       ↓
Context Engine / Computer Runtime
       ↓
Audit
```

---

# 2. FILESYSTEM SAFETY & WORKSPACE BOUNDARIES

Define complete path-safety contracts.

Required:

- allowed workspace roots
- canonical absolute paths
- symlink/reparse-point policy
- path-length handling
- case normalization
- Windows drive handling
- UNC path policy
- alternate data stream policy
- device-path rejection
- hidden/system-file policy
- read/write operation policy

---

## 2.1 Canonicalization

Provide complete Python code for:

```python
canonicalize_path(...)
assert_within_allowed_roots(...)
```

Handle:

```text
.
..
relative paths
absolute Windows paths
mixed separators
symlinks
reparse points
UNC paths
```

Never trust a raw model-generated path.

---

## 2.2 Read safety

Define:

- maximum file size
- maximum text extraction size
- streaming/bounded reads
- cancellation
- file sharing behavior
- retry handling for locked files

Handle Windows:

```text
ERROR_SHARING_VIOLATION
ERROR_LOCK_VIOLATION
```

using bounded retry/backoff.

---

## 2.3 Write safety

Define:

```text
destination validation
→ parent validation
→ free-space check
→ temp-file creation in same filesystem
→ write
→ flush
→ verify
→ atomic replace
```

Prefer same-directory temporary files to preserve atomic rename semantics.

---

# 3. FORMAT DETECTION & CONTENT CLASSIFICATION

Implement deterministic format detection.

Use multiple signals:

```text
magic bytes
→ MIME sniffing
→ extension
→ parser signature
```

Extension alone must not be authoritative.

Support at minimum:

```text
DOCX
XLSX
PPTX
PDF
TXT
MD
CSV
JSON
XML
source-code files
images where explicitly supported
```

Define:

- binary/text classification
- parser selection
- malformed input handling
- unsupported format behavior

Never inject arbitrary binary bytes into an LLM context.

---

# 4. DOCUMENT EXTRACTION ENGINE

Define a pluggable parser interface.

Example:

```python
class DocumentParserProtocol(Protocol):
    supported_types: frozenset[str]

    async def inspect(
        self,
        source: Path,
        options: "ExtractionOptions",
        cancellation: "CancellationToken",
    ) -> "DocumentInspection":
        ...

    async def extract(
        self,
        source: Path,
        options: "ExtractionOptions",
        cancellation: "CancellationToken",
    ) -> "DocumentExtractionResult":
        ...
```

Provide complete models.

---

# 4.1 DOCX extraction

Use `python-docx`.

Extract:

- paragraphs
- headings
- runs where useful
- tables
- hyperlinks where accessible
- core metadata
- section/page settings where supported

Avoid indiscriminate XML dumps.

Define:

- maximum paragraphs
- maximum table cells
- maximum extracted characters
- malformed document handling

---

# 4.2 XLSX extraction

Use `openpyxl`.

Extract:

- workbook metadata
- sheet names
- dimensions
- merged ranges
- cell values
- formulas where needed
- selected styles/number formats where relevant

Define:

- maximum sheets
- maximum cells
- maximum formula text
- formula sanitization
- unsupported workbook features

Do not execute spreadsheet formulas.

---

# 4.3 PPTX extraction

Use `python-pptx`.

Extract:

- slide count
- slide titles
- text boxes
- tables
- notes where safely accessible
- shape metadata
- image references/metadata

Define size and element limits.

---

# 4.4 PDF extraction

Use local PDF utilities from `idea.md`.

Specify:

- text extraction
- page limits
- metadata
- malformed PDF handling
- password/encryption behavior
- binary object handling

Do not attempt to bypass document encryption or protected access controls.

---

# 4.5 Plain text / Markdown / source code

Provide deterministic extraction for:

```text
TXT
MD
JSON
YAML
XML
CSV
Python
JavaScript/TypeScript
C/C++
Rust
SQL
```

Use:

- bounded reads
- encoding detection
- UTF-8 normalization
- structural summaries
- line-range metadata

Where appropriate produce AST or syntax-aware summaries for Context Engine compaction.

---

# 5. DOCUMENT GENERATION ENGINE

Define the generation architecture.

Canonical flow:

```text
Structured Artifact Specification
      ↓
Template / Generator
      ↓
In-memory Document Model
      ↓
Validation
      ↓
Temporary Artifact
      ↓
Atomic Commit
      ↓
Reopen
      ↓
Structural Verification
```

---

# 5.1 Artifact specification

Provide schemas for:

- `ArtifactRequest`
- `ArtifactType`
- `ArtifactMetadata`
- `ArtifactDestination`
- `ArtifactContent`
- `GenerationOptions`
- `ArtifactVerificationRules`

---

# 5.2 DOCX generator

Implement specification for:

- paragraphs
- headings
- tables
- lists
- styles
- page breaks
- margins
- metadata

Use `python-docx`.

Define deterministic ordering and style behavior.

Provide complete example for creating a Word document.

---

# 5.3 XLSX generator

Implement:

- workbook
- sheets
- cells
- formulas
- styles
- column widths
- frozen panes
- filters
- validation where supported

Use `openpyxl`.

Do not execute formulas.

Define formula injection handling where cell values originate from untrusted text.

---

# 5.4 PPTX generator

Implement:

- presentation
- slides
- titles
- text boxes
- tables
- basic shapes
- image placement
- speaker notes where safely supported

Use `python-pptx`.

Define layout validation.

---

# 5.5 PDF generation/processing boundary

Respect the capabilities actually supported by `idea.md`.

Where PDF generation is not guaranteed by the selected local stack:

- do not invent an unsupported implementation
- define a concrete local adapter only when a compatible library is included
- otherwise specify a deterministic failure:
  `PDF_GENERATION_UNAVAILABLE`

---

# 6. ARTIFACT VERSIONING, HASHING & ATOMIC COMMIT

Define artifact identity.

Use:

```text
SHA256(final_bytes)
```

as the immutable content digest.

---

## 6.1 Artifact identity

Define:

```python
class ArtifactIdentity(BaseModel):
    artifact_id: UUID
    canonical_path: str
    relative_path: str
    media_type: str
    sha256: str
    byte_size: int
    created_at: datetime
    parent_artifact_id: UUID | None
```

---

## 6.2 Atomic write algorithm

Provide complete implementation:

```text
1. validate destination
2. create temp file in destination directory
3. write bytes
4. flush
5. fsync
6. reopen/read
7. validate expected digest/structure
8. atomically replace destination
9. reopen final file
10. recalculate digest
11. emit artifact record
```

If verification fails before commit:

```text
delete temp file
→ preserve original
→ return failure
```

---

# 6.3 Existing-file overwrite policy

Differentiate:

```text
new file
existing identical file
existing different file
```

Define behavior for:

- overwrite allowed
- overwrite requires approval
- versioned output path
- conflict
- backup

Never overwrite silently when policy prohibits it.

---

# 7. DOCUMENT DIFFERENCING & CHANGE DETECTION

Define artifact-level and structural diffs.

---

## 7.1 Byte-level diff

Use SHA-256 and byte comparison where appropriate.

---

## 7.2 Semantic diff

Define structured diff models:

```text
paragraph_added
paragraph_removed
paragraph_changed
table_changed
sheet_added
sheet_removed
cell_changed
slide_added
slide_removed
shape_changed
```

For office files, compare logical document structures rather than ZIP container bytes alone when possible.

---

# 7.3 Filesystem diff integration

Integrate with Context Engine temporal tracking.

Track:

```text
path
size
mtime
sha256
artifact_id
```

Emit:

```text
ADDED
MODIFIED
DELETED
UNCHANGED
```

Only state changes should generate new artifact observations.

---

# 8. DOCUMENT VALIDATION & VERIFICATION

Define independent verification after generation.

---

## 8.1 Structural verification

For DOCX:

- file opens successfully
- expected paragraph count
- expected headings
- expected tables
- expected content markers

For XLSX:

- workbook opens
- expected sheets
- expected dimensions
- expected cell values/formulas

For PPTX:

- presentation opens
- expected slide count
- expected titles/content

For PDF:

- parser can reopen
- expected page/text properties where supported

---

## 8.2 Cryptographic verification

Verify:

```text
written bytes
→ SHA256
→ expected hash
```

A changed file must never be reported as identical.

---

## 8.3 Reopen-after-write rule

Every generated office artifact must be reopened through its local parser after writing.

Example:

```text
create.docx
→ save
→ reopen python-docx
→ inspect structure
→ PASS/FAIL
```

Do not consider `save()` success sufficient.

---

# 8.4 Optional visible application verification

For workflows requiring real desktop confirmation:

```text
artifact generated
→ Computer Runtime opens application
→ application visibly loads artifact
→ UI state observed
→ verifier checks document state
```

The document runtime generates the artifact.

The Computer Runtime performs visible OS/application interaction.

---

# 9. TEMPLATE, STYLE & METADATA MANAGEMENT

Define deterministic handling of:

- document templates
- style inheritance
- fonts
- headers/footers
- metadata
- author field
- creation time
- modification time
- application metadata

Avoid nondeterministic metadata where reproducibility is required.

Provide an explicit reproducibility mode.

---

# 10. MALICIOUS CONTENT & FILE SECURITY

Threats:

- path traversal
- symlink escape
- malformed office files
- ZIP bomb-like package expansion
- oversized XML
- malicious formulas
- external-link metadata
- embedded scripts/macros
- deceptive filenames
- Unicode path confusables
- parser crashes

Required protections:

1. bounded file size
2. bounded decompression/package expansion
3. no macro execution
4. no formula execution
5. no external URL fetching during parsing
6. no automatic remote resource resolution
7. parser timeouts
8. parser worker isolation where appropriate
9. sanitized metadata
10. fail-closed unsupported input

Never execute embedded VBA/macros.

Never fetch external links automatically.

---

# 11. OFFICE PACKAGE / ZIP SAFETY

Because DOCX/XLSX/PPTX are ZIP packages, define:

- archive entry count limit
- cumulative uncompressed-size limit
- individual entry-size limit
- compression-ratio anomaly detection
- path normalization inside archive
- rejection of `../` archive entries
- temporary extraction directory jail
- cleanup guarantees

Provide complete archive validation code.

---

# 12. CONCURRENCY & FILE ACCESS CONTENTION

Define behavior for:

```text
same artifact modified by multiple agents
same file opened by Word
same workbook locked by Excel
simultaneous parser access
```

Use:

- per-path async locks
- bounded retries
- file metadata revalidation
- optimistic concurrency
- atomic replace

For write conflicts:

```text
original hash captured
→ generated output
→ before commit recheck original
→ if changed externally:
    ARTIFACT_CONFLICT
```

Never overwrite an artifact changed by another process without an explicit conflict policy.

---

# 13. TEMPORARY FILE & RESOURCE MANAGEMENT

Define:

- temp directory policy
- per-run temp namespaces
- cleanup after success/failure
- crash cleanup
- file-handle closure
- parser object lifecycle

Example:

```text
%LOCALAPPDATA%/SyncNode/tmp/{run_id}/{step_id}/
```

or the local equivalent selected by `idea.md`.

No sensitive temporary artifact should remain indefinitely.

---

# 14. DATABASE INTEROPERABILITY & ARTIFACT RECORDS

Align with the database architecture in `idea.md`.

Where the source schema specifies artifact/file persistence, map:

```text
artifact ID
run ID
run_step_id
canonical path
relative path
media type
size
sha256
created_at
updated_at
verification status
```

If `idea.md` does not define a dedicated artifact table, introduce any proposed table/fields under:

> **Implementation Decision — Document Artifact Persistence Extensions**

Do not silently replace existing schema.

---

# 15. TOOL REGISTRY INTEGRATION

Define registered tools such as:

```text
files.find
files.inspect
files.read
files.create
files.write
files.copy
files.move
files.delete
document.extract
document.create_docx
document.modify_docx
document.create_xlsx
document.modify_xlsx
document.create_pptx
document.modify_pptx
document.inspect_pdf
artifact.verify
artifact.diff
```

Only include tools that match `idea.md`.

For each tool define:

- key
- version
- capabilities
- risk class
- approval requirement
- input schema
- output schema
- preconditions
- postconditions
- timeout
- retry policy
- implementation binding

---

# 16. CONTEXT ENGINE INTEGRATION

After artifact creation/update:

```text
Document Runtime
      ↓
ArtifactIdentity
      ↓
Filesystem hash / metadata
      ↓
Context Engine delta
      ↓
Workspace artifact context
```

The Context Engine should consume:

- relative path
- modification time
- digest
- structural summary
- selected excerpts

Do not inject entire binary document packages into context.

---

# 17. COMPUTER RUNTIME INTEGRATION

For workflows such as:

> “Create a Word document and verify it in Word.”

Define:

```text
Document Runtime
→ generate DOCX
→ verify file structurally
→ Computer Runtime opens Word
→ open artifact
→ observe UIA state
→ verify document is visible
→ close Word
```

The Computer Runtime controls Word.

The Document Runtime remains responsible for the artifact itself.

---

# 18. COMPLETE DATA CONTRACTS & INTERFACE DEFINITIONS

Provide complete Pydantic v2 models and Python Protocols.

At minimum define:

- `ArtifactType`
- `ArtifactRequest`
- `ArtifactDestination`
- `ArtifactIdentity`
- `ArtifactMetadata`
- `GenerationOptions`
- `ExtractionOptions`
- `DocumentInspection`
- `DocumentExtractionResult`
- `DocumentWriteResult`
- `ArtifactVerificationResult`
- `ArtifactDiff`
- `ArtifactConflict`
- `FilesystemFileRecord`
- `ArchiveValidationResult`
- `DocumentRuntimeError`

Required interface:

```python
class DocumentFileAutomationProtocol(Protocol):
    async def inspect(
        self,
        request: DocumentInspectRequest,
        cancellation: CancellationToken,
    ) -> DocumentInspection:
        ...

    async def extract(
        self,
        request: DocumentExtractRequest,
        cancellation: CancellationToken,
    ) -> DocumentExtractionResult:
        ...

    async def create(
        self,
        request: ArtifactRequest,
        cancellation: CancellationToken,
    ) -> DocumentWriteResult:
        ...

    async def modify(
        self,
        request: ArtifactModifyRequest,
        cancellation: CancellationToken,
    ) -> DocumentWriteResult:
        ...

    async def verify(
        self,
        artifact: ArtifactIdentity,
        rules: ArtifactVerificationRules,
        cancellation: CancellationToken,
    ) -> ArtifactVerificationResult:
        ...

    async def diff(
        self,
        before: ArtifactIdentity,
        after: ArtifactIdentity,
        cancellation: CancellationToken,
    ) -> ArtifactDiff:
        ...
```

Improve signatures where necessary, but preserve deterministic responsibilities.

---

# 19. REQUIRED SUPPORTING SCHEMAS

Also define complete models for:

- `WorkspaceRootPolicy`
- `PathPolicy`
- `FileAccessPolicy`
- `DocumentType`
- `MimeClassification`
- `ParserCapabilities`
- `DocumentNode`
- `DocumentSection`
- `TableRecord`
- `SpreadsheetRecord`
- `PresentationRecord`
- `PdfRecord`
- `FileHash`
- `AtomicWriteRequest`
- `AtomicCommitResult`
- `ArtifactVerificationRule`
- `VerificationEvidence`
- `ArtifactConflict`
- `FileLock`
- `TemporaryArtifact`
- `DocumentAuditEvent`
- `DocumentRuntimeMetrics`

No undefined types may appear in code examples.

---

# 20. COMPLETE IMPLEMENTATION EXAMPLES

The generated `DOCUMENT_FILE_AUTOMATION.md` MUST contain real Python 3.12+ implementation code for at least:

1. path canonicalization
2. workspace-root enforcement
3. symlink/reparse-point guard
4. bounded file read
5. sharing-violation retry
6. magic-byte/MIME detection
7. ZIP-package safety validation
8. DOCX inspection
9. DOCX extraction
10. DOCX generation
11. XLSX inspection
12. XLSX generation
13. PPTX inspection
14. PPTX generation
15. local PDF inspection/extraction
16. text/Markdown extraction
17. atomic temporary-file write
18. fsync/flush handling
19. atomic replace
20. SHA-256 hashing
21. artifact identity construction
22. reopen-after-write verification
23. semantic document diff
24. filesystem diff
25. external-change conflict detection
26. temporary artifact cleanup
27. complete `DocumentFileAutomationProtocol` orchestration
28. structured audit event creation
29. persistence contract
30. `ARTIFACT_CONFLICT` propagation

Code MUST be:

- Python 3.12+
- Pydantic v2-compatible
- fully type annotated
- async-compatible where appropriate
- Windows-compatible where required
- syntactically complete
- executable with documented dependencies
- free of `TODO`
- free of `TBD`
- free of `pass`
- free of undefined types
- free of placeholder implementations
- free of unexplained magic constants

Do not execute macros, formulas, embedded scripts, or external document links.

---

# 21. FAILURE MODES & ERROR TAXONOMY

Define a complete catalog:

```text
PATH_OUTSIDE_WORKSPACE
FILE_NOT_FOUND
FILE_ACCESS_DENIED
FILE_LOCKED
FILE_TOO_LARGE
BINARY_INPUT_UNSUPPORTED
MIME_MISMATCH
MALFORMED_DOCUMENT
ZIP_PACKAGE_UNSAFE
PARSER_TIMEOUT
PARSER_FAILED
FORMAT_UNSUPPORTED
ARTIFACT_GENERATION_FAILED
ARTIFACT_WRITE_FAILED
ATOMIC_COMMIT_FAILED
ARTIFACT_VERIFICATION_FAILED
ARTIFACT_HASH_MISMATCH
ARTIFACT_CONFLICT
OVERWRITE_NOT_ALLOWED
OUTPUT_DESTINATION_INVALID
TEMP_ARTIFACT_CLEANUP_FAILED
DOCUMENT_RUNTIME_TIMEOUT
EXTERNAL_RESOURCE_BLOCKED
MACRO_EXECUTION_BLOCKED
FORMULA_EXECUTION_BLOCKED
```

Every error must include:

- stable code
- severity
- retryability
- run ID
- step ID
- artifact ID where applicable
- trace ID
- sanitized reason
- recovery recommendation

Never include secrets or full sensitive document bodies.

---

# 22. RESILIENCE & RECOVERY

Define bounded recovery behavior.

### File locked

```text
bounded backoff
→ recheck
→ final failure
```

### Parser failure

```text
retry only when failure is classified transient
→ otherwise fail
```

### Artifact verification failure

```text
do not commit bad artifact
→ delete temp
→ preserve prior artifact
→ return failure
```

### External modification

```text
detect source hash changed
→ ARTIFACT_CONFLICT
→ preserve both versions where configured
→ notify Planner/Recovery
```

### Crash

Startup recovery should:

```text
scan temp namespaces
→ identify orphan artifacts
→ validate timestamps/ownership
→ clean safe leftovers
→ preserve evidence for active runs
```

---

# 23. SECURITY MODEL

Explicitly address:

- path traversal
- symlink escape
- junction/reparse-point escape
- malicious ZIP packages
- ZIP bombs
- malformed XML
- macro payloads
- formula injection
- external link loading
- oversized text
- parser denial of service
- race conditions
- file replacement attacks
- Unicode confusables
- cross-workspace leakage
- temporary-file leakage
- stale artifact references

Required guarantees:

1. All paths are canonicalized.
2. All paths are checked against allowed roots.
3. Symlink/reparse escapes fail closed.
4. Office packages are bounded before extraction.
5. Macros are never executed.
6. Spreadsheet formulas are never executed by the runtime.
7. External resources are not automatically fetched.
8. All generated artifacts are structurally verified.
9. Hashes identify committed bytes.
10. Write conflicts are detected.
11. Temporary artifacts are cleaned.
12. Sensitive content is excluded from logs by default.

---

# 24. OBSERVABILITY & TELEMETRY

Define structured events:

```text
document.inspect_started
document.inspect_completed
document.extract_started
document.extract_completed
artifact.generation_started
artifact.generation_completed
artifact.write_started
artifact.committed
artifact.verification_passed
artifact.verification_failed
artifact.hash_generated
artifact.conflict_detected
artifact.cleanup_completed
document.parser_failed
document.external_resource_blocked
```

Metrics:

```text
file_read_latency_ms
parser_latency_ms
generation_latency_ms
atomic_commit_latency_ms
verification_latency_ms
artifact_size_bytes
files_processed
parser_failures
verification_failures
artifact_conflicts
temp_cleanup_failures
```

Never log entire sensitive document bodies or binary payloads.

---

# 25. PERFORMANCE & CONCURRENCY

Define measurable targets for:

- file metadata access
- hashing
- parser initialization
- document extraction
- artifact generation
- atomic commit
- verification
- diffing

Define limits:

```text
max_file_bytes
max_document_nodes
max_docx_paragraphs
max_xlsx_cells
max_pptx_shapes
max_pdf_pages
max_zip_entries
max_zip_uncompressed_bytes
max_concurrent_parsers
max_concurrent_generators
```

Use bounded concurrency.

---

# 25.1 Per-artifact locking

Define:

```text
artifact:{canonical_path}
```

as a scoped lock for mutating operations.

A read may be concurrent only when file-consistency policy permits.

Writes to the same artifact must serialize.

---

# 26. REFERENCE PACKAGE STRUCTURE

Provide:

```text
syncnode/
└── document_file_automation/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── protocols.py
    ├── runtime.py
    ├── paths.py
    ├── mime.py
    ├── hashing.py
    ├── locks.py
    ├── atomic_write.py
    ├── conflicts.py
    ├── artifacts.py
    ├── verification.py
    ├── diff.py
    ├── temp_files.py
    ├── parsers/
    │   ├── __init__.py
    │   ├── docx.py
    │   ├── xlsx.py
    │   ├── pptx.py
    │   ├── pdf.py
    │   ├── text.py
    │   └── source_code.py
    ├── generators/
    │   ├── __init__.py
    │   ├── docx.py
    │   ├── xlsx.py
    │   ├── pptx.py
    │   └── pdf.py
    ├── persistence.py
    ├── telemetry.py
    ├── errors.py
    └── tests/
        ├── test_paths.py
        ├── test_mime.py
        ├── test_hashing.py
        ├── test_zip_safety.py
        ├── test_docx.py
        ├── test_xlsx.py
        ├── test_pptx.py
        ├── test_pdf.py
        ├── test_atomic_write.py
        ├── test_conflicts.py
        ├── test_verification.py
        ├── test_diff.py
        ├── test_security.py
        └── test_determinism.py
```

Adapt to `idea.md`.

---

# 27. TESTING & ACCEPTANCE CRITERIA

Define:

- unit tests
- parser tests
- generator tests
- filesystem tests
- Windows lock/contention tests
- security tests
- atomicity tests
- conflict tests
- deterministic replay tests
- integration tests
- crash recovery tests
- performance tests

Mandatory tests:

### Path security

A path outside allowed roots always fails.

### Symlink security

A symlink/reparse point escaping the workspace is rejected.

### ZIP safety

Oversized/deceptive Office packages are rejected before unsafe expansion.

### Macro safety

Embedded macros are never executed.

### Formula safety

Spreadsheet formulas are stored/validated but never executed by the runtime.

### External-resource safety

Parser does not fetch arbitrary external URLs.

### Atomicity

A failed generation leaves the existing committed artifact unchanged.

### Hash correctness

Final digest matches the committed bytes.

### Verification

A corrupted generated artifact does not report success.

### Conflict detection

An artifact externally modified after source-hash capture produces `ARTIFACT_CONFLICT`.

### Determinism

Identical inputs and configuration produce identical logical document output wherever deterministic generation is supported.

---

# 28. REFERENCE END-TO-END WORKFLOW

Use:

> “Write a story about a tree, create a Word document, save it in the workspace, verify it, and prepare it for email.”

Show:

```text
Intent
→ Planner
→ Document Agent
→ Document Runtime
→ workspace path validation
→ content generation
→ DOCX generation
→ atomic write
→ SHA-256
→ reopen/verify
→ artifact identity
→ Context Engine filesystem delta
→ Computer Runtime opens Word
→ visible verification
→ artifact remains immutable
→ Browser/Email workflow receives verified artifact reference
```

Clearly distinguish:

- generated content
- committed bytes
- artifact hash
- UI verification
- model interpretation
- persisted evidence

---

# 29. INTEGRATION WITH AGENT RUNTIME / TOOL REGISTRY / VERIFIER

Define the responsibility boundaries.

### Agent Runtime

Requests a typed artifact operation.

### Tool Registry

Validates and authorizes the registered tool.

### Document Runtime

Performs deterministic file/document processing.

### Context Engine

Consumes filesystem/artifact deltas.

### Computer Runtime

Performs visible application interaction when required.

### Verifier

Evaluates postconditions based on evidence.

No component should silently perform another component's responsibilities.

---

# 30. FINAL ENGINE CONTRACT

The Document & File Automation subsystem SHALL:

- operate locally
- enforce workspace boundaries
- canonicalize all paths
- reject path traversal
- handle symlink/reparse-point safety
- detect file format using bounded deterministic methods
- support local office-document parsing/generation as defined by `idea.md`
- create artifacts through temporary files
- atomically commit successful artifacts
- hash committed bytes with SHA-256
- reopen artifacts for verification
- detect external modification conflicts
- produce structured artifact identities
- generate filesystem/document diffs
- integrate with Context Engine
- integrate with Computer Runtime for visible verification
- remain independently testable
- emit auditable telemetry

The subsystem SHALL NOT:

- upload files to cloud services
- fetch arbitrary external resources
- execute macros
- execute spreadsheet formulas
- bypass document encryption
- execute arbitrary shell commands
- write outside workspace policy
- silently overwrite conflicting artifacts
- claim artifact validity without verification
- expose entire sensitive files in logs
- treat model-generated paths as trusted

---

# 31. OUTPUT QUALITY BAR

The generated `DOCUMENT_FILE_AUTOMATION.md` must be:

- exhaustive
- production-grade
- implementation-ready
- deterministic
- secure
- workspace-isolated
- concurrency-safe
- artifact-integrity-focused
- compatible with SyncNode

Do not produce:

- generic document-automation tutorials
- generic Python office examples without runtime architecture
- marketing language
- vague recommendations
- pseudo-code presented as implementation
- undefined classes
- placeholder methods
- `TODO`
- `TBD`
- `pass`
- unexplained constants
- cloud dependencies
- macro execution
- formula execution
- arbitrary external URL fetching

Use throughout:

- Pydantic v2
- Python Protocols
- filesystem security models
- Mermaid diagrams
- state machines
- atomic-write algorithms
- SHA-256 hashing
- Office parser/generator contracts
- ZIP/package security
- artifact verification
- semantic diff models
- SQL persistence examples
- failure taxonomies
- audit schemas
- acceptance tests
- complete implementation code

---

# INPUT

Use the attached/provided **`idea.md`** as the system foundation.

Generate only the requested engineering specification:

```text
DOCUMENT_FILE_AUTOMATION.md
```
