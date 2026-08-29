import { NextRequest, NextResponse } from "next/server";

const OLLAMA_HOST = process.env.OLLAMA_HOST || "http://localhost:11434";
// Single vision+reasoning VLM (Mistral track, fits 16 GB VRAM). qwen3-vl:8b is the stronger
// general-vision alternative — set VISION_MODEL=qwen3-vl:8b to switch. See docs/research/model-selection-rtx4080-2026.md
const VISION_MODEL = process.env.VISION_MODEL || "ministral-3:8b-instruct-2512-q4_K_M";
const REASON_MODEL = process.env.REASON_MODEL || "ministral-3:14b";

// BOM-grounded wiring checklist — research ROI #1 (RAG prompt) + #2 (stronger VLM).
const VISION_SYSTEM = `You are SHALLOT Harness vision analyst for OT hardware (RP2350 Pico 2W, SX1262 LoRa, ESP32-S3 pico-fido2, Noctua NF-A4x10 fan, 30N06L MOSFET, 1N4007 diode). Analyze the image generically — any electronics, not just breadboards. Identify components, pins, and wiring. Flag: wrong polarity, missing pull-ups, shorts, reversed MOSFET, loose connections. Output structured: components[], issues[], checks[]. Match user language (Swedish/English).`;

// Free cloud providers — only for non-sensitive images
const NIM_HOST = "https://integrate.api.nvidia.com/v1";
const NIM_MODEL = process.env.NIM_VISION_MODEL || "nvila"; // or meta/llama-3.2-11b-vision-instruct
const OPENROUTER_HOST = "https://openrouter.ai/api/v1";
const OPENROUTER_MODEL = process.env.OPENROUTER_VISION_MODEL || "qwen/qwen2.5-vl-7b-instruct:free";

async function ollamaChat(model: string, messages: unknown, timeoutMs = 120000) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${OLLAMA_HOST}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model, messages, stream: false }),
      signal: controller.signal,
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Ollama ${model} ${res.status}: ${txt.slice(0, 500)}`);
    }
    const data = await res.json();
    return data.message?.content ?? data.response ?? "";
  } finally {
    clearTimeout(t);
  }
}

async function openAIChat(
  baseUrl: string,
  apiKey: string,
  model: string,
  messages: unknown,
  timeoutMs = 60000
) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
        ...(baseUrl.includes("openrouter") ? { "HTTP-Referer": "https://shallot.local", "X-Title": "SHALLOT Vision" } : {}),
      },
      body: JSON.stringify({ model, messages, max_tokens: 2048 }),
      signal: controller.signal,
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`${baseUrl} ${model} ${res.status}: ${txt.slice(0, 600)}`);
    }
    const data = await res.json();
    return data.choices?.[0]?.message?.content ?? "";
  } finally {
    clearTimeout(t);
  }
}

export async function POST(req: NextRequest) {
  try {
    const { image, prompt, chain, provider } = await req.json();

    if (!image || typeof image !== "string") {
      return NextResponse.json({ error: "Missing image (base64)" }, { status: 400 });
    }
    const b64 = image.includes(",") ? image.split(",")[1] : image;
    if (b64.length < 100) {
      return NextResponse.json({ error: "Image too small" }, { status: 400 });
    }

    const userPrompt = prompt || "Analyze this image. Identify the components and wiring, and flag any errors or risks. Be concise and structured.";
    const dataUrl = `data:image/jpeg;base64,${b64}`;

    // Provider selection: local (default) | nim | openrouter
    // Policy: cloud only if provider explicitly requested and image is non-sensitive (client opts in)
    let vision: string;
    let visionModelUsed: string;

    if (provider === "nim") {
      const key = process.env.NIM_API_KEY;
      if (!key) return NextResponse.json({ error: "NIM_API_KEY not set on server" }, { status: 400 });
      visionModelUsed = `nim:${NIM_MODEL}`;
      vision = await openAIChat(NIM_HOST, key, NIM_MODEL, [
        { role: "user", content: [{ type: "text", text: userPrompt }, { type: "image_url", image_url: { url: dataUrl } }] },
      ]);
    } else if (provider === "openrouter") {
      const key = process.env.OPENROUTER_API_KEY;
      if (!key) return NextResponse.json({ error: "OPENROUTER_API_KEY not set on server" }, { status: 400 });
      visionModelUsed = `openrouter:${OPENROUTER_MODEL}`;
      vision = await openAIChat(OPENROUTER_HOST, key, OPENROUTER_MODEL, [
        { role: "user", content: [{ type: "text", text: userPrompt }, { type: "image_url", image_url: { url: dataUrl } }] },
      ]);
    } else {
      visionModelUsed = VISION_MODEL;
      vision = await ollamaChat(VISION_MODEL, [
        { role: "system", content: VISION_SYSTEM },
        { role: "user", content: userPrompt, images: [b64] },
      ]);
    }

    let reasoning: string | null = null;
    if (chain === true) {
      const reasonPrompt = `You are SHALLOT Harness — OT access control assistant. Vision analysis:\n\n${vision}\n\nUser question: ${userPrompt}\n\nProvide: 1) what you see, 2) wiring/component errors, 3) next check. Be concise, match user language (Swedish/English).`;
      try {
        // Reasoning always local (sensitive context stays on Fedora)
        reasoning = await ollamaChat(REASON_MODEL, [{ role: "user", content: reasonPrompt }]);
      } catch {
        reasoning = null;
      }
    }

    return NextResponse.json({
      vision,
      reasoning,
      models: { vision: visionModelUsed, reason: REASON_MODEL },
      provider: provider || "local",
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function GET() {
  try {
    const res = await fetch(`${OLLAMA_HOST}/api/tags`);
    const data = await res.json();
    const models = (data.models ?? []).map((m: { name: string }) => m.name);
    const hasNim = !!process.env.NIM_API_KEY;
    const hasOpenRouter = !!process.env.OPENROUTER_API_KEY;
    return NextResponse.json({
      ollama: OLLAMA_HOST,
      models,
      vision: VISION_MODEL,
      reason: REASON_MODEL,
      cloud: { nim: hasNim ? NIM_MODEL : null, openrouter: hasOpenRouter ? OPENROUTER_MODEL : null },
    });
  } catch (e) {
    return NextResponse.json({ error: String(e), ollama: OLLAMA_HOST }, { status: 500 });
  }
}
