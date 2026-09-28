export type NavItem = { label: string; to: string; desc?: string };
export type NavGroup = { label: string; items: NavItem[] };

export const navGroups: NavGroup[] = [
  {
    label: "Product",
    items: [
      { label: "About", to: "/about", desc: "Why SyncNode exists" },
      { label: "Features", to: "/features", desc: "What the system can do" },
      { label: "Workflow", to: "/workflow", desc: "How a goal becomes a result" },
      { label: "Architecture", to: "/architecture", desc: "The full system schematic" },
    ],
  },
  {
    label: "Explore",
    items: [
      { label: "Demo", to: "/demo", desc: "Watch SyncNode work" },
      { label: "Use Cases", to: "/use-cases", desc: "Real executable workflows" },
      { label: "Security", to: "/security", desc: "Sovereignty as a property" },
      { label: "Roadmap", to: "/roadmap", desc: "Built, integrating, planned" },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "FAQ", to: "/faq", desc: "Answers to common questions" },
      { label: "Download", to: "/download", desc: "Run SyncNode on Windows" },
    ],
  },
];

export const allNavItems: NavItem[] = navGroups.flatMap((g) => g.items);
