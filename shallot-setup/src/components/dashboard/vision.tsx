"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Camera, Loader2, Sparkles, Eye, Brain, Shield, Cloud, Image as ImageIcon, Cpu } from "lucide-react";

type Provider = "local" | "nim" | "openrouter";

export function VisionDashboard() {
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
    <div className="flex-1 space-y-6 p-4 md:p-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Eye className="h-6 w-6" /> Vision
        </h2>
        <p className="text-muted-foreground">Analysera valfri bild — hårdvara, schema, komponenter. Lokalt eller fri cloud.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Camera className="h-5 w-5" /> Kamera
            </CardTitle>
            <CardDescription>Fota eller välj bild från galleri</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
              onClick={() => fileRef.current?.click()}
              className="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer hover:border-primary/50 transition-colors bg-muted/20 min-h-[200px] flex items-center justify-center"
            >
              {image ? (
                <img src={image} alt="preview" className="max-h-64 mx-auto rounded-lg object-contain" />
              ) : (
                <div>
                  <ImageIcon className="h-10 w-10 mx-auto mb-2 text-muted-foreground" />
                  <p className="font-medium">Tryck för att välja bild</p>
                  <p className="text-xs text-muted-foreground">Kamera eller galleri — alla motiv</p>
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
              placeholder="Fråga (valfritt): t.ex. 'Identifiera komponenterna och kolla kopplingen'"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
            />

            <div className="space-y-2">
              <label className="text-xs font-medium flex items-center gap-1.5">
                <Cloud className="h-3.5 w-3.5" /> Vision-provider
              </label>
              <Select value={provider} onValueChange={(v) => setProvider(v as Provider)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="local">Lokal — llava:13b → mixtral (4080)</SelectItem>
                  <SelectItem value="nim" disabled={!cloudAvail?.nim}>
                    NIM Free — {cloudAvail?.nim ?? "ej konfigurerad"}
                  </SelectItem>
                  <SelectItem value="openrouter" disabled={!cloudAvail?.openrouter}>
                    OpenRouter Free — {cloudAvail?.openrouter ?? "ej konfigurerad"}
                  </SelectItem>
                </SelectContent>
              </Select>
              {provider !== "local" && (
                <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                  <Shield className="h-3 w-3" /> Endast för ej känsliga bilder
                </p>
              )}
            </div>

            <Button onClick={analyze} disabled={!image || loading} className="w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Sparkles className="h-4 w-4 mr-2" />}
              {loading ? "Analyserar..." : "Analysera"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-6 text-sm text-destructive">{error}</CardContent>
            </Card>
          )}

          {result ? (
            <>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Eye className="h-4 w-4" /> Vision ({result.models.vision})
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm whitespace-pre-wrap leading-relaxed">{result.vision}</CardContent>
              </Card>
              {result.reasoning && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Brain className="h-4 w-4" /> Reasoning ({result.models.reason})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm whitespace-pre-wrap leading-relaxed">{result.reasoning}</CardContent>
                </Card>
              )}
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground/70 px-1">
                <span className="inline-flex items-center gap-1 rounded border px-1.5 py-0.5">
                  <Cpu className="h-3 w-3" /> {result.provider}
                </span>
                <span className="inline-flex items-center gap-1 rounded border px-1.5 py-0.5">
                  vision: {result.models.vision}
                </span>
                {result.reasoning && (
                  <span className="inline-flex items-center gap-1 rounded border px-1.5 py-0.5">
                    reason: {result.models.reason}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 rounded border px-1.5 py-0.5">
                  {result.reasoning ? "chain" : "single-model"}
                </span>
              </div>
            </>
          ) : (
            <Card className="border-dashed">
              <CardContent className="pt-6 text-center text-sm text-muted-foreground py-12">
                <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                Resultat visas här — fota och analysera
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
