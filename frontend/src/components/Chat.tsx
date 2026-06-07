"use client";
import { useState, useRef, useEffect, FormEvent } from "react";
import { MessageBubble } from "./MessageBubble";
import { Button } from "./ui/Button";
import { sendChatMessage } from "@/lib/api";
import { generateId } from "@/lib/utils";
import type { Message, SuggestionItem } from "@/types";

const SUGGESTIONS: SuggestionItem[] = [
  { label: "Échéances mars 2026", prompt: "Quelles sont les échéances fiscales pour mars 2026 ?" },
  { label: "TVA 5M FCFA", prompt: "Calcule ma déclaration TVA de mars 2026 pour un CA HT de 5 000 000 FCFA" },
  { label: "Cotisations CNPS", prompt: "Calcule les cotisations CNPS pour 2 employés : Alice à 350 000 FCFA et Bob à 800 000 FCFA" },
  { label: "PIB Cameroun", prompt: "Donne-moi l'évolution du PIB du Cameroun entre 2018 et 2023" },
  { label: "Vérifier matricule", prompt: "Vérifie le matricule CNPS C123456789" },
];

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setError(null);

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage(text.trim(), [...messages, userMsg]);
      const assistantMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: res.message,
        tool_calls: res.tool_calls,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      // Remove the user message if call failed
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-8 animate-fade-in">
            {/* Logo / Hero */}
            <div className="text-center space-y-2">
              <div className="flex items-center justify-center gap-2 mb-4">
                <span className="w-3 h-8 rounded-sm bg-brand-green" />
                <span className="w-3 h-8 rounded-sm bg-brand-red" />
                <span className="w-3 h-8 rounded-sm bg-brand-yellow" />
              </div>
              <h1 className="text-2xl font-bold text-brand-text">eGov Cameroun</h1>
              <p className="text-brand-text-muted text-sm max-w-sm">
                Votre assistant IA pour les services gouvernementaux — DGI, CNPS, statistiques économiques.
              </p>
            </div>
            {/* Suggestions */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  onClick={() => sendMessage(s.prompt)}
                  className="text-left px-4 py-3 rounded-xl border border-brand-border bg-brand-surface hover:border-brand-green hover:bg-brand-surface/80 transition-all text-sm text-brand-text group"
                >
                  <span className="font-medium group-hover:text-brand-green transition-colors">
                    {s.label}
                  </span>
                  <p className="text-brand-text-muted text-xs mt-0.5 line-clamp-1">{s.prompt}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="flex gap-3 animate-slide-up">
            <div className="w-8 h-8 rounded-full bg-brand-surface border border-brand-border flex items-center justify-center text-xs font-bold text-brand-yellow flex-shrink-0">
              AI
            </div>
            <div className="bg-brand-surface border border-brand-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-brand-text-muted animate-pulse"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-brand-red/40 bg-brand-red/10 px-4 py-3 text-sm text-brand-red animate-fade-in">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-brand-border px-4 py-4 bg-brand-dark">
        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="text-xs text-brand-text-muted hover:text-brand-text mb-3 transition-colors"
          >
            Nouvelle conversation
          </button>
        )}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question en français ou en anglais…"
            className="flex-1 rounded-xl border border-brand-border bg-brand-surface px-4 py-3 text-sm text-brand-text placeholder:text-brand-text-muted focus:outline-none focus:border-brand-green transition-colors"
            disabled={loading}
            autoFocus
          />
          <Button type="submit" disabled={loading || !input.trim()}>
            {loading ? "..." : "Envoyer"}
          </Button>
        </form>
      </div>
    </div>
  );
}
