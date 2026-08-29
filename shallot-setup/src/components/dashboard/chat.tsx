"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Loader2, Trash2, Cpu, Wrench, ShieldCheck, Check, X } from "lucide-react";

type ToolCall = { name: string; args: string; result: string };
type Msg = { role: "user" | "assistant"; content: string; model?: string; tools?: ToolCall[] };
type Approval = { action_id: string; kind: string; target: string };

export function ChatDashboard() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: "Hej! Jag är SHALLOT Harness — jag kan använda verktyg (projektstatus, minne, godkännanden). Fråga mig om projektet eller be mig analysera en bild via Vision." },
  ]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    fetch("/api/approve").then((r) => r.json()).then((d) => setApprovals(d.approvals ?? [])).catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, streaming, approvals]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    setStreaming(true);

    const assistant: Msg = { role: "assistant", content: "", tools: [] };
    setMessages([...next, assistant]);

    const ac = new AbortController();
    abortRef.current = ac;
    watchdogRef.current = setTimeout(() => {
      ac.abort();
      assistant.content = assistant.content || "[avbruten: svaret dröjde för långt — försök igen]";
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { ...assistant };
        return copy;
      });
      setLoading(false);
      setStreaming(false);
    }, 50000);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(agentMode ? { "x-agent": "agnos" } : {}),
        },
        body: JSON.stringify({ messages: next }),
        signal: ac.signal,
      });
      if (!res.ok || !res.body) throw new Error((await res.json()).error || "Chat failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n\n");
        buf = lines.pop() ?? "";
        for (const ev of lines) {
          const line = ev.trim();
          if (!line.startsWith("data: ")) continue;
          const data = JSON.parse(line.slice(6));
          if (data.token) {
            assistant.content += data.token;
          } else if (data.tool_call) {
            assistant.tools = [...(assistant.tools ?? []), data.tool_call];
          } else if (data.model) {
            assistant.model = data.model;
          } else if (data.approvals) {
            setApprovals(data.approvals);
          } else if (data.done) {
            assistant.model = data.model ?? assistant.model;
          } else if (data.error) {
            assistant.content = `Fel: ${data.error}`;
          }
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { ...assistant };
            return copy;
          });
        }
      }
    } catch (e) {
      if ((e as any)?.name !== "AbortError") {
        assistant.content = `Fel: ${e instanceof Error ? e.message : String(e)}`;
        setMessages((m) => {
          const copy = [...m];
          copy[copy.length - 1] = { ...assistant };
          return copy;
        });
      }
    } finally {
      if (watchdogRef.current) clearTimeout(watchdogRef.current);
      setLoading(false);
      setStreaming(false);
    }
  }

  async function approve(id: string) {
    setApprovals((a) => a.filter((x) => x.action_id !== id));
    await fetch("/api/approve", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action_id: id }) }).catch(() => {});
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] p-4 md:p-6 gap-4 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Bot className="h-6 w-6" /> Chat
          </h2>
          <p className="text-muted-foreground text-sm">SHALLOT Harness — verktyg + HITL, lokalt via ministral-3:8b</p>
        </div>
        {approvals.length > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-1 text-xs text-amber-700 dark:text-amber-400">
            <ShieldCheck className="h-3.5 w-3.5" /> {approvals.length} väntar på godkännande
          </span>
        )}
        <Button
          variant={agentMode ? "default" : "outline"}
          size="sm"
          onClick={() => setAgentMode((v) => !v)}
          title="Slå på agent-läge (verkliga verktyg + HITL). Långsammare per svar."
        >
          <Wrench className="h-4 w-4 mr-1" /> {agentMode ? "Agent: PÅ" : "Agent: AV"}
        </Button>
      </div>

      {approvals.length > 0 && (
        <Card className="border-amber-500/40 bg-amber-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2 text-amber-700 dark:text-amber-400">
              <ShieldCheck className="h-4 w-4" /> Väntande godkännanden (HITL)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {approvals.map((a) => (
              <div key={a.action_id} className="flex items-center justify-between gap-2 rounded-lg border bg-background/60 px-3 py-2">
                <div className="min-w-0">
                  <div className="font-mono text-xs">{a.kind}</div>
                  <div className="truncate text-xs text-muted-foreground">{a.target}</div>
                </div>
                <Button size="sm" onClick={() => approve(a.action_id)} className="shrink-0">
                  <Check className="h-4 w-4 mr-1" /> Godkänn
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="pb-2 flex flex-row items-center justify-between">
          <CardTitle className="text-base">Konversation</CardTitle>
          <Button variant="ghost" size="sm" onClick={() => setMessages(messages.slice(0, 1))}>
            <Trash2 className="h-4 w-4 mr-1" /> Rensa
          </Button>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col min-h-0 p-0">
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-4 py-4">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex gap-2 max-w-[85%] ${m.role === "user" ? "flex-row-reverse" : ""}`}>
                    <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                      {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className="space-y-2">
                      <div className={`rounded-2xl px-4 py-2 text-sm whitespace-pre-wrap ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                        {m.content}
                        {streaming && i === messages.length - 1 && m.role === "assistant" && (
                          <span className="inline-block w-2 h-4 ml-0.5 bg-current animate-pulse align-middle" />
                        )}
                      </div>

                      {m.tools && m.tools.length > 0 && (
                        <div className="space-y-1.5">
                          {m.tools.map((t, ti) => (
                            <details key={ti} className="rounded-lg border bg-background/50 text-xs">
                              <summary className="flex cursor-pointer items-center gap-1.5 px-2.5 py-1.5 font-medium">
                                <Wrench className="h-3.5 w-3.5 text-primary" /> {t.name}
                              </summary>
                              <div className="space-y-1 border-t px-2.5 py-1.5 font-mono text-[11px] text-muted-foreground">
                                <div><span className="text-foreground/70">args:</span> {t.args}</div>
                                {t.result && <div><span className="text-foreground/70">→</span> {t.result.slice(0, 300)}{t.result.length > 300 ? "…" : ""}</div>}
                              </div>
                            </details>
                          ))}
                        </div>
                      )}

                      {m.role === "assistant" && m.model && (
                        <div className="flex items-center gap-1 text-[10px] text-muted-foreground/70 px-1">
                          <Cpu className="h-3 w-3" /> {m.model}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {loading && !streaming && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-muted rounded-2xl px-4 py-2 text-sm flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Tänker...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          </ScrollArea>

          <div className="p-4 border-t flex gap-2">
            <Textarea
              placeholder="Skriv meddelande..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              rows={1}
              className="min-h-[44px] max-h-32 resize-none"
            />
            <Button onClick={send} disabled={loading || !input.trim()} size="icon" className="h-[44px] w-[44px] shrink-0">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
