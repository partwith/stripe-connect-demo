type Status = "pending" | "in_progress" | "complete" | "restricted";

const config: Record<Status, { label: string; classes: string }> = {
  pending: { label: "Pending", classes: "bg-gray-100 text-gray-600" },
  in_progress: { label: "In Progress", classes: "bg-yellow-100 text-yellow-700" },
  complete: { label: "Complete", classes: "bg-green-100 text-green-700" },
  restricted: { label: "Restricted", classes: "bg-red-100 text-red-700" },
};

export default function StatusBadge({ status }: { status: string }) {
  const s = config[status as Status] ?? config.pending;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${s.classes}`}>
      {s.label}
    </span>
  );
}
