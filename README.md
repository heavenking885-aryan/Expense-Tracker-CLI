 💰 Expense Tracker CLI

A lightweight, powerful, and user-friendly Command Line Interface (CLI) application to track, manage, and analyze your daily expenses directly from your terminal.

Built with Python and styled with rich terminal formatting, it supports both a guided **Interactive Terminal UI** and high-speed **Direct Command-Line Arguments**.

---

## 📁 Project Structure

```text
expense-tracker/
│
├── README.md             # Documentation and usage guide
├── requirements.txt      # Python dependencies
├── expenses.csv          # Persistent CSV data storage
├── app.py                # Main script (CLI parser & Interactive Menu)
├── tracker.py            # Core business logic & CRUD operations
└── report.py             # Analytics, aggregation & visualization
```

---

## ✨ Features

- **Dual Interaction Modes**:
  - **Interactive Terminal Menu**: Run `python app.py` for a visual step-by-step menu with live budget tracking and instant feedback.
  - **Direct Command-Line Flags**: Execute fast actions directly via subcommands (e.g. `python app.py add ...`).
- **Complete Expense Management (CRUD)**:
  - Add expenses with auto-incrementing IDs, custom or today's date, category tags, and descriptions.
  - View all expenses formatted in responsive ASCII/Rich tables.
  - Update any field (amount, category, description, date) of an existing expense.
  - Delete records safely with confirmation prompts.
- **Search & Filtering**:
  - Filter by text keyword in description or category.
  - Filter by specific category (Food, Groceries, Transport, etc.).
  - Date range filtering (`--start` and `--end` dates).
- **Reports & Visual Analytics**:
  - **Summary Overview**: Total transactions, total expenditure, average expense, and highest spending record.
  - **Category Breakdown**: Percentage shares with visual distribution progress bars.
  - **Monthly Trends**: Aggregate historical expenditures month-by-month.
  - **Top Expenses**: Quickly inspect your highest expenses.
- **Budget Tracking**:
  - Set a monthly budget goal and monitor real-time utilization with alert warnings when approaching or exceeding your limit.
- **Data Exporting**:
  - Export your expenses to CSV or JSON formats at any time.

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.8+** installed on your system.

### 2. Install Dependencies
Clone or navigate to the project directory and install the required packages:

```bash
pip install -r requirements.txt
```

*(Note: `app.py` has built-in graceful fallbacks if `rich` is not installed, ensuring it runs out-of-the-box in any standard Python environment).*

---

## 💻 Usage Guide

### Mode 1: Interactive Terminal Menu
To launch the interactive menu, simply run:

```bash
python app.py
```

You will be greeted with the live status banner and interactive menu options:
```text
=============================================================================
 EXPENSE TRACKER CLI | Current Month (October 2026): $228.89 | Budget: $500.00 (45.8%)
=============================================================================
Menu Options:
  [1] List All Expenses
  [2] Add New Expense
  [3] Update Expense
  [4] Delete Expense
  [5] Search & Filter
  [6] Summary & Category Analytics
  [7] Monthly Trends
  [8] Monthly Budget Manager
  [9] Export Expenses (CSV / JSON)
  [0] Exit
```

---

### Mode 2: Command-Line Flags

#### 1. Add an Expense
```bash
python app.py add -a 25.50 -c Food -d "Lunch at cafe"
python app.py add -a 60.00 -c Transport -d "Train ticket" -t 2026-10-12
```

#### 2. List Expenses
```bash
# List all expenses
python app.py list

# Sort by date (descending)
python app.py list --sort-date --desc

# Filter by category
python app.py list -c Food

# Filter by month and year
python app.py list -m 10 -y 2026
```

#### 3. Update an Expense
```bash
# Update amount and description for ID 2
python app.py update --id 2 -a 50.00 -d "Monthly pass updated"
```

#### 4. Delete an Expense
```bash
python app.py delete --id 4
```

#### 5. Search Expenses
```bash
# Search by keyword
python app.py search -q "lunch"

# Search by category and date range
python app.py search -c Groceries --start 2026-10-01 --end 2026-10-15
```

#### 6. View Summary & Visual Analytics
```bash
# Overall summary & category breakdown
python app.py summary

# Filter summary for a specific month
python app.py summary -m 10 -y 2026
```

#### 7. View Monthly Trends & Top Expenses
```bash
# Monthly trends table
python app.py report --monthly

# Top 5 highest expenses
python app.py report --top 5
```

#### 8. Set and Check Monthly Budget
```bash
# Set monthly budget limit to $500
python app.py budget --set 500

# View current budget status
python app.py budget
```

#### 9. Export Data
```bash
# Export to CSV
python app.py export --format csv -o my_expenses.csv

# Export to JSON
python app.py export --format json -o backup.json
```

---

## 📊 Data Storage Format (`expenses.csv`)

Expenses are persisted in `expenses.csv` with the following structure:

| Header | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Unique auto-incrementing ID |
| `date` | String | Format `YYYY-MM-DD` |
| `amount` | Float | Cost formatted to 2 decimal places |
| `category` | String | Categorization (e.g. Food, Groceries, Transport) |
| `description` | String | Note or merchant details |

Sample data:
```csv
id,date,amount,category,description
1,2026-10-01,15.50,Food,Lunch at cafe
2,2026-10-03,45.00,Transport,Monthly bus pass
3,2026-10-05,120.00,Groceries,Weekly grocery run
4,2026-10-08,12.99,Entertainment,Movie ticket
5,2026-10-10,35.40,Utilities,Internet bill share
```

---

## 🛠️ Module Architecture

- **[tracker.py](tracker.py)**: Contains the `Expense` dataclass and the `ExpenseTracker` management class. Manages data validation (positive amounts, valid date strings), CSV read/write locks, ID assignment, and queries.
- **[report.py](report.py)**: Contains pure analytics and aggregation helpers for computing category percentages, monthly spending trends, budget metrics, and progress bars.
- **[app.py](app.py)**: Orchestrates CLI execution, argparse subcommands, interactive menu prompts, and terminal rendering.
