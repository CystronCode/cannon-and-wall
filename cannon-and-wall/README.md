---
title: Cannon And Wall
emoji: 🔴🔵
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---

# 🔴🔵 Cannon & Wall — RedBlue Arena

> *A self-improving attacker vs defender RL environment for training LLMs on cybersecurity reasoning.*

**Author:** Jairaj S & Amogh | **Hackathon:** Meta PyTorch × OpenEnv × Scaler School of Technology, April 2026
**Theme:** Self-Improving Agents (Theme 4) + Multi-Agent Interactions (Theme 1)

---

## 🔗 Links

| Resource | URL |
|---|---|
| 🤗 HuggingFace Space (live env) | https://huggingface.co/spaces/CystronCode/cannon-and-wall |
| 📝 Writeup / Model Card | https://huggingface.co/CystronCode/cannon-and-wall-grpo |
| 📓 Training notebook (Colab) | https://colab.research.google.com/drive/1uTSt6DahNVXoAZ0hlpyzrXrn-F6ehc9z?usp=sharing|
| Reward curves | https://wandb.ai/saiamogh7-r-v-c-e/cannon-and-wall/runs/p3uh8q2b |

---

## 🧠 The Problem

LLMs are surprisingly bad at security reasoning — not because they lack knowledge,
but because they have never been trained to think adversarially in a loop.

Current benchmarks test security knowledge statically. There is no environment where:
- An attacker agent gets smarter by failing to find bugs
- A defender agent gets smarter by getting exploited
- Both co-evolve through self-play, round after round

**Cannon & Wall fills that gap.**

---

## 🏟️ What Is the Environment?

A sandboxed Flask web application with seeded OWASP Top 3 vulnerabilities.
Two LLM agents compete inside it:

| Agent | Role | What it does |
|---|---|---|
| 🔴 **Cannon** | Attacker | Reads source code, finds vulnerabilities, proposes exploits |
| 🔵 **Wall** | Defender | Reads Cannon's report, patches the code, hardens the app |
| ⚖️ **Judge** | Verifier | Runs deterministic checks — no LLM-as-judge |

### Vulnerability scope
- SQL Injection (SQLi)
- Cross-Site Scripting (XSS)
- Broken Authentication

### Key design decision — textual reasoning only
Neither agent executes live exploits. All reasoning happens over source code as text.
This keeps the environment safe, reproducible, and trainable.

---

## 🔁 The 3-Phase Self-Play Loop

```
Phase 1 — ATTACK
  Cannon reads the vulnerable Flask app source code
  Cannon outputs: { vuln_type, line_number, explanation, proof_of_concept }

Phase 2 — PATCH
  Wall reads the source code + Cannon's report
  Wall outputs: { patched_code, explanation }

Phase 3 — BYPASS
  Cannon reads original code + Wall's patched version
  Cannon tries to find a remaining vulnerability or bypass

Judge scores both agents after each bypass phase.
Loser faces a harder variant next round.
Both agents improve — neither can memorize.
```

---

## 🏆 Reward Logic

```python
# Cannon (Attacker)
+10   real vulnerability correctly identified
+5    correct vulnerability type (sqli / xss / broken_auth)
+2    exploit novelty bonus (PoC differs from last 3 PoCs — anti-memorization)
-5    false positive reported
+15   bypass succeeded (Wall's patch failed)
+2    bypass novelty bonus

# Wall (Defender)
+5    per vulnerability correctly patched (up to 3)
+5    patched code still works (functionality preserved)
-5    patch introduced a new vulnerability
+5    bypass attempt failed (patch held)

# All rewards normalized to 0.0-1.0 for OpenEnv compliance
# Per-component rewards logged as separate W&B columns for observability
```

### Anti-reward-hacking: exploit novelty
Cannon receives a +2 bonus for producing a PoC that differs from its last 3 PoCs
(Jaccard similarity < 0.6). This directly prevents the agent from memorizing a single
payload string and repeating it every episode.

---

## 📐 Environment Structure

```
cannon-and-wall/
├── openenv.yaml                          # OpenEnv manifest
├── openenv.py                            # Environment base class (local stub)
├── app.py                                # FastAPI wrapper (reset / step / state)
├── Dockerfile                            # Container definition
├── requirements.txt                      # Dependencies
│
├── environment/
│   ├── server.py                         # CannonWallEnvironment class
│   ├── models.py                         # Pydantic schemas
│   ├── curriculum.py                     # Stage progression logic
│   ├── vulnerable_app/
│   │   └── stage_1/app.py               # Seeded Flask app (3 OWASP vulns)
│   └── judge/
│       ├── verifier.py                   # Deterministic patch checker + bandit
│       └── reward.py                     # Multi-component reward calculator
│
├── client/
│   ├── client.py                         # CannonWallClient (httpx)
│   └── models.py                         # Client-side Pydantic models
│
├── agents/
│   ├── cannon_prompt.py                  # Red agent system prompt + helpers
│   └── wall_prompt.py                    # Blue agent system prompt + helpers
│
├── training/
│   └── train_grpo.ipynb                  # TRL + Unsloth GRPO training notebook
│
└── ui/
    └── demo.py                           # Gradio live demo interface
```

