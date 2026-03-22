type KpiCardProps = {
  label: string;
  value: string;
  subtext: string;
  badge?: string;
};

export function KpiCard({ label, value, subtext, badge }: KpiCardProps) {
  return (
    <article className="panel kpi-card">
      <div className="kpi-card__header">
        <p className="panel__label">{label}</p>
        {badge ? <span className="badge badge--neutral">{badge}</span> : null}
      </div>
      <strong className="panel__metric">{value}</strong>
      <p className="panel__description">{subtext}</p>
    </article>
  );
}
