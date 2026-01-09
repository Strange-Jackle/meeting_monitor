

# AI Sales Pilot: Hackathon Enhancement Plan

## 1. The "Winner" Vision: The Glass HUD

Instead of a clunky window, we are building a **Floating Glass HUD**.

* **Differentiating Feature:** "Confidence Meter" and "Real-time Objection Handling" cards that slide out from the side of the screen based on Gemini's analysis.
* **UI Style:** Dark mode, 80% opacity, neon accents (cyberpunk aesthetic), and non-intrusive placement.

## 2. Project Structure Update

The IDE should ensure the following files are updated/created:

```text
app/
├── ui/
│   ├── glass_overlay.py       # The new High-End UI
│   └── components/
│       ├── confidence_bar.py  # Visual feedback for the rep
│       └── battlecard_pop.py  # Slide-in alerts for competitors
└── modules/
    └── intelligence/
        └── analysis_engine.py # Extracts "Intent" from WhisperX stream

```

---

## 3. Implementation Code: The Floating Glass UI

Copy this into `app/ui/glass_overlay.py`. This uses **PyQt6** with `WindowStaysOnTopHint` and `FramelessWindowHint`.

```python
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QPalette, QFont

class SalesPilotHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 1. Window Flag Setup: Transparent, Always on Top, No Taskbar Icon
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 2. Layout & Styling
        self.layout = QVBoxLayout()
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 35, 200);
                border: 2px solid #4facfe;
                border-radius: 15px;
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            .hint-text {
                color: #00f2fe;
                font-size: 14px;
                font-style: italic;
            }
        """)

        # 3. UI Components
        self.title_label = QLabel("LIVE SALES PILOT")
        self.title_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        
        self.transcript_preview = QLabel("Listening for cues...")
        self.transcript_preview.setWordWrap(True)
        
        self.hint_box = QLabel("Waiting for competitor mention...")
        self.hint_box.setObjectName("hint-text")
        
        # Confidence Meter (Differentiator)
        self.conf_label = QLabel("Closing Probability: 65%")
        self.progress = QProgressBar()
        self.progress.setValue(65)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #00f2fe; }")

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.transcript_preview)
        self.layout.addWidget(self.hint_box)
        self.layout.addWidget(self.conf_label)
        self.layout.addWidget(self.progress)
        
        self.setLayout(self.layout)
        self.setGeometry(100, 100, 350, 200) # Floating at top right
        
    def update_data(self, transcript, hint, confidence):
        """Method to be called by the WebSocket thread"""
        self.transcript_preview.setText(f"Recent: {transcript[-50:]}...")
        if hint:
            self.hint_box.setText(f"💡 {hint}")
        self.progress.setValue(confidence)
        self.conf_label.setText(f"Closing Probability: {confidence}%")

    # Make it draggable even without a title bar
    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = SalesPilotHUD()
    hud.show()
    sys.exit(app.exec())

```

---

## 4. Feature Differentiator: "The Intent Engine"

To win, you need more than just keywords. Update `gemini_service.py` to analyze **Sentiment + Intent** and return a JSON object that the UI can render.

**Logic for Gemini Prompt:**

> "Analyze this transcript. 1. Calculate a 'Closing Probability' (0-100). 2. Identify 'Current Friction' (e.g., Pricing, Trust, Feature Gap). 3. Provide a 'Killer Response' for the salesperson."

---

## 5. Execution Steps for the Next 12 Hours

1. **Hours 1-3 (UI Core):** Replace `overlay.py` with the `SalesPilotHUD` provided above. Ensure it floats and is draggable.
2. **Hours 4-6 (The "Wow" Metric):** Modify your Gemini prompt to calculate a "Closing Confidence" percentage based on the tone of the customer. This is a visual "wow" factor for judges.
3. **Hours 7-9 (Backend Optimization):** Use `WhisperX` in a separate process to ensure the UI doesn't lag. If VRAM is an issue, switch to the `small` model for the demo to ensure 60fps UI smoothness.
4. **Hours 10-12 (Polish):** Add a "Demo Mode" toggle that simulates a perfect sales call if the local audio loopback gets finicky during the live judging.

---
