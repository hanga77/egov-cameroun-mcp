# AI & LLM Strategy — eGov Cameroun

## Current Choice: Claude Sonnet 4.6

**Why Sonnet for this product:**

eGov interactions require two things: accurate tool selection and structured output
formatting. Sonnet delivers both at a cost point that allows free-tier users without
burning budget. Opus is overkill for routing "calculate my VAT" to `calculate_vat()`.
Haiku is too weak for multi-turn French/English bilingual conversations with tool chains.

## Model Comparison for This Product

| Model | Quality | Cost (per 1M tokens) | Latency | Verdict |
|-------|---------|----------------------|---------|---------|
| **Claude Sonnet 4.6** | High | ~$3/$15 (in/out) | ~1-2s | **Default choice** |
| Claude Opus 4.8 | Very high | ~$15/$75 (in/out) | ~3-5s | Reserve for complex edge cases |
| Claude Haiku 4.5 | Medium | ~$0.25/$1.25 | <1s | Classification / routing layer |
| GPT-4o | High | ~$2.50/$10 | ~1-2s | Alternative to Sonnet; similar quality |
| GPT-4.1 | High | ~$2/$8 | ~1s | Strong at structured outputs; consider |
| Gemini 2.5 Pro | Very high | ~$1.25/$10 | ~2s | Long context; overkill here |
| Llama 3.3 70B | Medium | Self-host cost | ~1-3s | Privacy use case (see below) |
| Mistral Large | Medium | ~$2/$6 | ~1s | French-language advantage |

## Recommended Strategy: Model Tiering

Not all queries need the same model. Route based on complexity:

```
User message
    ↓
[Haiku: intent classifier]
    ├── "simple lookup" → Haiku directly answers
    ├── "single tool" → Sonnet with 1 tool call
    └── "multi-tool orchestration" → Sonnet full pipeline
                                        ↑
                           "complex annual filing" → Opus
```

This reduces Anthropic API cost by ~60% at scale by avoiding Sonnet for trivial queries.

## French Language Consideration

Cameroonian users write in French (and sometimes Camfranglais). 

- **Claude Sonnet/Opus**: Excellent French — trained on substantial French data.
- **Mistral**: Paris-based, strong French — a viable alternative with GDPR benefits.
- **GPT-4o**: Good French, but slightly worse than Claude on African French variants.
- **Llama/Open source**: French quality varies; fine-tuning would be needed for Cameroon-
  specific terminology (FCFA, DGI, CNPS, DSF, AIB).

## Privacy, GDPR & Compliance

**Current risk:** User salary data and matricule numbers pass through Anthropic's API.
This is sensitive data.

**Mitigations:**
1. **Data minimization**: Strip PII before sending to Claude where possible. For example,
   calculate contributions locally (already done — `calculate_cnps_contributions` runs on
   our server), then only send the summary to Claude for formatting.
2. **No training opt-out**: Use Anthropic's API (not consumer Claude.ai) — API calls are
   not used for training by default per Anthropic's usage policy.
3. **Retention**: Implement conversation TTL (e.g. 30 days) in our database. Never log
   raw salaries or matricule numbers in application logs.
4. **GDPR Article 28**: If serving EU-resident Cameroonians (diaspora), Anthropic acts
   as a data processor. A DPA (Data Processing Agreement) with Anthropic is required.

## Self-Hosting Opportunity

For a government procurement context (ministries, DGI, CNPS as clients), self-hosted
models become critical for data sovereignty:

- **Llama 3.3 70B on-premise**: Runs on 2x A100 GPUs. Sufficient for tool routing.
  Cost: ~$1,500/month (GPU rental) vs ~$5k-15k/month Anthropic at 100k users.
- **Mistral Large on Mistral's EU infrastructure**: GDPR-native, data stays in EU/Africa.

**Recommendation:** Start with Anthropic for speed-to-market. Plan migration to self-hosted
if government contracts require it or if monthly costs exceed $5k.

## Security Considerations

- API keys stored server-side only (never in frontend JS bundle)
- Rate limiting per user session (prevent abuse of Anthropic API)
- Tool input validation (Pydantic) prevents prompt injection via tool parameters
- MCP tool outputs are JSON-serialized before returning to Claude — prevents output injection
- The `require_api_key` middleware prevents unauthorized access to `/chat`

## Future AI Features

1. **Document ingestion**: Users upload accounting CSV → Claude extracts figures → auto-fill
   VAT declaration. Uses Claude's tool use + file reading.
2. **Proactive alerts**: Cron job checks upcoming deadlines → sends SMS via Orange/MTN API.
3. **Voice interface**: WhatsApp Business API integration (dominant in Cameroon) using
   Whisper for transcription + Claude for response + TTS for audio reply.
4. **Fine-tuned model**: Once data accumulates, fine-tune Llama on Cameroon-specific tax
   QA to reduce hallucination on local regulations.
