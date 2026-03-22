import { PropsWithChildren } from "react";

interface StatusCardProps extends PropsWithChildren {
  title: string;
  description: string;
}

export function StatusCard({ title, description, children }: StatusCardProps) {
  return (
    <section className="surface-card">
      <header className="surface-card__header">
        <div>
          <p className="surface-card__eyebrow">{description}</p>
          <h3>{title}</h3>
        </div>
      </header>
      <div className="surface-card__content">{children}</div>
    </section>
  );
}
