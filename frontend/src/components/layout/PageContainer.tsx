import type { PropsWithChildren, ReactNode } from 'react';

type PageContainerProps = PropsWithChildren<{
  title: string;
  description: string;
  actions?: ReactNode;
  breadcrumbs?: ReactNode;
}>;

export function PageContainer({
  title,
  description,
  actions,
  breadcrumbs,
  children,
}: PageContainerProps) {
  return (
    <div className="page-container">
      <header className="page-header">
        <div className="page-header__content">
          {breadcrumbs ? <div className="page-breadcrumbs">{breadcrumbs}</div> : null}
          <div>
            <h1>{title}</h1>
            <p>{description}</p>
          </div>
        </div>
        {actions ? <div className="page-header__actions">{actions}</div> : null}
      </header>
      <main className="page-body">{children}</main>
    </div>
  );
}
