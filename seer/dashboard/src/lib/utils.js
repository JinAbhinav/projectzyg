import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatDate(input) {
  const date = new Date(input);
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

export function formatTime(input) {
  const date = new Date(input);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function truncate(str, length) {
  if (!str) return "";
  return str.length > length ? `${str.substring(0, length)}...` : str;
}

export function getSeverityColor(severity) {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-100 text-red-800 border-red-200";
    case "HIGH":
      return "bg-orange-100 text-orange-800 border-orange-200";
    case "MEDIUM":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "LOW":
      return "bg-green-100 text-green-800 border-green-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
}

export function getSeverityTextColor(severity) {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
      return "text-red-600";
    case "HIGH":
      return "text-orange-600";
    case "MEDIUM":
      return "text-yellow-600";
    case "LOW":
      return "text-green-600";
    default:
      return "text-gray-600";
  }
} 