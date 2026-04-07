# Skill Harvester 

[English](README.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

## Kernphilosophie: Der Mensch ist Zweck, niemals nur Mittel. - Kant ## 
> Der Ausgangspunkt des Systems ist es, Menschen von der kognitiven Last monotoner Arbeit zu befreien. Indem automatisierbare, implizite Regeln an einen Agenten übergeben werden, wird der Mensch von repetitiven Abläufen befreit, um sich voll und ganz auf kreative Tätigkeiten konzentrieren zu können.

## Theoretisches Fundament & Designphilosophie: Was ist ein "Skill"?

Aus Sicht der Logik und der Kognitionswissenschaft beschreibt ein "Skill" (Fähigkeit) dasselbe Kernphänomen: die Komprimierung expliziten Wissens in ein automatisches Programm. Um dies verständlicher zu machen, verwenden wir Analogien (Feynman-Methode):

1. **Logische Perspektive (Aus "Muskelgedächtnis" wird ein "Handbuch")**
   Gilbert Ryle unterscheidet zwischen "Knowing That" (Aussagenwissen) und "Knowing How" (Prozedurales Wissen). Ein Skill ist der Träger von Letzterem.
   **Analogie: Sie wissen, wie man Fahrrad fährt (Knowing How/Muskelgedächtnis), aber Sie könnten kaum eine Anleitung schreiben, wie man es jemand anderem beibringt (Knowing That/Handbuch).** Viele wiederholte Aufgaben werden zu diesem Muskelgedächtnis. Unsere Aufgabe ist es, dieses "Muskelgedächtnis" durch Dialoge wieder in ein "Regelhandbuch" zu entflechten, das die Maschine versteht.

2. **Kognitionswissenschaftliche Perspektive (Analytik der "Intuition")**
   In der ACT-R-Theorie ist dies der Prozess der "Wissenskompilierung" (Knowledge Compilation) – durch lange Praxis werden Regeln verinnerlicht, und Experten können oft "nicht erklären, warum" (Tacit Knowledge).
   **Analogie: Wie wenn man Fahren lernt: Zuerst denkt man "Kupplung treten, dann schalten". Aber ein erfahrener Fahrer bremst im Notfall sofort; fragt man warum, sagt er nur "Intuition".** Im Arbeitsalltag sind Sie zu diesem "Routinier" geworden, und das System holt diese Intuitionen an die Oberfläche.

3. **"Event-Aufzeichnung" vs. "Logische Kompilierung": Warum nicht aufzeichnen?**
   Traditionelle RPA ist ein "Event-Recorder", während dieses System "Produktionen" (IF-THEN-Logikregeln) generiert.
   **Analogie: Eine Bildschirmaufzeichnung ist wie eine Kamera; sie erfasst nur "Sie haben Taste A gedrückt" – das sind Ereignisse. Wenn sich die Tastatur verschiebt, ist sie blind. Eine Produktion hingegen ist wie ein Kochrezept: Es sagt "WENN das Wasser kocht, DANN schalte den Herd aus".** Wir wollen Ihre Bewegungen nicht auswendig lernen, sondern verstehen, "unter welchen Umständen Sie sich entscheiden".

4. **Befreiung von digitaler Entfremdung**
   Traditionelle RPA beobachtet nur den redundanten Klickstrom. Skill Harvester baut Ihren persönlichen digitalen Co-Piloten auf. Die langweiligen Aspekte Ihrer Arbeit werden als "kognitives Exoskelett" an die Maschine übergeben, damit Sie sich auf unersetzliche Aufgaben fokussieren können.

## Kerndesign und Ockhams Rasiermesser

Menschliche Arbeitsabläufe sind durchsetzt mit einer Unmenge an bedeutungslosen Aktionen. Wie findet das System effektive Entscheidungen?

1. **Information = Überraschung (Surprisal)**
   **Analogie: Genau wie Sie normalerweise das Summen Ihres Kühlschranks nicht hören, es aber sofort bemerken, wenn er aufhört.** Alltägliche Operationen sind "weißes Rauschen" und werden nicht aufgezeichnet. Das System wacht nur auf, wenn ein "Unfall" passiert.

2. **Fokus auf "Goldene Momente"**
   Wir erfassen nur Momente mit abnormalen Schwankungen: **langes Pausieren, Rückgängigmachen (Ctrl+Z), häufiges Wechseln von Fenstern**. Dies sind die Momente, in denen implizites Wissen an die Oberfläche kommt.

3. **Externalisierung impliziten Wissens (Cognitive Task Analysis)**
   Nachdem diese Momente erfasst wurden, stellt das System an einem natürlichen Ruhepunkt eine kurze Frage: "Sie haben hier 5 Sekunden gezögert. Haben Sie diesen Betrag verglichen?" — Mit nur diesem einen Satz wird Ihre Erfahrung in Code verpackt.

## Fünf-Ebenen-Systemarchitektur

Das System umfasst 5 Kompressionsmechanismen:

1. **L0 Task Catalog**: Liefert die Vorab-Absicht. *(Analogie: Die Liste der Dinge, die Sie heute erledigen wollen)*
2. **L1 Sparse Sensor**: Überwacht den Event-Stream. *(Analogie: Keine Videoaufzeichnung, nur ein Stethoskop für App-Wechsel)*
3. **L2 Episode Builder**: Speichert einen "Episoden"-Schnappschuss bei Vorhersagefehlern. *(Analogie: Bemerkt, dass Sie feststecken, und macht einen Screenshot der letzten 30 Sekunden)*
4. **L3 Dialogue Engine**: Initiiert Fragen. *(Analogie: Stellt Ihnen passend zum Schnappschuss eine Multiple-Choice-Frage)*
5. **L4 Production Inducer**: Extrahiert IF-THEN-Logiken. *(Analogie: Vergleicht Ihr Zögern gestern mit dem heute, um die Regel abzuleiten)*
6. **L5 Skill Compiler**: Übersetzt Ergebnisse in ein `.md`-Skript. *(Analogie: Schreibt das Handbuch für den Roboter)*

*(Design-Dokumente [v1](./skill-harvester-design.md) und [v2](./skill-harvester-design-v2.md) sind auf Chinesisch verfügbar)*

## Running: Phase 1 MVP

Dieses Repository befindet sich in der Phase-1-Prototyp-Phase (L3→L4→L5 Pipeline Validierung).

### Quick Start

```bash
# 1. Installieren
pip install -e .

# 2. Task List vorbereiten
cp examples/task_list.example.yaml ~/.skill-harvester/task_list.yaml
# Bearbeiten Sie task_list.yaml

# 3. Phase 0 Erkennung starten
skill-harvester capture
# Drücken Sie Ctrl+Alt+M für einen abzuspeichernden Moment

# 4. Fragen abends beantworten
skill-harvester review

# 5. Induktion der Regeln
skill-harvester induce

# 6. Kompilieren zu SKILL.md
skill-harvester compile
```

### Projektstruktur

```
skill_harvester/
├── models.py       # Daten: TaskCatalog, Episode, Production
├── storage.py      # Speicher
├── llm.py          # LLM Backend
├── capture.py      # L1/L2
├── classifier.py   # L3 step 1
├── dialogue.py     # L3 step 2
├── inducer.py      # L4
├── compiler.py     # L5
└── cli.py          # CLI
```

*Skill Harvester zielt auf die Romantik tief im Cyberpunk ab—Arbeiter schmieden ihre eigenen „automatisierten digitalen Klone“, um nie ein mechanisches Anhängsel langweiliger Aufgaben zu sein.*
