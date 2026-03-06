export function Logo({ className }: { className?: string }) {
  return (
    <span className={`text-sm font-semibold tracking-tight ${className ?? ""}`}>
      <span className="text-foreground">Cold</span>
      <span className="text-primary">Approach</span>
    </span>
  );
}
