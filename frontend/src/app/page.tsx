import { Chat } from "@/components/Chat";

export default function Home() {
  return (
    <main className="flex flex-col h-screen bg-brand-dark">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-brand-border bg-brand-surface/50 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span className="w-1.5 h-5 rounded-sm bg-brand-green" />
            <span className="w-1.5 h-5 rounded-sm bg-brand-red" />
            <span className="w-1.5 h-5 rounded-sm bg-brand-yellow" />
          </div>
          <span className="font-semibold text-brand-text text-sm">eGov Cameroun</span>
          <span className="text-brand-text-muted text-xs hidden sm:block">— Assistant IA</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brand-green animate-pulse" />
          <span className="text-xs text-brand-text-muted">MCP connecté</span>
        </div>
      </header>

      {/* Chat — fills remaining height */}
      <div className="flex-1 overflow-hidden">
        <Chat />
      </div>
    </main>
  );
}
