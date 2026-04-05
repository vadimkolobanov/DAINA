interface Props {
  current: number;
  total: number;
}

export default function StepIndicator({ current, total }: Props) {
  return (
    <div className="steps">
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`step-dot ${i === current ? "active" : ""} ${i < current ? "completed" : ""}`}
        />
      ))}
    </div>
  );
}
