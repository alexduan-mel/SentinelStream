import { useState } from "react";

interface StructuredOutputAccordionProps {
  data: object;
}

export default function StructuredOutputAccordion({ data }: StructuredOutputAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const payload = JSON.stringify(data, null, 2);

  return (
    <section className="rounded-md border border-border-default bg-bg-surface p-16">
      <button
        type="button"
        className="flex w-full items-center justify-between text-left text-h3"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        LLM Structured Output
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={["text-text-muted transition-transform", isOpen ? "rotate-180" : ""].join(" ")}
        >
          <path
            d="M6 9l6 6 6-6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      {isOpen && (
        <pre className="mt-16 rounded border border-border-subtle bg-bg-elevated p-16 text-mono font-mono text-text-secondary">
          {payload}
        </pre>
      )}
    </section>
  );
}
