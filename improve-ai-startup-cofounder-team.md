# Improvement Plan: AI Startup Co-Founder Team (Multi-Agent Venture Engine)

**Current rating: 6.5/10 → Target: 8.5/10**
**Why it's lower:** multi-agent LangGraph pipelines are very common. Your project's claim ("higher quality with peer debate") rests on 10 self-picked ideas and likely LLM-judged scores. Output quality (TAM numbers, cost estimates) can look plausible but be hallucinated — a rigorous technical audit will probe exactly that.

---

## P0 — Must do

### 1. Make the "debate improves quality" claim defensible
Your core selling point. Right now it's weak evidence.

- Run an **ablation**: (a) single-agent baseline, (b) multi-agent no debate, (c) multi-agent with debate. Same ideas, same model, same prompts otherwise.
- Use **more than 10 ideas** (30–50), including bad/unrealistic ideas.
- Score with a **rubric** (market realism, internal consistency, feasibility, specificity) using:
  - LLM judge from a *different model family* than the generator (avoid self-preference bias), AND
  - **Human scoring** on a subset (even 10 ideas × 3 friends/peers = real signal).
- Report: mean, std dev, win-rate (pairwise), **cost and latency per run** for each setup.
- **Done when:** README table shows debate vs no-debate vs single-agent with cost/latency trade-off. If debate does *not* help, say so — that is still a strong honest result.

### 2. Ground the numbers (stop hallucinated TAM/SAM/SOM and cloud costs)
- Add a **web-search / data tool** to the market agent; require **source URLs** for every market figure.
- Cloud cost estimates: compute from real pricing data (AWS/GCP pricing API or a pinned pricing JSON) rather than LLM guesses.
- Add a **fact-check / citation agent** that flags unsupported claims in the final deliverables.
- **Done when:** every number in the PRD/pitch deck has a source or is labeled "assumption".

### 3. Cost, latency, reliability numbers
Report per run: total tokens, $ cost, wall-clock time, retry rate, schema-repair rate, provider-fallback rate (e.g. "avg run costs $0.18 and takes 94s; schema repair triggered in 7% of runs.")

---

## P1 — Should do

### 4. Observability and tracing
- Integrate LangSmith / Langfuse / OpenTelemetry. Screenshot a trace in the README.
- Log each agent's input, output, tokens, and latency.

### 5. Guardrails & failure handling (prove "reliability")
- Test: malformed JSON, provider outage (fallback triggers), infinite debate loop (max-iteration cap), prompt injection via the startup idea text.
- Add a hard **budget cap** (max tokens/$) per run.

### 6. Human-in-the-loop
- Use LangGraph `interrupt` so the user can approve/edit the PRD before the pitch deck stage. This is a commonly expected production pattern.

### 7. Tests & CI
- 57 tests is good; make them **visible**: GitHub Actions + badge, mocked-LLM deterministic tests, plus one recorded-response integration test.
- Add schema validation tests per agent output.

---

## P2 — Nice to have
- Persistent run history + comparison view (v1 vs v2 of a deck).
- Pluggable agent roles via config (YAML), so it's a framework, not one pipeline.
- Docker compose one-command run; `.env.example` with clear provider setup.
- Short blog post / write-up of the ablation results (public proof of depth).

---

## README structure to use
1. One-line pitch + **Live demo** + **Interactive walkthrough** + sample outputs
2. Results table (single vs multi vs debate; quality, cost, latency)
3. Architecture graph (LangGraph node diagram)
4. How grounding works (sources, fact-check agent)
5. Reliability (fallback, repair, retries, budget cap) with numbers
6. Quick start
7. Evaluation methodology + reproduction command
8. Limitations (be explicit: LLM judges are biased, small sample, market data may be stale)

---

## Technical highlight summary (after P0)
> Built a LangGraph multi-agent system (FastAPI, React) that converts a startup idea into market sizing, PRD, architecture with cost estimates, and a pitch deck; ablation on **N ideas** showed peer debate raised rubric score **A → B** (human-validated on a subset) at **+C% cost**; market figures source-cited; provider fallback + schema repair kept failure rate at **D%**.[GitHub]

Use only numbers you actually measure.

