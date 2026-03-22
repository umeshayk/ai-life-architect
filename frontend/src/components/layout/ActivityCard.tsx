import type { ReactNode } from 'react';

import { ContentCard } from 'components/layout/ContentCard';

type ActivityItem = {
  title: string;
  description: string;
  meta?: ReactNode;
};

type ActivityCardProps = {
  title: string;
  helperText?: string;
  items: ActivityItem[];
};

export function ActivityCard({ title, helperText, items }: ActivityCardProps) {
  return (
    <ContentCard title={title} helperText={helperText} className="activity-card">
      <ul className="activity-list">
        {items.map((item) => (
          <li className="activity-list__item" key={item.title}>
            <div className="activity-list__row">
              <strong>{item.title}</strong>
              {item.meta ? <span className="activity-list__meta">{item.meta}</span> : null}
            </div>
            <span>{item.description}</span>
          </li>
        ))}
      </ul>
    </ContentCard>
  );
}
