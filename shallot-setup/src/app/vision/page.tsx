"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Camera, Loader2, Sparkles, Eye, Brain, Shield, Cloud } from "lucide-react";

type Provider = "local" | "nim" | "openrouter";

export default function VisionPage() {
  const [image, setImage] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState<Provider>("local");
  const [cloudAvail, setCloudAvail] = useState<{ nim: string | null; openrouter: string | null } | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ vision: string; reasoning: string | null; models: { vision: string; reason: string }; provider: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch("/api/vision")
      .then((r) => r.json())
      .then((d) => setCloudAvail(d.cloud ?? null))
      .catch(() => {});
  }, []);

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => setImage(reader.result as string);
    reader.readAsDataURL(f);
  }

  async function analyze() {
    if (!image) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/vision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image, prompt: prompt || undefined, provider }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Vision failed");
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background p-4 pb-20 max-w-lg mx-auto">
      <header className="py-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Eye className="w-6 h-6" /> SHALLOT Vision
        </h1>
        <p className="text-sm text-muted-foreground">Fota — lokalt eller fri cloud (ej känsligt)</p>
      </header>

      <Card className="mb-4">
        <CardContent className="pt-6 space-y-4">
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer hover:border-primary/50 transition-colors bg-muted/20"
          >
            {image ? (
              <img src={image} alt="preview" className="max-h-64 mx-auto rounded-lg" />
            ) : (
              <div className="py-8">
                <Camera className="w-10 h-10 mx-auto mb-2 text-muted-foreground" />
                <p className="font-medium">Tryck för att fota</p>
                <p className="text-xs text-muted-foreground">Kamera eller galleri</p>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/*" capture="environment" onChange={onFile} className="hidden" />
          {image && (
            <Button variant="outline" size="sm" onClick={() => setImage(null)} className="w-full">
              Ta bort bild
            </Button>
          )}

          <Textarea
            placeholder="Fråga (valfritt): t.ex. 'Är MOSFET rätt kopplad?'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={2}
          />

          <div className="space-y-2">
            <label className="text-xs font-medium flex items-center gap-1.5">
              <Cloud className="w-3.5 h-3.5" /> Vision-provider
            </label>
            <Select value={provider} onValueChange={(v) => setProvider(v as Provider)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="local">Lokal — llava:13b → mixtral (4080)</SelectItem>
                <SelectItem value="nim" disabled={!cloudAvail?.nim}>
                  NIM Free — {cloudAvail?.nim ?? "ej konfigurerad"} {!cloudAvail?.nim ? "(sätt NIM_API_KEY)" : ""}
                </SelectItem>
                <SelectItem value="openrouter" disabled={!cloudAvail?.openrouter}>
                  OpenRouter Free — {cloudAvail?.openrouter ?? "ej konfigurerad"} {!cloudAvail?.openrouter ? "(sätt OPENROUTER_API_KEY)" : ""}
                </SelectItem>
              </SelectContent>
            </Select>
            {provider !== "local" && (
              <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <Shield className="w-3 h-3" /> Endast för ej känsliga bilder — skickas till {provider === "nim" ? "Nvidia NIM" : "OpenRouter"}
              </p>
            )}
          </div>

          <Button onClick={analyze} disabled={!image || loading} className="w-full">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
            {loading ? "Analyserar..." : "Analysera"}
          </Button>
          <p className="text-xs text-center text-muted-foreground">
            Via Tailscale till Fedora • Reasoning alltid lokalt
          </p>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-destructive mb-4">
          <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="w-4 h-4" /> Vision ({result.models.vision})
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm whitespace-pre-wrap">{result.vision}</CardContent>
          </Card>
          {result.reasoning && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Brain className="w-4 h-4" /> Reasoning ({result.models.reason})
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm whitespace-pre-wrap">{result.reasoning}</CardContent>
            </Card>
          )}
        </div>
      )}

      <p className="text-xs text-center text-muted-foreground mt-8">
        Lägg till på hemskärmen för app-läge • Vision kräver Fedora (Tailscale)
      </p>
    </div>
  );
}
