
# 🚀 Project Limelight: Stealth AI Meeting Co-Pilot

**Hackathon Differentiation Build (12-Hour Sprint)**

> *A floating, context-aware AI assistant that listens, sees, and thinks — silently helping the user win conversations.*

---

## 🧠 Product Vision (Judge-Facing)

**Project Limelight** is a **hovering, always-on AI intelligence layer** that lives *above* any meeting software (Zoom, Meet, Teams).
Unlike dashboards or chatbots, Limelight feels like **Jarvis for sales conversations**.

### Why It Wins

* 🫥 **Stealth Hovering UI** (no context switching)
* ⚡ **Real-time AI hints** (not post-meeting summaries)
* 👀 **Vision + Audio fusion**
* 🧩 **Actionable micro-insights**, not noise

---

## 🪟 UI SYSTEM: Hovering Overlay (Core Differentiator)

### Window Behavior

* Transparent, borderless, always-on-top
* Draggable from any empty area
* Click-through mode toggle (Ctrl + Shift + H)
* Auto-hides when no insight is available

```ui-spec
window:
  type: floating-overlay
  transparency: true
  always_on_top: true
  draggable: true
  click_through_toggle: true
  hide_on_idle: 5s
```

---

## 🎯 Layout Structure

```
┌─────────────────────────────┐
│  🔴 LIVE  |  Speaker: Client │
├─────────────────────────────┤
│  💡 AI Insight Card         │
│  “Mention pricing only     │
│   after feature validation”│
│                             │
│  Confidence: ████████░░ 82% │
├─────────────────────────────┤
│ ⭐ Save   ⚔ Battlecard  ❌ │
└─────────────────────────────┘
```

---

## 💡 Insight Card (Main Attention Hook)

### Behavior

* Slides in from right
* Soft glow pulse when new insight arrives
* Auto-expires unless starred

```ui-component
InsightCard:
  animation: slide-in-right
  glow_on_new: true
  auto_expire: 12s
```

### Insight Types (Color-Coded)

| Type        | Color  | Icon |
| ----------- | ------ | ---- |
| Objection   | Red    | ⚠    |
| Opportunity | Green  | 💰   |
| Strategy    | Blue   | 🧠   |
| Risk        | Orange | 🔥   |

---

## 🧠 AI Confidence Meter (Judge Candy 🍬)

> Judges LOVE visible “thinking”

```ui-component
ConfidenceBar:
  label: "AI Confidence"
  range: 0-100
  animate_on_update: true
```

---

## ⭐ Star Hint → CRM Sync (Instant Value)

### Interaction

* One-click ⭐
* Toast: “Saved & synced to CRM”
* Visual confirmation animation

```ui-action
onStarClick:
  save_to: local_db.starred_hints
  async_sync: odoo_crm
  feedback: toast + pulse
```

---

## ⚔ Battlecard Peek (Competitive Edge)

### Hover Action

* Shows competitor-specific talking points
* Expands on hover, collapses automatically

```ui-component
BattlecardPeek:
  trigger: hover
  expand_direction: left
  auto_collapse: true
```

---

## 👀 Vision Awareness Indicator (Unique Differentiator)

Small floating eye icon 👁

**States**

* 👁 Grey → No screen change
* 👁 Blue → New slide detected
* 👁 Green → Key entity recognized (Pricing, Competitor, Feature)

```ui-component
VisionIndicator:
  source: GeminiVision
  react_to: screen_context_change
```

---

## 🔊 Speaker Intelligence Strip

```ui-component
SpeakerBar:
  show_current_speaker: true
  confidence_level: diarization_score
```

Displays:

* “Client speaking”
* “You are speaking too much” (soft warning)

---

## 🎮 Demo Mode Toggle (Hackathon Safety Net)

```ui-toggle
DemoMode:
  label: "Demo Simulation"
  source: demo_transcript.txt
```

> Allows flawless demos even without live audio.

---

## ⚡ Keyboard Shortcuts (Power-User Feel)

| Shortcut         | Action            |
| ---------------- | ----------------- |
| Ctrl + Shift + H | Toggle visibility |
| Ctrl + Shift + S | Star insight      |
| Ctrl + Shift + B | Show battlecard   |
| Ctrl + Shift + D | Demo mode         |

---

## 🏁 Judge WOW Moments (Call These Out Verbally)

1. “This UI never steals focus — it *assists silently*”
2. “Insights are contextual, not scripted”
3. “Everything you star is already in CRM”
4. “This replaces sticky notes, not dashboards”

---

## 🛠 Build Priority (12-Hour Reality Plan)

### Hour 0-3

* Hovering overlay
* Insight card animation
* Dummy data feed

### Hour 3-6

* Star interaction
* Confidence bar
* Vision indicator

### Hour 6-9

* Battlecard peek
* Demo mode polish

### Hour 9-12

* Motion tuning
* Visual consistency
* Rehearse demo narrative

---

## 🎤 Final Line for Judges (Use This)

> “Everyone else built AI that *analyzes meetings*.
> We built AI that **shows up inside the meeting**.”

---
