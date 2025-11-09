# **MoST — Mixture of Socratic Thoughts**

*A tri-agent iterative reasoning framework for improving LLM reliability.*

MoST is an experimental reasoning architecture designed to improve an LLM’s accuracy, stability, and step-by-step reasoning through a structured multi-agent loop.
It is built by a young developer (age 13), so the project evolves rapidly as experiments continue.

---

## ⭐ **What is MoST?**

MoST stands for **Mixture of Socratic Thoughts** — a system where multiple “thinking agents” collaborate to solve a task more reliably than a single LLM.

The core idea:

> Instead of asking an LLM to answer directly, split the thinking process into *roles* and let them collaborate under supervision.

The MVP (Minimum Viable Product) of MoST uses **three agents**:

### ✅ **1. U-LM (User-Like Model)**

Rephrases each step as a natural language instruction, acting like a questioning partner.

### ✅ **2. R-LM (Responder Model)**

Attempts to answer the U-LM’s question.

### ✅ **3. Meta-Agent** *(Coming soon)*

Supervises the turn, checks for correctness, and decides whether:

* the step is complete
* R-LM hallucinated or drifted
* the U-LM needs to ask a better question
* the loop should retry or move on

This creates a **controlled feedback loop**:

```
U-LM → R-LM → Meta-Agent → U-LM → R-LM → ...
```

…until the Meta-Agent decides the step is finished.

---

## 🧠 **Why MoST?**

Large Language Models often struggle with:

* multi-step reasoning
* task consistency
* state tracking
* hallucinations
* long chain-of-thought drift

MoST attempts to fix this by *splitting* the reasoning into roles and supervising each turn.

Even small improvements over the baseline LLM count — this is research and experimentation, not a finished product.

---

## 📁 **Project Structure**

```
MoST/
├── main.py
├── utils/
│   ├── lm.py
│   ├── loading.py
│   ├── clean_output.py
│   ├── colourized_logs.py
├── prompts/
│   ├── planner/
│   │   └── planner.md
│   ├── u_lm/
│   │   └── u_lm.md
│   ├── r_lm/
│   │   └── r_lm.md
│   └── meta_agent/
│       └── meta_agent.md   (coming soon)
└── README.md
```

---

## 🚀 **Running the Project**

Make sure you're inside the virtual environment, then run:

```bash
python main.py
```

The process:

1. The **Planner** produces a step-by-step reasoning plan.
2. For each step:

   * U-LM reformulates the step as a question.
   * R-LM answers it.
   * *(Soon)* Meta-Agent judges correctness.
3. The system continues until all steps are complete.

Logs are colourized and show each agent’s output.

---

## 🧪 Example Tasks

MoST has been tested on:

* word breakdown tasks
* counting tasks
* classic logic riddles (e.g., wolf–goat–cabbage)
* simple reasoning problems

Early tests show promising improvements when Meta-Agent supervision is added.

---

## 🔮 **Roadmap**

MoST MVP (now)

✅ Planner
✅ U-LM
✅ R-LM
🟥 Meta-Agent (in progress)
🟥 Step completion detection
🟥 Retry + correction loop

Planned additions:

* ✅ **Critics (Factual, Logical, Ethical, Creative)**
* ✅ **Ensemble scoring / confidence aggregation**
* ✅ **CGS – Context-Grabbing System**
* ✅ **LAMS – Long-Term Memory System**
* ✅ **Background Mind / reflective processes**
* ✅ **Improved state tracking and grounding**

MoST will grow in complexity over time.

---

## 🤝 Contributing

This is an experimental research project.
Pull requests, suggestions, and improvements are welcome — just be kind and constructive.

---

## ⚠️ Disclaimer

MoST is an independent research project created for fun and learning.
It is *not* a commercial product, and it may break, hallucinate, or behave unpredictably.
The author is 13, so some design choices are intentionally simple or experimental.