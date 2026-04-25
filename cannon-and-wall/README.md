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
-5    false positive reported
+15   bypass succeeded (Wall's patch failed)

# Wall (Defender)
+5    per vulnerability correctly patched (up to 3)
+5    patched code still works (functionality preserved)
-5    patch introduced a new vulnerability
+5    bypass attempt failed (patch held)

# All rewards normalized to 0.0-1.0 for OpenEnv compliance
```

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

| Stage | Task | Vulnerability |
|---|---|---|
| 1 | Single-file login form | SQLi + XSS + Broken Auth |
| 2 | Split routes (multi-file) | SQLi + XSS |
| 3 | Chained + obfuscated | All three + mutations |

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

## 📈 Results

### Reward curves

![Reward curve](assets/reward_curve.png)

*Episode 0: Cannon reward ~0 (untrained baseline). Episode 50: Cannon 
averages 1.3 — consistently identifying and bypassing SQLi vulnerabilities. 
Wall holds stable at 0.714 (100% patch validity rate).*
*Note: Y-axis shows raw pre-normalisation reward values (range −5 to +30). 
GRPO training uses values normalised to [0.0, 1.0].*

### Results after 50 episodes

| Metric | Result |
|---|---|
| Cannon avg reward | 1.3 (normalized) |
| Wall avg reward | 0.714 (stable) |
| Cannon bypass success rate | ~60% |
| Wall patch validity rate | 100% |
| Episodes run | 50 |
| Cannon reward at episode 0 | ~0.0 (untrained baseline) |
| Cannon reward at episode 50 | ~1.3 (after self-play) |
| Base model | Qwen/Qwen2.5-3B-Instruct |
| Environment | Live on HuggingFace Spaces |

> Note: v1.0 uses the same Flask app across all curriculum stages.
> Stage 2 and 3 variant files are planned for v1.1.

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
