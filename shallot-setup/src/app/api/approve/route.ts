import { NextRequest, NextResponse } from "next/server";

const HARNESS_URL = process.env.HARNESS_URL || "";

export async function POST(req: NextRequest) {
  if (!HARNESS_URL) return NextResponse.json({ error: "HARNESS_URL not configured" }, { status: 400 });
  try {
    const { action_id } = await req.json();
    const res = await fetch(`${HARNESS_URL}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id }),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : String(e) }, { status: 500 });
  }
}

export async function GET() {
  if (!HARNESS_URL) return NextResponse.json({ approvals: [] });
  try {
    const res = await fetch(`${HARNESS_URL}/approvals`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ approvals: [] });
  }
}