---

## 🛡️ Anti-Reward-Hacking Measures

- Judge is **fully deterministic** — static checks + bandit static analysis
- **Multiple independent reward components** — gaming one does not help overall score
- **Proof-of-concept validation** — Cannon must provide a working exploit pattern
- **Hard episode limit** — MAX_ROUNDS=3, prevents infinite loops
- **Dangerous import rejection** — patches with import os, exec(), eval() rejected instantly
- **Functionality preservation check** — Wall must not break the app to score

---

## 🎓 Curriculum

| Stage | File | Task | Vulnerabilities |
|---|---|---|---|
| 1 | `stage_1/app.py` | Single-file login form | SQLi + XSS + Broken Auth (explicit) |
| 2 | `stage_2/app.py` | Split `/auth` + `/search` routes | SQLi + XSS (aliased variable names) |
| 3 | `stage_3/app.py` | Chained + obfuscated portal | SQLi (string join) + XSS (in attribute) + Broken Auth (cookie override) |

Escalation triggers when either agent achieves consistently low reward for 3 episodes.

---

## 🛠️ Training Stack

| Component | Tool |
|---|---|
| RL algorithm | GRPO via HuggingFace TRL |
| Efficiency | Unsloth |
| Base model | Qwen/Qwen2.5-3B-Instruct |
| Environment | OpenEnv (Docker, HF Spaces) |
| Experiment tracking | Weights & Biases |
| Deployment | HuggingFace Spaces (Docker) |

---


## 🔬 Before vs After Training — Qualitative Example

The table below shows a real example of how the Cannon agent's output changes after 50 GRPO training steps.

| | Untrained (Episode 0) | Trained (Episode 50) |
|---|---|---|
| **vuln_type** | `"xss"` (wrong type) | `"sqli"` (correct) |
| **line_number** | `5` (wrong — no vuln there) | `16` (correct — f-string query) |
| **proof_of_concept** | `"<script>test</script>"` | `"' OR 1=1-- "` |
| **Judge verdict** | ❌ False positive (−5 pts) | ✅ Real vuln found + correct type (+15 pts) |
| **Cannon reward** | 0.000 (normalized) | 0.571 (normalized) |

The untrained model guesses XSS on the wrong line. After GRPO training,
it correctly identifies the SQLi on line 16 and produces a valid bypass PoC.
This is the kind of adversarial reasoning improvement the environment is designed to produce.

---
## 📈 Results

### Reward curves

![Reward curve](assets/reward_curve.png)

*Step 0: Cannon reward ≈ 0 (untrained baseline). Step 50: Cannon 
averages 1.38 — consistently identifying and bypassing SQLi vulnerabilities. 
Wall holds stable at 0.713 (100% patch validity rate).*
*Note: Y-axis shows raw pre-normalisation reward values. 
GRPO training uses values normalised to [0.0, 1.0].*

### Results after 50 GRPO training steps

| Metric | Result |
|---|---|
| Cannon avg reward (last 10 steps) | 1.38 (normalized) |
| Wall avg reward | 0.713 (stable) |
| Cannon bypass success rate | ~60% |
| Wall patch validity rate | 100% |
| Training steps | 50 (GRPO gradient updates) |
| Cannon reward at step 0 | 0.0 (untrained baseline) |
| Cannon reward at step 50 | 1.50 (after self-play) |
| Improvement over baseline | +1.38 (>20% criterion met) |
| Base model | Qwen/Qwen2.5-3B-Instruct |
| W&B run | [grpo-training-run](https://wandb.ai/saiamogh7-r-v-c-e/cannon-and-wall/runs/p3uh8q2b) |
| Environment | Live on HuggingFace Spaces |

> **Curriculum:** Stages 1–3 load distinct Flask apps with escalating difficulty
> (see `environment/vulnerable_app/stage_{1,2,3}/`).
> **Training:** The 50-step GRPO run uses `GRPOTrainer.train()` from HuggingFace TRL.
> Each step: G=4 completions are sampled → rewarded by the live environment →
> group-relative advantages are computed → `optimizer.step()` updates the LoRA adapter.
> The trained adapter is saved at `cannon_grpo_adapter/` and pushed to the Hub.

## ▶️ Running Locally

```bash
git clone https://huggingface.co/spaces/CystronCode/cannon-and-wall
cd cannon-and-wall
pip install -r requirements.txt
python app.py
curl -X POST "http://localhost:7860/reset?stage=1"
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /reset?stage=1 | Start new episode, returns source code |
| POST | /step | Send agent action, returns reward + observation |
| GET | /state | Read current episode state |
| GET | /docs | FastAPI Swagger UI |

---

## 💡 Why This Matters

Security is one of the few domains where verification is fully objective,
self-play is naturally adversarial, and the task is genuinely hard for current LLMs.

A model trained in Cannon & Wall learns to reason about code vulnerabilities through
thousands of adversarial rounds — not through static examples.

---

## 📄 License

MIT

---

*Built for the Meta PyTorch x OpenEnv Hackathon, Scaler School of Technology, Bangalore — April 2026*