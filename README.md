# Personal Investment System

<div align="center">

![Project Banner](https://via.placeholder.com/1200x300.png?text=Personal+Investment+System+Dashboard)
<!-- Replace with actual dashboard screenshot in Visual Showcase -->

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Vibe Coding](https://img.shields.io/badge/Vibe-Coding-purple.svg)](https://github.com/topics/vibe-coding)

**The AI-Native, Privacy-First Portfolio Intelligence Platform.**

[Features](#features) • [Quick Start](#quick-start) • [Showcase](#visual-showcase) • [Architecture](#architecture)

</div>

---

## 🚀 Why This Project?

Traditional finance tools force a tradeoff: surrender your privacy to cloud apps, or suffer in spreadsheet hell. **Personal Investment System** breaks this dichotomy. It is an open-source, locally-run engine designed for the **Vibe Coding** era—where logic is transparent, data is yours, and analysis is professional-grade.

### Core Pillars

|  |  |
| :--- | :--- |
| **🧠 AI-Driven Logic** | Built for **Vibe Coding**. The codebase is modular, typed, and documented to be easily read and modified by LLMs. Logic is transparent—no black boxes. |
| **🔒 Privacy First** | **Local Execution.** Your financial data never leaves your machine. No cloud sync, no tracking, no third-party APIs unless you configure them. |
| **📊 Sophisticated Analysis** | **Wall Street Grade.** Native support for Modern Portfolio Theory (MPT), Market Thermometers, and Hierarchical Asset Classification. |

---

## 🏎️ 5-Minute Quick Start

Go from zero to full dashboard with realistic demo data in 3 steps.

**1. Clone & Install**

```bash
git clone https://github.com/yourusername/personal_investment_system.git
cd personal_investment_system
pip install -r requirements.txt
```

**2. Generate Intelligence**
Create a full localized dataset (Holdings, Transactions, Cash Flow) instantly.

```bash
python scripts/generate_demo_data.py --seed 42
```

**3. Launch Control Center**

```bash
python -m flask --app src.web_app.app run
```

> Explore your new dashboard at `http://localhost:5000`

---

## 🆚 Feature Matrix

| Feature | Personal Investment System | Commercial App (Mint/Empower) | Excel / Spreadsheet |
| :--- | :---: | :---: | :---: |
| **Data Privacy** | 🔒 **100% Local** | ❌ Cloud Hosted | ⚠️ Local but Fragile |
| **Analytics Engine** | 📈 **SciPy / Pandas** | ❓ Proprietary Black Box | ➗ Formulas |
| **Portfolio Theory** | ✅ **MPT Efficient Frontier** | ❌ Basic Allocation | ❌ Hard Plugin |
| **Coding Interface** | 🤖 **AI-Native (Vibe Coding)** | ❌ Closed Source | ❌ VBA Macros |
| **Asset Class Model** | 🏷️ **Multi-Tier Hierarchical** | ⚠️ Flat Categories | ⚠️ Manual Tagging |
| **Cost** | 💸 **Free Open Source** | 💸 Subscription / Data Mining | 💸 License Fees |

---

## 🎨 Visual Showcase

> *The system transforms raw data into actionable strategic insights.*

<div align="center">
  <img src="https://via.placeholder.com/800x450.png?text=Dashboard+Overview" alt="Dashboard Overview" width="800" />
  <p><em>Real-time Net Worth & Allocation Tracking</em></p>
  
  <br/>

  <img src="https://via.placeholder.com/800x450.png?text=Efficient+Frontier+Matrix" alt="MPT Analysis" width="800" />
  <p><em>Modern Portfolio Theory: Efficient Frontier Optimization</em></p>
</div>

---

## 🏗️ Architecture

Engineered for extensibility. The system follows a clean separation of concerns, making it the perfect playground for AI-assisted development.

```mermaid
graph TD
    A[Data Sources] -->|Excel/CSV/API| B(Data Manager)
    B --> C{Core Engine}
    C -->|Stats| D[Financial Analysis]
    C -->|Optimization| E[Portfolio Lib (MPT)]
    C -->|Logic| F[Recommendation Engine]
    D --> G[Web Dashboard]
    E --> G
    F --> G
    G --> H[User Interface]
```

- **Data Layer**: Robust ETL pipelines handling various formats and currencies (USD/CNY).
- **Core Engine**: `scipy` for optimization, `pandas` for aggregation.
- **Web Layer**: Lightweight Flask app serving responsive, beautiful analytics.

---

## 🛠️ Advanced Configuration

Fine-tune the system to your exact financial DNA.

- **`config/settings.yaml`**: Control risk parameters, FX rates, and data paths.
- **`config/asset_taxonomy.yaml`**: Define your custom asset class hierarchy.

## 🤝 Contributing & License

**Vibe Coding Friendly.** Feel free to fork and let your AI agent add features.
Licensed under **MIT**.

---
<div align="center">
  <sub>Built with ❤️ by Independent Developers for Financial Sovereignty.</sub>
</div>
