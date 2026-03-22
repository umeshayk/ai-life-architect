interface QueryStateProps {
  title: string;
  body: string;
  tone?: "neutral" | "error";
}

export function QueryState({ title, body, tone = "neutral" }: QueryStateProps) {
  return (
    <div className={`query-state query-state--${tone}`}>
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}
