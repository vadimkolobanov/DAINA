export default function Skeleton({ count = 3, size = "" }: { count?: number; size?: "sm" | "lg" | "" }) {
  const cls = size ? `skeleton__block skeleton__block--${size}` : "skeleton__block";
  return (
    <div className="skeleton">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={cls} />
      ))}
    </div>
  );
}
