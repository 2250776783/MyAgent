interface Props {
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({ children, className = "" }: Props) {
  return (
    <div className={`mx-auto max-w-7xl p-6 ${className}`}>
      {children}
    </div>
  );
}
