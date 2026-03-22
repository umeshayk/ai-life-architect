import { Tooltip } from 'components/feedback/Tooltip';
import type { ReactNode } from 'react';

import { ContentCard } from 'components/layout/ContentCard';

type RecommendationCardProps = {
  title: string;
  helperText?: string;
  badge?: string;
  badgeTooltip?: string;
  emptyTitle: string;
  emptyDescription: string;
  action?: ReactNode;
};

export function RecommendationCard({
  title,
  helperText,
  badge,
  badgeTooltip,
  emptyTitle,
  emptyDescription,
  action,
}: RecommendationCardProps) {
  return (
    <ContentCard
      title={title}
      helperText={helperText}
      className="recommendation-card"
      actions={
        badge ? (
          <Tooltip content={badgeTooltip ?? `${title} currently has no active items requiring review.`}>
            <span className="badge badge--neutral">{badge}</span>
          </Tooltip>
        ) : null
      }
    >
      <div className="empty-panel-state empty-panel-state--compact">
        <h3>{emptyTitle}</h3>
        <p>{emptyDescription}</p>
        {action}
      </div>
    </ContentCard>
  );
}
