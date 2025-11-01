# ⚾ BaseballBinder

**Your Digital Baseball Card Collection Manager**

BaseballBinder is a modern, web-based application designed to help baseball card collectors organize, track, and manage their collections with ease. Import checklists, track values, and search your collection—all in one beautiful interface.

---

## ✨ Features

- **📤 CSV Checklist Import** - Upload multiple checklist CSV files by year to build your reference database
- **➕ Easy Card Entry** - Add cards to your collection with auto-fill from imported checklists
- **🔍 Smart Search** - Search your collection with auto-suggest player names and instant filtering
- **📊 Collection Stats** - Track total cards, current value, and profit/loss in real-time
- **🎴 Variety & Parallel Support** - Track different card varieties, parallels, numbered cards, and autographs
- **💰 Value Tracking** - Monitor purchase prices, current values, and sold prices
- **📍 Location Management** - Keep track of where your cards are stored (binders, boxes, etc.)
- **🎨 Modern UI** - Clean, professional interface with smooth animations and responsive design
- **☕ Free & Open Source** - Community-driven development

---

## 📸 Screenshots

<!-- Add your screenshots here -->
_Coming soon! Screenshots of the app in action._

---

## 🚀 Installation

### Prerequisites

- **Python 3.10 or higher**
- pip (Python package manager)

### Steps

1. **Clone the repository** (or download the ZIP)
   ```bash
   git clone https://github.com/yourusername/baseballbinder.git
   cd baseballbinder
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the app**
   Open your web browser and navigate to:
   ```
   http://localhost:8000/index.html
   ```

---

## 📖 Usage

### Importing Checklists

1. Navigate to the **Import Checklists** page
2. Enter the year for your checklists
3. Select one or more CSV files (named after the set, e.g., `Topps-Chrome.csv`)
4. Click **Upload Checklists**

**CSV Format:**
```csv
Variety,Card Number,Player/Athlete,Team,Rookie,Parallel
Base,1,Mike Trout,Angels,No,
Refractor,1,Mike Trout,Angels,No,Blue /150
```

### Adding Cards

1. Go to the **Add Cards** page
2. Select a set from the dropdown (populated from imported checklists)
3. Enter the card number
4. Click **Auto-Fill from Checklist** to populate player data
5. Select variety and parallel if applicable
6. Fill in pricing, grading, and location details
7. Click **Add Card**

### Viewing Your Collection

1. Navigate to **View Collection**
2. Use the search bar to find specific players or sets
3. Click on player suggestions for instant filtering
4. View all your cards in a sortable table
5. Delete cards as needed

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLAlchemy with SQLite
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Design:** Modern gradient UI with responsive layout

---

## 📁 Project Structure

```
card-collection/
├── main.py                      # FastAPI application entry point
├── models.py                    # Database models for cards
├── checklist_models.py          # Database models for checklists
├── checklist_api.py             # API endpoints for checklist operations
├── index.html                   # Main frontend application
├── BaseballBinderLogo.png       # Main logo
├── BaseballBinder_thumbnail.png # Thumbnail logo
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve BaseballBinder:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ☕ Support the Project

If you find BaseballBinder helpful, consider supporting its development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/baseballbinder)

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 BaseballBinder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📧 Contact

- **Project Website:** [BaseballBinder](https://buymeacoffee.com/baseballbinder)
- **Issues:** [GitHub Issues](https://github.com/yourusername/baseballbinder/issues)
- **Email:** [your.email@example.com](mailto:your.email@example.com)

---

## 🙏 Acknowledgments

- Built with ❤️ for the baseball card collecting community
- Icons and emojis for visual enhancement
- FastAPI for the powerful backend framework
- All contributors and supporters

---

**⚾ Happy Collecting with BaseballBinder! 🎴**
