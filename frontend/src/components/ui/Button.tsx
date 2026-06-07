import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "outline";
  size?: "sm" | "md";
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-green disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" &&
          "bg-brand-green text-white hover:bg-brand-green-light active:scale-95",
        variant === "ghost" &&
          "text-brand-text-muted hover:text-brand-text hover:bg-brand-border",
        variant === "outline" &&
          "border border-brand-border text-brand-text hover:bg-brand-border",
        size === "sm" && "px-3 py-1.5 text-sm",
        size === "md" && "px-4 py-2 text-sm",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
