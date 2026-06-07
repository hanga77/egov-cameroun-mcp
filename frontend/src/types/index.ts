export interface ToolCall {
  tool_name: string;
  input: Record<string, unknown>;
  output: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_calls?: ToolCall[];
  timestamp: Date;
}

export interface ChatApiResponse {
  message: string;
  tool_calls: ToolCall[];
}

export type SuggestionItem = {
  label: string;
  prompt: string;
};
