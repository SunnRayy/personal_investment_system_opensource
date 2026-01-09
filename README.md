# Personal Investment System

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docs.docker.com/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**The AI-Native, Privacy-First Portfolio Intelligence Platform.**

[Features](#-why-this-project) • [Quick Start](#-quick-start) • [Docker](#-docker-deployment) • [Architecture](#-architecture)

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

## 🐳 Docker Deployment

**Zero-configuration deployment** - get started in seconds:

```bash
# Clone and run
git clone https://github.com/yourusername/personal_investment_system.git
cd personal_investment_system
docker-compose up -d
```

Open `http://localhost:5000` and explore with demo data or upload your own.

See [docs/docker.md](docs/docker.md) for configuration, troubleshooting, and best practices.

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

## 🔌 API Integrations

Connect your accounts for automated sync (optional):

| Integration | Status | Notes |
| :--- | :---: | :--- |
| **Crypto Exchanges** | ✅ Ready | Binance, Coinbase, Kraken via CCXT |
| **Interactive Brokers** | ✅ Ready | Client Portal API |
| **Schwab** | 🔧 Planned | OAuth2 integration |
| **Custom Plugins** | ✅ Ready | Extensible plugin system |

See `config/data_sources.yaml` and `docs/automated-integrations/` for setup guides.

---

## 🛠️ Configuration

| File | Purpose |
| :--- | :--- |
| `config/settings.yaml` | Data paths, FX rates, risk parameters |
| `config/asset_taxonomy.yaml` | Custom asset class hierarchy |
| `config/data_sources.yaml` | API integrations configuration |
| `.env` | Secrets and API keys (gitignored) |

---

## 🤝 Contributing & License

**Vibe Coding Friendly.** Feel free to fork and let your AI agent add features.
Licensed under **MIT**.

---
<div align="center">
  <sub>Built with ❤️ by Independent Developers for Financial Sovereignty.</sub>
</div>
