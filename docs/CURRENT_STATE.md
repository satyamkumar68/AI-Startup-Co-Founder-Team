# Current State Architecture & Baseline Audit

**Audit Date:** 2026-10-27  
**Repository:** AI Startup Co-Founder Team (Multi-Agent Venture Engine)  
**Status:** Baseline Established (58 passing tests)

---

## 1. LangGraph Graph Topology

The core orchestrator is implemented in `backend/app/graph/workflow.py` (`CoFounderWorkflow`):

### Graph Nodes
- `intake`: Validates input idea, initializes `RunState` data structures (tokens, retries, scores, debate log).
- `market_analyst`: Runs `MarketAnalystAgent` with web search & competitor lookup.
- `review_market`: CEO critic review (`CEOCriticAgent`) scoring market analysis (1.0–10.0).
- `product_manager`: Runs `ProductManagerAgent` to generate comprehensive PRD.
- `review_pm`: CEO critic review of PRD.
- `tech_architect`: Runs `TechArchitectAgent` with Mermaid diagram generation and cloud cost estimation.
- `review_architect`: CEO critic review of Tech Architecture.
- `debate_round`: Multi-agent critique and revision engine (`DebateEngine`) between Analyst, PM, and Architect.
- `pitch_writer`: Runs `PitchWriterAgent` to generate 10-slide investor pitch deck with speaker notes.
- `review_pitch`: CEO critic review of final pitch deck.
- `finalize`: Evaluates retry budgets and assigns final status (`completed` or `needs_review`).

### Conditional Edge Routers
- `should_retry_market`: Loops back to `market_analyst` if score < 7.0 (max 2 retries), otherwise advances to `product_manager`.
- `should_retry_pm`: Loops back to `product_manager` if score < 7.0 (max 2 retries), otherwise advances to `tech_architect`.
- `should_retry_architect`: Loops back to `tech_architect` if score < 7.0 (max 2 retries); on pass, routes to `debate_round` (if `debate_rounds > 0`) or directly to `pitch_writer`.
- `should_continue_debate`: Repeats `debate_round` until consensus is reached or `debate_round >= max_rounds`, then routes to `pitch_writer`.
- `should_retry_pitch`: Loops back to `pitch_writer` if score < 7.0 (max 2 retries), then routes to `finalize`.

---

## 2. Model Routing & Providers

Implemented in `backend/app/agents/llm.py` (`MultiProviderLLM`):
- Supported providers: `ollama`, `openrouter`, `openai`, `gemini`, `anthropic`.
- Failover system: `_switch_to_next_model` automatically switches to backup model candidates on 401/timeout/network errors.
- Structured output: `generate_structured` enforces Pydantic schemas with 1 automatic repair retry prompt upon validation failure.

---

## 3. Test Suite Audit

Ran `pytest` on 2026-10-27:
- **Total Tests:** 58 tests
- **Passing:** 58 passed in 22.69s
- **Breakdown:**
  - `tests/integration/test_api.py`: 12 tests (FastAPI route health, run creation, SSE stream, exports)
  - `tests/integration/test_end_to_end_niche.py`: 1 test
  - `tests/unit/test_agents.py`: 2 tests
  - `tests/unit/test_db_models.py`: 2 tests
  - `tests/unit/test_exporters.py`: 10 tests (Markdown, PDF, PPTX, CSV)
  - `tests/unit/test_llm_adapter.py`: 6 tests
  - `tests/unit/test_model_failover.py`: 3 tests
  - `tests/unit/test_schemas.py`: 10 tests
  - `tests/unit/test_tools.py`: 5 tests
  - `tests/unit/test_workflow.py`: 7 tests

---

## 4. Identified Gaps & Deficiencies (Why Current Score is 6.5/10)

1. **Ablation Evidence Gap:**
   - Previous benchmark report in `evals/evaluation_report.md` used hardcoded synthetic numbers in mock mode (every idea showed exactly `8.35` for debate and `7.55` for no debate, with identical latency and tokens).
   - No `single_agent` baseline implementation existed to prove multi-agent superiority over a strong single prompt.
2. **Grounding & Sourcing Discrepancy:**
   - Web search in `backend/app/tools/search.py` returns dictionary keys `href` and `body`, but `MarketAnalystAgent` referenced `url` and `snippet`, resulting in empty context during research synthesis.
   - Cloud cost estimations in `CostEstimatorTool` used arbitrary static hardcoded estimates rather than a pinned, verifiable dataset with source dates.
   - No automated fact-checking node to detect ungrounded figures.
3. **Guardrails & Safety Limits:**
   - No hard budget cap per run ($ or max tokens).
   - No prompt injection sanitization on input startup idea text.
4. **Human-In-The-Loop:**
   - No LangGraph `interrupt` checkpoint for PRD approval prior to pitch deck generation.
5. **Observability & CI:**
   - No native LangSmith / Langfuse integration hooks.
   - Missing GitHub Actions CI workflow for automated testing and container validation.
