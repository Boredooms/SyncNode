export type UseCase = {
  id: string;
  domain: string;
  title: string;
  goal: string;
  steps: string[];
  outcome: string;
};

export const useCases: UseCase[] = [
  {
    id: "quarterly-package",
    domain: "DOCUMENT WORK",
    title: "Quarterly report package",
    goal: "Produce a complete Q4 executive package and prepare it for email.",
    steps: [
      "Create a Word summary of Q4 performance",
      "Create an Excel workbook with structured data",
      "Create a PowerPoint with title, metrics, next steps",
      "Open email compose; fill recipient, subject, body",
      "Attach all three files",
      "Stop — wait for approval before sending",
    ],
    outcome: "A ready-to-send package at the approval gate. Nothing is sent without you.",
  },
  {
    id: "engineering-analysis",
    domain: "ENGINEERING",
    title: "Inspection data to technical report",
    goal: "Turn inspection records and local documents into a structured engineering report.",
    steps: [
      "Ingest local inspection documents into knowledge",
      "Retrieve relevant specifications with sources",
      "Run the analysis against grounded context",
      "Draft the technical report as a Word document",
      "Verify the file exists with expected content",
    ],
    outcome: "A grounded, sourced report created entirely on your machine.",
  },
  {
    id: "maintenance-review",
    domain: "MAINTENANCE",
    title: "Corrective-action preparation",
    goal: "Review maintenance history and prepare corrective-action documentation.",
    steps: [
      "Search local maintenance records by equipment and date",
      "Summarize findings with source attribution",
      "Create the corrective-action document",
      "Verify content and save to the workspace",
    ],
    outcome: "Prepared documentation with a verifiable trail from source to output.",
  },
  {
    id: "project-review",
    domain: "PROJECTS",
    title: "Project document analysis",
    goal: "Understand a project package and surface open actions.",
    steps: [
      "Index the project documents locally",
      "Extract structure — deliverables, dates, owners",
      "Identify open items and dependencies",
      "Produce a summary presentation",
      "Verify slide count and content",
    ],
    outcome: "A current picture of the project, generated from the documents you already have.",
  },
  {
    id: "procurement",
    domain: "PROCUREMENT",
    title: "Vendor submission comparison",
    goal: "Compare vendor submissions against your specification.",
    steps: [
      "Retrieve specification requirements from local documents",
      "Read each vendor submission",
      "Build a technical comparison table",
      "Flag deviations from the specification",
      "Write the evaluation note",
    ],
    outcome: "A documented technical comparison — with the decision left to you.",
  },
  {
    id: "desktop-automation",
    domain: "DESKTOP WORK",
    title: "Windows application control",
    goal: "Open an application, interact with it, and capture evidence.",
    steps: [
      "Search the taskbar and launch the application",
      "Interact via Windows UI Automation",
      "Take a screenshot as evidence",
      "Verify the expected window title and state",
    ],
    outcome: "Real desktop work, with a screenshot and assertions as proof.",
  },
  {
    id: "browser-form",
    domain: "DESKTOP WORK",
    title: "Web form automation",
    goal: "Navigate to a page, fill a form, and capture what was filled.",
    steps: [
      "Open Chromium via Playwright",
      "Navigate to the URL",
      "Fill fields by accessible label or role",
      "Screenshot the completed form",
      "Stop before submitting — unless you said otherwise",
    ],
    outcome: "Form work automated up to the line; the line is yours.",
  },
  {
    id: "system-audit",
    domain: "R&D / IT",
    title: "System audit report",
    goal: "Collect system information and produce a structured report.",
    steps: [
      "Run PowerShell commands to gather state",
      "List processes, disk usage, environment",
      "Search the filesystem for matching files",
      "Write findings into a structured report",
      "Verify the report was saved correctly",
    ],
    outcome: "An environment audit you can file — generated and verified locally.",
  },
];
