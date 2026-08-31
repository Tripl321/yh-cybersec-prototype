#!/usr/bin/env bash
#
# push-remaining.sh — RESUME after the first push aborted on a .git-in-URL bug.
# Map #83 already exists; stray D1 = #84 already exists (unresolved). This script
# resolves D1 #84, then creates D2..D10, links them as sub-issues of #83, and
# wires blocking via "Blocked by:" body lines (native dependencies API is 404 here).
#
# Prereq: gh authenticated, run inside the repo clone.
set -euo pipefail

REPO=$(git remote get-url origin | sed -E 's#\.git$##; s#.*[:/]([^/]+/[^/]+)$#\1#')
echo "Target repo: $REPO"
MAP_NUM=83
SUB_H="-H Accept:application/vnd.github.sub-issues-preview+json"

declare -A TICKET_NUM TICKET_BLOCKERS

dbid_of() { gh api "repos/$REPO/issues/$1" --jq '.id'; }

link_sub() {
  local child="$1" cdbid
  cdbid=$(dbid_of "$child")
  gh api --method POST "repos/$REPO/issues/$MAP_NUM/sub_issues" "$SUB_H" \
    -H "Content-Type: application/json" --input - <<<"{\"sub_issue_id\":$cdbid}" >/dev/null 2>&1 \
    && echo "  -> linked #$child as sub-issue" \
    || echo "  -> sub-issue link skipped (fallback: 'Part of #$MAP_NUM' in body)"
}

resolve_ticket() {
  local num="$1" res="$2"
  gh issue comment "$num" --body "$res" >/dev/null
  gh issue close "$num" --comment "$res" >/dev/null
  echo "  -> closed #$num"
}

