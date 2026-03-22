type EmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <section className="empty-state" aria-live="polite">
      <div className="empty-state__content">
        <h2>{title}</h2>
        <p>{description}</p>
        {actionLabel && onAction ? (
          <button className="button button--primary" type="button" onClick={onAction}>
            {actionLabel}
          </button>
        ) : null}
      </div>
    </section>
  );
}
