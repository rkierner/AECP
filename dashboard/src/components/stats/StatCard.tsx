import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string;
  delta?: string;
  deltaPositive?: boolean;
  icon?: LucideIcon;
  loading?: boolean;
}

export function StatCard({
  title,
  value,
  delta,
  deltaPositive,
  icon: Icon,
  loading,
}: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-8 w-24 animate-pulse rounded bg-muted" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        {delta && !loading && (
          <p
            className={cn(
              "text-xs mt-1",
              deltaPositive ? "text-green-600 dark:text-green-400" : "text-red-500"
            )}
          >
            {delta}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
