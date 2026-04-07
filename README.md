# Skill Harvester 

[English](README.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

## Core Credo: Humanity is an end, never merely a means. - Kant ## 
> The design's starting point is to help people offload the cognitive burden of mundane labor. By delegating automatable implicit rules to a personal AI Agent, individuals are liberated from repetitive operations, allowing them to fully refocus their energy on creative work.

## Theoretical Foundation & Design Philosophy: What is a Skill?

From the perspectives of logic and cognitive science, a "Skill" points to the same core phenomenon: compressing explicit knowledge into an automated procedure that can be called directly. To make this easier to understand, we use Feynman-style analogies:

1. **Logical Perspective (Translating "Muscle Memory" back to an "Operations Manual")**
   Gilbert Ryle distinguishes between "Knowing That" (propositional knowledge) and "Knowing How" (procedural knowledge). A Skill is essentially the carrier of the latter.
   **Analogy: You know how to ride a bicycle (Knowing How/muscle memory), but you might not be able to write an instruction manual teaching someone else how to ride it (Knowing That/knowledge manual).** Many routine tasks workers repeat daily become this kind of muscle memory. Our job is to use dialogue to unravel this "muscle memory" back into an "automated rule manual" that machines can understand.

2. **Cognitive Science Perspective (Dissecting the "Veteran's Intuition")**
   In ACT-R theory, this is the "Knowledge Compilation" process—long-term practice internalizes rules, and experts often "cannot explain why" (Tacit Knowledge).
   **Analogy: Just like when you first learn to drive, you consciously think "step on the clutch, then shift gears". But a veteran driver brakes instantly in an emergency; if you ask why, they just say "intuition".** In your day-to-day work, you've become a "veteran", and Skill Harvester gently fishes out these silent "veteran intuitions".

3. **Differences Between "Event Recording" & "Logical Compilation": Why Not Just Record Screens?**
   Traditional RPA is an "Event Recorder", while this system generates "Productions" (IF-THEN logical rules).
   **Analogy: Traditional screen recording is like a video camera; it only captures "you pressed Key A, then unplugged the power"—these are events. If your keyboard moves, it's blind. A production, however, is a recipe: it tells you "IF the water boils (Condition), THEN turn off the heat (Action)".** Our intention isn't to "rote memorize your actions", but to understand "under what circumstances you decide to do this".

4. **Breaking Free from Exploitation & Digital Alienation (Liberating Productivity)**
   Traditional monitoring or RPA just observes the "redundant click stream resulting from a clumsy system", which actually exacerbates the user's passivity. Skill Harvester does not extract employee knowledge to fortify corporate moats.
   Its core mechanism is: building your personal digital co-pilot, extracting the mechanical and tedious parts of your work into a "cognitive exoskeleton" for the machine, allowing you to focus on irreplaceable, high-value tasks.

## Core Design and Occam's Razor

Human workflows are cluttered with a massive amount of meaningless actions like mouse jitters and window switching. How does the system find effective decisions using the minimal path?

1. **Information = Surprisal**
   **Analogy: Just as you normally don't hear the hum of your refrigerator compressor, but immediately notice if it suddenly stops.** Routine operations (like opening emails or copy-pasting) are "white noise" with an information value near zero, needing no recording. The system only opens its eyes at the moment an "accident" happens.
   
2. **Focusing on "Golden Moments"**
   Given the above, we only capture nodes with abnormal fluctuations: **long pauses, undo actions (Ctrl+Z), frequent window switching for research**, etc. These are the moments when tacit knowledge is forced up from the subconscious.

3. **Externalizing Tacit Knowledge (Cognitive Task Analysis)**
   After capturing these golden moments, the system gently asks a counterfactual question during your natural break before clocking out: "You hesitated for 5 seconds here; were you comparing this amount to a specific number?" — With just this one sentence, your god-tier experience is extracted into a line of code.

## Five-Layer System Architecture

By capturing "golden moments", we map your actions into a 5-layer compression process:

1. **L0 Task Catalog**: Provides prior intent, your explicit daily work declaration. *(Analogy: The list of things you plan to do today)*
2. **L1 Sparse Sensor**: Monitors the event stream with extremely low overhead. *(Analogy: No video recording, just a stethoscope listening for big changes like app switching)*
3. **L2 Episode Builder**: Triggers saving an "episode" snapshot only at prediction error peaks. *(Analogy: Notices you're stuck or hit undo, quickly snaps a screenshot and saves the last 30 seconds)*
4. **L3 Dialogue Engine**: Initiates counterfactual questioning. *(Analogy: Following the snapshot, asks you a quick multiple-choice question)*
5. **L4 Production Inducer**: Extracts IF-THEN logic and decouples intention from execution. *(Analogy: Compares your hesitation yesterday with today to induce the real rule)*
6. **L5 Skill Compiler**: Translates reasoning results into an executable `.md` script for the Agent. *(Analogy: Writes the final operating manual delivered to the robot)*

*(Design documents [v1](./skill-harvester-design.md) & [v2](./skill-harvester-design-v2.md) are available in Chinese)*

## Running: Phase 1 MVP

This repository is currently in the Phase 1 closed-loop prototype stage. The goal is to **run the L3→L4→L5 pipeline once**, completing the validation of "manual episode submission -> production compilation".

### Quick Start

```bash
# 1. Install
pip install -e .

# 2. Prepare Task List
cp examples/task_list.example.yaml ~/.skill-harvester/task_list.yaml
# Edit task_list.yaml with your daily tasks

# 3. Start Phase 0 "Keystroke Capture" mode
skill-harvester capture
# While working, press Ctrl+Alt+M to mark a difficult branch you want to automate

# 4. Do Counterfactual Questioning in the evening
skill-harvester review

# 5. Run induction after gathering enough episodes
skill-harvester induce

# 6. Compile into exclusive automated SKILL.md
skill-harvester compile

# Output: ./skills/pending/<task_id>.md
```

### Environment Config

Defaults to a mock backend for local experiments. To use real models:
```bash
export SKILL_HARVESTER_LLM=anthropic   # or openai / mock
export ANTHROPIC_API_KEY=...
```

### Project Structure

```
skill_harvester/
├── models.py       # Data structures: TaskCatalog, Episode, Production
├── storage.py      # Episode serialization & secure storage
├── llm.py          # LLM backend abstraction
├── capture.py      # L1/L2: Hotkey capture & episode building
├── classifier.py   # L3 step 1: Goal semantic classification
├── dialogue.py     # L3 step 2: Interactive counterfactual questioning
├── inducer.py      # L4: Logic purification & production grouping
├── compiler.py     # L5: Markdown Skill compilation
└── cli.py          # CLI entry point
```

*Skill Harvester aims for the romance hidden deep within cyberpunk—letting workers forge their own "automated digital clones", so they never have to be mechanical appendages in boring tasks.*
