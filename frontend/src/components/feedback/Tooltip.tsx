import { useId, useState, type PropsWithChildren } from 'react';

type TooltipProps = PropsWithChildren<{
  content: string;
  side?: 'bottom' | 'right';
  disabled?: boolean;
}>;

export function Tooltip({
  children,
  content,
  side = 'bottom',
  disabled = false,
}: TooltipProps) {
  const tooltipId = useId();
  const [open, setOpen] = useState(false);

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <span
      className="tooltip"
      data-open={open ? 'true' : 'false'}
      onBlur={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <span aria-describedby={tooltipId} className="tooltip__trigger">
        {children}
      </span>
      <span
        id={tooltipId}
        role="tooltip"
        aria-hidden={open ? 'false' : 'true'}
        className={`tooltip__content tooltip__content--${side}`}
      >
        {content}
      </span>
    </span>
  );
}
