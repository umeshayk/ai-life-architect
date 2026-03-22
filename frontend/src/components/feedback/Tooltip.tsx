import { useEffect, useId, useRef, useState, type PropsWithChildren } from 'react';

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
  const containerRef = useRef<HTMLSpanElement | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    const handlePointerDown = (event: PointerEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  if (disabled) {
    return <>{children}</>;
  }

  return (
    <span
      ref={containerRef}
      className="tooltip"
      data-open={open ? 'true' : 'false'}
      onBlur={() => setOpen(false)}
      onClick={() => setOpen((current) => !current)}
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
