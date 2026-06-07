"use client";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { getToolDisplayName } from "@/lib/utils";
import type { ToolCall } from "@/types";

interface ToolExecutionProps {
  toolCalls: ToolCall[];
}

export function ToolExecution({ toolCalls }: ToolExecutionProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!toolCalls.length) return null;

  return (
    <div className="mt-2 space-y-1.5">
      {toolCalls.map((tc, i) => {
        const key = `${tc.tool_name}-${i}`;
        const isOpen = expanded === key;
        let parsedOutput: unknown = null;
        try { parsedOutput = JSON.parse(tc.output); } catch { /* raw */ }

        return (
          <div
            key={key}
            className="rounded-md border border-brand-border bg-brand-surface/60 text-xs overflow-hidden"
          >
            <button
              onClick={() => setExpanded(isOpen ? null : key)}
              className="w-full flex items-center gap-2 px-3 py-2 hover:bg-brand-border/40 transition-colors"
            >
              <span className="w-2 h-2 rounded-full bg-brand-green flex-shrink-0" />
              <span className="font-mono text-brand-green font-medium">
                {getToolDisplayName(tc.tool_name)}
              </span>
              <span className="text-brand-text-muted ml-auto">
                {isOpen ? "▲" : "▼"}
              </span>
            </button>
            {isOpen && (
              <div className="px-3 pb-3 space-y-2 border-t border-brand-border animate-fade-in">
                <div>
                  <p className="text-brand-text-muted mb-1 mt-2">Input</p>
                  <pre className={cn("text-brand-text bg-brand-dark rounded p-2 overflow-x-auto text-xs font-mono")}>
                    {JSON.stringify(tc.input, null, 2)}
                  </pre>
                </div>
                <div>
                  <p className="text-brand-text-muted mb-1">Output</p>
                  <pre className="text-brand-text bg-brand-dark rounded p-2 overflow-x-auto text-xs font-mono">
                    {parsedOutput ? JSON.stringify(parsedOutput, null, 2) : tc.output}
                  </pre>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
