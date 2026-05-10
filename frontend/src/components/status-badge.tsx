type Status = "pending" | "in_progress" | "complete" | "restricted";

const config: Record<Status, { label: string; classes: string }> = {
  pending: { label: "Pending", classes: "bg-mauve text-brand-mid" },
  in_progress: { label: "In Progress", classes: "bg-accent text-brand" },
  complete: { label: "Complete", classes: "bg-green-100 text-green-800" },
  restricted: { label: "Restricted", classes: "bg-cream-blush text-brand" },
};

export default function StatusBadge({ status }: { status: string }) {
  const s = config[status as Status] ?? config.pending;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${s.classes}`}>
      {s.label}
    </span>
  );
}
