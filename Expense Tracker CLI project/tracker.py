"""
tracker.py - Core logic for Expense Tracker
Handles expense data models, CSV file persistence, and CRUD operations.
"""

from __future__ import annotations
import csv
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional


@dataclass
class Expense:
    """Represents a single expense record."""
    id: int
    date: str
    amount: float
    category: str
    description: str

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "date": self.date,
            "amount": f"{self.amount:.2f}",
            "category": self.category,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Expense:
        return cls(
            id=int(data["id"]),
            date=data["date"],
            amount=float(data["amount"]),
            category=data["category"].strip(),
            description=data["description"].strip(),
        )


class ExpenseTracker:
    """Manages reading, writing, and querying expense records."""

    DEFAULT_CATEGORIES = [
        "Food",
        "Groceries",
        "Transport",
        "Utilities",
        "Entertainment",
        "Shopping",
        "Health",
        "Travel",
        "Education",
        "Other",
    ]

    FIELDNAMES = ["id", "date", "amount", "category", "description"]

    def __init__(self, filepath: str = "expenses.csv", config_path: str = "config.json"):
        self.filepath = filepath
        self.config_path = config_path
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Create the CSV file with headers if it does not already exist."""
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def load_expenses(self) -> List[Expense]:
        """Load all expenses from the CSV file."""
        self._ensure_storage_exists()
        expenses: List[Expense] = []
        with open(self.filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row or not row.get("id"):
                    continue
                try:
                    expenses.append(Expense.from_dict(row))
                except (ValueError, KeyError):
                    # Skip malformed lines gracefully
                    continue
        return expenses

    def save_expenses(self, expenses: List[Expense]) -> None:
        """Write all expenses to the CSV file safely."""
        temp_file = f"{self.filepath}.tmp"
        with open(temp_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            for exp in expenses:
                writer.writerow(exp.to_dict())
        os.replace(temp_file, self.filepath)

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate and return normalized YYYY-MM-DD date string."""
        date_str = date_str.strip()
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{date_str}'. Please use YYYY-MM-DD.")

    @staticmethod
    def validate_amount(amount_input: float | str) -> float:
        """Validate that amount is a positive number."""
        try:
            val = float(amount_input)
            if val <= 0:
                raise ValueError("Amount must be greater than zero.")
            return round(val, 2)
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid amount '{amount_input}'. Must be a positive number.") from err

    def _get_next_id(self, expenses: List[Expense]) -> int:
        """Generate the next sequential ID."""
        if not expenses:
            return 1
        return max(exp.id for exp in expenses) + 1

    def add_expense(
        self,
        amount: float | str,
        category: str,
        description: str,
        date: Optional[str] = None,
    ) -> Expense:
        """Add a new expense record."""
        valid_amount = self.validate_amount(amount)
        valid_date = self.validate_date(date) if date else datetime.now().strftime("%Y-%m-%d")
        category_clean = category.strip().capitalize() if category else "Other"
        desc_clean = description.strip() if description else "N/A"

        expenses = self.load_expenses()
        new_id = self._get_next_id(expenses)

        new_expense = Expense(
            id=new_id,
            date=valid_date,
            amount=valid_amount,
            category=category_clean,
            description=desc_clean,
        )

        expenses.append(new_expense)
        self.save_expenses(expenses)
        return new_expense

    def get_all_expenses(self, sort_by_date: bool = False, reverse: bool = False) -> List[Expense]:
        """Retrieve all expenses with optional sorting."""
        expenses = self.load_expenses()
        if sort_by_date:
            expenses.sort(key=lambda x: x.date, reverse=reverse)
        return expenses

    def get_expense_by_id(self, expense_id: int) -> Optional[Expense]:
        """Find an expense by its unique ID."""
        expenses = self.load_expenses()
        for exp in expenses:
            if exp.id == expense_id:
                return exp
        return None

    def update_expense(
        self,
        expense_id: int,
        amount: Optional[float | str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Optional[Expense]:
        """Update fields of an existing expense."""
        expenses = self.load_expenses()
        target: Optional[Expense] = None

        for exp in expenses:
            if exp.id == expense_id:
                if amount is not None:
                    exp.amount = self.validate_amount(amount)
                if category is not None and category.strip():
                    exp.category = category.strip().capitalize()
                if description is not None and description.strip():
                    exp.description = description.strip()
                if date is not None:
                    exp.date = self.validate_date(date)
                target = exp
                break

        if target:
            self.save_expenses(expenses)
        return target

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense by ID. Returns True if deleted, False if not found."""
        expenses = self.load_expenses()
        initial_len = len(expenses)
        expenses = [exp for exp in expenses if exp.id != expense_id]

        if len(expenses) < initial_len:
            self.save_expenses(expenses)
            return True
        return False

    def search_expenses(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Expense]:
        """Search and filter expenses by query keywords, category, or date range."""
        results = self.load_expenses()

        if keyword:
            kw = keyword.lower().strip()
            results = [
                exp for exp in results
                if kw in exp.description.lower() or kw in exp.category.lower()
            ]

        if category:
            cat = category.lower().strip()
            results = [exp for exp in results if exp.category.lower() == cat]

        if start_date:
            s_date = self.validate_date(start_date)
            results = [exp for exp in results if exp.date >= s_date]

        if end_date:
            e_date = self.validate_date(end_date)
            results = [exp for exp in results if exp.date <= e_date]

        return results

    def get_categories(self) -> List[str]:
        """Return combined unique categories from history and default suggestions."""
        expenses = self.load_expenses()
        used_categories = {exp.category for exp in expenses if exp.category}
        all_cats = list(dict.fromkeys(list(used_categories) + self.DEFAULT_CATEGORIES))
        return sorted(all_cats)

    # --- Budget Management ---
    def get_monthly_budget(self) -> Optional[float]:
        """Fetch the monthly budget from configuration file if set."""
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("monthly_budget")
        except Exception:
            return None

    def set_monthly_budget(self, budget: float) -> float:
        """Save a new monthly budget limit."""
        val = self.validate_amount(budget)
        data = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["monthly_budget"] = val
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return val
