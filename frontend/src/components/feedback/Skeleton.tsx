type SkeletonProps = {
  height?: 'sm' | 'md' | 'lg';
};

export function Skeleton({ height = 'md' }: SkeletonProps) {
  return <div className={`skeleton skeleton--${height}`} aria-hidden="true" />;
}
