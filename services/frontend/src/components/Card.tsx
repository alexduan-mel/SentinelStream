import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  variant?: "default" | "compact" | "highlight";
}

const variantStyles: Record<NonNullable<CardProps["variant"]>, string> = {
  default: "p-24",
  compact: "p-16",
  highlight: "p-24 border border-semantic-info"
};

export default function Card({ title, subtitle, action, children, className = "", variant = "default" }: CardProps) {
  return (
    <section
      className={[
        "rounded-md border border-border-default bg-bg-surface",
        variantStyles[variant],
        className
      ].join(" ")}
    >
      {(title || action) && (
        <div className="mb-16 flex items-start justify-between">
          <div>
            {title && <h3 className="text-h3">{title}</h3>}
            {subtitle && <p className="text-caption text-text-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
