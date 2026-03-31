import { formatDistanceToNowStrict } from "date-fns";

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCount(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return String(value);
}

export function formatTimeSince(isoString: string | null): string {
  if (!isoString) return "never";
  try {
    return formatDistanceToNowStrict(new Date(isoString), { addSuffix: true });
  } catch {
    return "unknown";
  }
}

export function formatHour(isoString: string): string {
  try {
    return new Date(isoString).toLocaleTimeString("en-US", {
      hour: "numeric",
      hour12: false,
    });
  } catch {
    return "";
  }
}
