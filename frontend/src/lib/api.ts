import type { ChatApiResponse, Message } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export async function sendChatMessage(
  message: string,
  history: Message[]
): Promise<ChatApiResponse> {
  const historyPayload = history.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify({ message, history: historyPayload }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erreur inconnue" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }

  return res.json();
}

export async function fetchTools(): Promise<{ name: string; description: string }[]> {
  const res = await fetch(`${API_URL}/tools`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.tools ?? [];
}