D1_RES="## Resolution (D1 — HITL delivery mechanism)
- MVP approver: the local operator at the dev machine running the harness. Remote approval deferred.
- MVP mechanism: Agno built-in \`requires_confirmation=True\` terminal confirmation prompt under \`cli_app()\` (already wired on approve_action / run_harness in agno_agent.py). No AgentOS serve required for MVP.
- Correction: the original 'PWA approval UI (#81)' branch is wrong — the only in-repo UI is the stock Agno \`agent-ui\` chat client, which only receives confirmation interrupts when AgentOS is *served* (that is ticket D2). The served/PWA approval path is deferred to after D2.
- Terminology: one HITL glossary term added to CONTEXT.md, covering both SHALLOT Harness (Agno durable/restart-safe HITL) and Cub (Pydantic AI deferred tools)."

D2_RES="## Resolution (D2 — Transport: AgentOS serve vs cli)
- MVP transport: CLI-first default (\`cli_app()\`); AgentOS.serve(:7777) is opt-in via env flag \`SHALLOT_SERVE=1\` / \`--serve\`. One \`shallot\` Agent object, two entrypoints behind the flag.
- Served chat/approval adapter: AG-UI (Agno-native; what stock agent-ui speaks on :7777). ACP is the Cub/ADR-0007 stack and is NOT used for the harness.
- AgentOS.serve is IN-MVP but opt-in — keeps D7 (MCP git-server) and D9 (e2e) reachable without making a running server a prerequisite for the core local CLI experience.
- Build seam (#82, not done here): enable the AgentOS.serve path in agno_agent.py:132 guarded by SHALLOT_SERVE; MCP remains for tool integration (D7). Note: cannot be verified in this env (no agno/ollama)."

# --- D1: resolve existing #84, link ---
TICKET_NUM[D1]=84
echo "Resolving existing D1 (#84)..."
link_sub 84
resolve_ticket 84 "$D1_RES"

create_ticket() {
  local key="$1" type="$2" title="$3" body="$4" blockers="$5"
  local blk="" b num
  if [ -n "$blockers" ]; then
    blk="Blocked by:"
    IFS=',' read -ra B <<< "$blockers"
    for b in "${B[@]}"; do blk="$blk #${TICKET_NUM[$b]}"; done
    blk="$blk"$'\n'
  fi
  local full="Part of #$MAP_NUM

$blk## Question
$body"
  num=$(gh issue create --label "wayfinder:$type" --title "$title" --body "$full" | grep -oE '[0-9]+$')
  echo "Creating $key ($type): #$num"
  TICKET_NUM[$key]=$num
  link_sub "$num"
  TICKET_BLOCKERS[$key]=$blockers
}

create_ticket D2 grilling "Transport: AgentOS serve vs cli" \
"Which MVP transport + adapter? (RESOLVED: CLI-first default via cli_app(); AgentOS.serve(:7777) opt-in via SHALLOT_SERVE=1/--serve, one shallot Agent, two entrypoints. Served chat/approval adapter = AG-UI, not ACP. AgentOS.serve is in-MVP but opt-in.) Original tension: build-ref #82 step 4 wants AgentOS.serve; agno_agent.py defaults to cli_app(). Decision recorded in Decisions so far." ""
resolve_ticket "$(printf '%s' "${TICKET_NUM[D2]}")" "$D2_RES"

create_ticket D3 research "Model reconciliation + vision policy" \
"Confirm \`ministral-3:8b\` (ADR 0010) as default harness model over \`llama3.2\` (ADR 0006); set \`VISION_MODEL=qwen3-vl:8b\`. The two are different agents/stacks — verify intentional, and confirm both tags run on the RTX 4080 Fedora box. Do NOT harmonize." ""

create_ticket D4 research "RAG / knowledge inclusion in MVP" \
"Include SHALLOT docs as agent knowledge now, or defer to Postgres+pgvector (build-ref says post-MVP)? Weigh \`enable_agentic_memory=True\` (already on) vs explicit RAG (see cub/rag.py experiment). Decide MVP knowledge-grounding scope." ""

create_ticket D5 task "Memory backend migration path" \
"Define the seam from MVP SqliteDb + agentic memory to post-MVP PostgreSQL+pgvector (ADR 0010) with durable scheduling. What interface must agno_agent.py hide behind so the storage swap is non-breaking? Depends on D4." "D4"

create_ticket D6 task "Observability in MVP" \
"Include any local tracing/observability (MLflow/Latitude local) in MVP, or fully post-MVP? Any tool must be self-hostable, no cloud egress. Decide minimal signal the harness emits locally." ""

create_ticket D7 task "Connect MCP git-server" \
"Wire the existing MCP git-server (build-ref #82). Shape depends on D2 (transport+adapter). Confirm the MCP server is available locally; define the repo-operation tool surface (read-only per \`git * → deny\` unless granted). See D10 auth gap." "D2"

create_ticket D8 grilling "run_harness safety policy" \
"\`run_harness\` is a shell-exec tool gated by \`requires_confirmation=True\` — powerful, high-risk until an allowlist exists. Define: repo-root confinement, no network egress, permitted command patterns. Must sit within cub.hooks egress-deny + provenance policy." ""

create_ticket D9 task "Verification & e2e" \
"Define MVP verification: AgentOS endpoint answers via local Ollama; approve_action/run_harness pause for HITL and continue after approval; serves on :7777 (acceptance for #82). Needs the RTX 4080 box (no agno/ollama here). Depends on D2 (D1 resolved: MVP HITL = terminal prompt under cli_app). Note: if MVP stays CLI-first per D2, verification runs via cli_app() not :7777." "D2"

create_ticket D10 task "Agent gh/wayfinder access" \
"Provision gh auth so the agent can read/create issues (currently \`gh * → ask\`, \`git * → deny\`). Decide credential scope (read vs write issues) + location, consistent with local-first / zero-egress. Unblocks the agent's own wayfinder participation." ""

echo
echo "=== Map #$MAP_NUM charted. D1/D2 resolved; D3..D10 open. ==="
echo "Research tickets D3/D4: resolve via research subagents (branch research/<name>) before others."
echo "Frontier: open, unblocked, unassigned children of #$MAP_NUM (drop any with open blocker / assignee)."
