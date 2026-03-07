interface RuleChecklistItem {
  id: string;
  label: string;
  description: string;
  weight: string;
}

interface RuleChecklistCardProps {
  items: RuleChecklistItem[];
}

export default function RuleChecklistCard({ items }: RuleChecklistCardProps) {
  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-16">
      <h3 className="text-h3">Rule Checklist</h3>
      <div className="mt-16 flex flex-col gap-12">
        {items.map((item) => (
          <div key={item.id} className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="text-semantic-positive"
              >
                <path
                  d="M5 13l4 4L19 7"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div>
                <div className="text-body text-text-secondary">{item.label}</div>
                <div className="text-caption text-text-muted">{item.description}</div>
              </div>
            </div>
            <span className="text-caption text-text-muted">{item.weight}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
