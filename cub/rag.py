"""
Local-first Agentic RAG (Agno) for the Cub agent.

Adapted from Agno cookbook (agentic_rag / agentic_rag_with_reasoning /
agentic_rag_with_reranking) to the SHALLOT stack (ADR 0006 §"Agentiskt minne
+ RAG", ADR 0007):

- Zero egress by design: model, embedder and vector store all run locally.
- Embeddings via Ollama `nomic-embed-text` (ADR 0006), not a cloud API.
- LanceDB = serverless local store (mount a Podman volume in prod).
- No Tier-2 cloud path on purpose (deny-by-default, ADR 0006 §6).
- ReasoningTools keep the agentic RAG audit-friendly (AI Act art. 14 framing).

Conflict: ADR 0005 selects Pydantic AI, not Agno. Treat this file as an
alternative inference path until the framework choice is reconciled.

Deps: agno lancedb pyarrow ollama
"""

from agno.agent import Agent
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker.sentence_transformer import SentenceTransformerReranker
from agno.models.ollama import Ollama
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.lancedb import LanceDb, SearchType

CORPUS = [
    # Swap for the real SHALLOT corpus: NIST CSF/800-53, MITRE ATT&CK,
    # CIS v8, SHALLOT ADRs, runbooks, historical audit findings.
    "https://docs.agno.com/introduction.md",
]

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="shallot_corpus",
        search_type=SearchType.hybrid,
        # dimensions MUST match the Ollama embedding model (nomic-embed-text = 768).
        embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
        # Local-first: SentenceTransformer reranker runs in-process, no API/egress.
        # (CohereReranker would violate ADR 0006/0007 zero-egress — do not use.)
        reranker=SentenceTransformerReranker(model="BAAI/bge-reranker-v2-m3"),
    ),
)

agent = Agent(
    model=Ollama(id="llama3.2"),
    knowledge=knowledge,
    search_knowledge=True,  # agentic RAG: query KB on demand
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Include sources in your response.",
        "Always search your knowledge before answering.",
    ],
    markdown=True,
)


if __name__ == "__main__":
    knowledge.insert(name="SHALLOT corpus", url=CORPUS[0])
    agent.print_response(
        "What are the key controls in NIST CSF?",
        stream=True,
        show_full_reasoning=True,
    )
