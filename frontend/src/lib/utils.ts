import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}

export function formatTime(date: Date): string {
  return date.toLocaleTimeString("fr-CM", { hour: "2-digit", minute: "2-digit" });
}

export function getToolDisplayName(toolName: string): string {
  const names: Record<string, string> = {
    verify_cnps_matricule: "Vérification CNPS",
    get_statistical_data: "Données statistiques",
    calculate_vat: "Calcul TVA",
    calculate_cnps_contributions: "Cotisations CNPS",
    get_tax_deadlines: "Échéances fiscales",
  };
  return names[toolName] ?? toolName;
}
