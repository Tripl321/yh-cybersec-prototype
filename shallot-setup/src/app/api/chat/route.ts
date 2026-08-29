import { NextRequest } from "next/server";

const OLLAMA_HOST = process.env.OLLAMA_HOST || "http://localhost:11434";
const CHAT_MODEL = process.env.CHAT_MODEL || "ministral-3:8b-instruct-2512-q4_K_M";
// Python SHALLOT Harness (real tools + HITL). If unset or down, fall back to Ollama direct.
const HARNESS_URL = process.env.HARNESS_URL || "";
const AGENTOS_URL = process.env.AGENTOS_URL || "http://localhost:7777";

export const dynamic = "force-dynamic";

async function ollamaStream(messages: { role: string; content: string }[]): Promise<Response> {
  const upstream = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: CHAT_MODEL,
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      stream: true,
    }),
  });
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const reader = upstream.body!.getReader();
      const decoder = new TextDecoder();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          for (const line of chunk.split("\n")) {
            const t = line.trim();
            if (!t) continue;
            try {
              const json = JSON.parse(t);
              const token = json.message?.content ?? "";
              if (token) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ token })}\n\n`));
            } catch {
              /* skip */
            }
          }
        }
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ done: true, model: CHAT_MODEL })}\n\n`));
      } finally {
        controller.close();
      }
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" },
  });
}

export async function POST(req: NextRequest) {
  let messages: { role: string; content: string }[] = [];
  try {
    const body = await req.json();
    messages = body.messages ?? [];
  } catch {
    return new Response(JSON.stringify({ error: "Missing messages" }), { status: 400 });
  }
  if (!Array.isArray(messages) || messages.length === 0) {
    return new Response(JSON.stringify({ error: "Missing messages" }), { status: 400 });
  }

  // Default: fast direct-Ollama chat. The Python harness (real tools + HITL) is
  // opt-in via the x-agent: tools header — it is slower per turn, so it must not
  // be the default path that the UI depends on for responsiveness.
  if (HARNESS_URL && req.headers.get("x-agent") === "tools") {
    try {
      const upstream = await fetch(`${HARNESS_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
      });
      if (upstream.ok && upstream.body) {
        return new Response(upstream.body, {
          headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" },
        });
      }
    } catch {
      /* fall through to Ollama */
    }
  }

  // AgentOS proxy for PWA chat with tools/HITL. Triggered by x-agent: agnos header.
  if (req.headers.get("x-agent") === "agnos") {
    try {
      const last = messages[messages.length - 1];
      const form = new FormData();
      form.append("message", last?.content ?? "");
      // include simple session continuity
      const sessionId = req.headers.get("x-session-id") ?? undefined;
      if (sessionId) form.append("session_id", sessionId);
      // stream disabled for simple MVP JSON response
      form.append("stream", "false");
      const upstream = await fetch(`${AGENTOS_URL}/teams/agno/runs`, {
        method: "POST",
        body: form,
        // do not forward Authorization here
      });
      if (upstream.ok) {
        const data = await upstream.json();
        // AgentOS returns completed run synchronously when stream false; for MVP return final content as SSE tokens
        const content = typeof data.content === "string" ? data.content : JSON.stringify(data.content ?? "");
        const encoder = new TextEncoder();
        const stream = new ReadableStream({
          start(controller) {
            for (const ch of content) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ token: ch })}\n\n`));
            }
            controller.enqueue(encoder.encode(`data: ${JSON.stringify({ done: true, model: "agentos" })}\n\n`));
            controller.close();
          },
        });
        return new Response(stream, {
          headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" },
        });
      }
    } catch {
      /* fall through to Ollama */
    }
  }

  try {
    return await ollamaStream(messages);
  } catch (e) {
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : String(e) }), { status: 500 });
  }
}
