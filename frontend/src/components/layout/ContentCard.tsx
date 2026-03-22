import type { PropsWithChildren, ReactNode } from 'react';

type ContentCardProps = PropsWithChildren<{
  title: string;
  helperText?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function ContentCard({
  title,
  helperText,
  actions,
  className,
  children,
}: ContentCardProps) {
  return (
    <section className={`panel content-card${className ? ` ${className}` : ''}`}>
      <div className="panel__header">
        <div>
          <h2>{title}</h2>
          {helperText ? <p className="panel__helper-text">{helperText}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}
