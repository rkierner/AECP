import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface ChartContainerProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  loading?: boolean;
}

export function ChartContainer({ title, description, children, loading }: ChartContainerProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <CardDescription className="text-xs">{description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex-1 min-h-0">
        {loading ? (
          <div className="h-48 animate-pulse rounded bg-muted" />
        ) : (
          children
        )}
      </CardContent>
    </Card>
  );
}
