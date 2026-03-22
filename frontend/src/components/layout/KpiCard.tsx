import { Tooltip } from 'components/feedback/Tooltip';

type KpiCardProps = {
  label: string;
  value: string;
  subtext: string;
  badge?: string;
  tooltip?: string;
  badgeTooltip?: string;
};

export function KpiCard({ label, value, subtext, badge, tooltip, badgeTooltip }: KpiCardProps) {
  return (
    <article className="panel kpi-card">
      <div className="kpi-card__header">
        <Tooltip content={tooltip ?? subtext} disabled={!tooltip}>
          <p className="panel__label">{label}</p>
        </Tooltip>
        {badge ? (
          <Tooltip content={badgeTooltip ?? `${label} is ready for new data and actions.`} disabled={!badgeTooltip && !tooltip}>
            <span className="badge badge--neutral">{badge}</span>
          </Tooltip>
        ) : null}
      </div>
      <Tooltip content={tooltip ?? subtext}>
        <strong className="panel__metric">{value}</strong>
      </Tooltip>
      <p className="panel__description">{subtext}</p>
    </article>
  );
}
