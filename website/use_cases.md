# SyncNode Use Cases

Real workflows SyncNode can execute today, running entirely offline on your Windows machine.

---

## Quarterly report package

**Goal:** Produce a complete Q4 executive package and prepare it for email.

SyncNode will:
1. Create a Word document with a professional written summary of Q4 performance
2. Create an Excel workbook with a structured data table (headers, rows, formulas)
3. Create a PowerPoint presentation with a title slide, metrics slide, and next-steps slide
4. Open the email compose page in your browser
5. Fill in the recipient, subject, and body
6. Attach all three files
7. **Stop and wait for your approval before sending**

The entire sequence runs locally. Each step is verified. If Word doesn't open, the recovery agent retries. If the Excel file is empty after creation, the verifier catches it and the run fails with a clear error — not a false success.

---

## Document drafting and filing

**Goal:** Draft a letter, save it, and open it in Word for final review.

SyncNode will:
1. Write the letter content based on your description
2. Create the .docx file in your workspace
3. Open it in Microsoft Word using the taskbar search
4. Take a screenshot as evidence that Word opened with the file
5. Report completion with the file path, word count, and verification screenshot

You review in Word. No cloud ever saw the document.

---

## Data workbook creation

**Goal:** Create a structured Excel workbook with real data from your description.

SyncNode will:
1. Create the workbook with named sheets
2. Write header rows and data rows
3. Verify the file exists and has non-zero size
4. Optionally open Excel and take a screenshot as visual evidence

Useful for quickly scaffolding reports, templates, and data tables that you then fill out further.

---

## Presentation from notes

**Goal:** Turn bullet-point notes into a formatted PowerPoint presentation.

SyncNode will:
1. Create a title slide with your presentation name
2. Add content slides for each section in your notes
3. Format text with appropriate slide layouts
4. Save the file to your workspace
5. Verify the slide count and content

You end up with a real .pptx file you can open in PowerPoint and polish.

---

## Desktop application control

**Goal:** Open an application, interact with it, and capture evidence.

SyncNode will:
1. Search the Windows taskbar for the application
2. Launch it and wait for it to be ready
3. Interact with it via Windows UI Automation (type, click, navigate menus)
4. Take a screenshot showing the result
5. Verify the expected window title and UI state

Works with Office applications, Notepad, File Explorer, and any UIA-accessible Windows app.

---

## Web form automation

**Goal:** Navigate to a web page, fill a form, and capture what was filled.

SyncNode will:
1. Open Chromium via Playwright
2. Navigate to the URL
3. Fill form fields by accessible label or role
4. Take a screenshot of the filled form
5. **Stop before submitting** — unless you've explicitly included submission in the goal

The approval gate catches anything classified as an external side effect before it executes.

---

## Local knowledge search

**Goal:** Find relevant information in your local document collection.

SyncNode's RAG layer will:
1. Embed your query using a local model (all-MiniLM-L6-v2)
2. Search the ChromaDB vector index built from your ingested documents
3. Return the most relevant chunks with source attribution
4. Use the retrieved context to answer your question

All indexing and retrieval is local. No document content is sent anywhere.

---

## System audit and reporting

**Goal:** Collect system information and produce a structured report.

SyncNode will:
1. Run PowerShell commands to gather system state
2. List running processes, disk usage, environment
3. Search the filesystem for files matching criteria
4. Write the findings into a structured text or Word report
5. Verify the report was saved correctly

Useful for IT operations, compliance documentation, and environment audits.

---

## Email draft with attachments

**Goal:** Compose an email with multiple attachments and wait for approval.

SyncNode will:
1. Open your browser-based email client (Gmail, Outlook Web, etc.)
2. Navigate to the compose view
3. Fill in recipient, CC, subject, and body
4. Attach files from your local workspace
5. **Pause at the approval gate — it will not click Send**
6. Present you with a summary of the draft for review

You decide whether to send. SyncNode records your decision either way.

---

## Combining it all

The real power of SyncNode is combining these capabilities in a single goal:

> "Search Windows for Microsoft Word and open it. Create a Word document called Q4_Report.docx with a 2-paragraph professional summary about SyncNode local AI automation capabilities — save it. Create an Excel workbook called Q4_Data.xlsx with a Metrics sheet containing headers (Category, Value, Notes) and 4 rows — save it. Create a PowerPoint called Q4_Slides.pptx with a title slide 'Q4 Executive Summary', a metrics slide, and a next-steps slide — save it. Open email compose for demo@company.com with subject 'Q4 Package' and body 'Please find the Q4 package attached. Best regards.' Attach all three files. Do NOT send — wait for my approval."

SyncNode decomposes this into ~12 steps, runs them in the optimal order (some in parallel), verifies each one, and stops at the approval gate with everything ready for your review.

That sequence — which would take a human 20-30 minutes — takes SyncNode 8-12 minutes on a mid-range RTX GPU.
