"""
report.py - Reporting and Analytics functions for Expense Tracker
Computes aggregations, breakdowns by category and month, budget progress,
and terminal visualization widgets.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

from tracker import Expense


def calculate_summary(expenses: List[Expense]) -> Dict[str, Any]:
    """Calculate overall statistics for a given list of expenses."""
    if not expenses:
        return {
            "count": 0,
            "total_spent": 0.0,
            "average": 0.0,
            "min_expense": None,
            "max_expense": None,
        }

    total_spent = sum(e.amount for e in expenses)
    count = len(expenses)
    avg = total_spent / count if count > 0 else 0.0
    min_exp = min(expenses, key=lambda e: e.amount)
    max_exp = max(expenses, key=lambda e: e.amount)

    return {
        "count": count,
        "total_spent": round(total_spent, 2),
        "average": round(avg, 2),
        "min_expense": min_exp,
        "max_expense": max_exp,
    }


def category_breakdown(expenses: List[Expense]) -> List[Dict[str, Any]]:
    """Group expenses by category with total, count, average, and percentage share."""
    if not expenses:
        return []

    cat_totals: Dict[str, float] = defaultdict(float)
    cat_counts: Dict[str, int] = defaultdict(int)
    overall_total = sum(e.amount for e in expenses)

    for exp in expenses:
        cat_totals[exp.category] += exp.amount
        cat_counts[exp.category] += 1

    breakdown = []
    for cat, total in cat_totals.items():
        count = cat_counts[cat]
        pct = (total / overall_total * 100.0) if overall_total > 0 else 0.0
        breakdown.append({
            "category": cat,
            "total": round(total, 2),
            "count": count,
            "average": round(total / count, 2),
            "percentage": round(pct, 1),
        })

    # Sort descending by total amount spent
    breakdown.sort(key=lambda x: x["total"], reverse=True)
    return breakdown


def monthly_breakdown(expenses: List[Expense], target_year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Group expenses by month (YYYY-MM). Optionally filter by a specific year."""
    if not expenses:
        return []

    monthly_map: Dict[str, List[Expense]] = defaultdict(list)
    for exp in expenses:
        try:
            exp_date = datetime.strptime(exp.date, "%Y-%m-%d")
            if target_year is not None and exp_date.year != target_year:
                continue
            month_key = exp_date.strftime("%Y-%m")
            monthly_map[month_key].append(exp)
        except ValueError:
            continue

    result = []
    for m_key in sorted(monthly_map.keys(), reverse=True):
        items = monthly_map[m_key]
        m_total = sum(i.amount for i in items)
        result.append({
            "month": m_key,
            "total": round(m_total, 2),
            "count": len(items),
            "average": round(m_total / len(items), 2),
        })

    return result


def filter_by_month(expenses: List[Expense], month: int, year: int) -> List[Expense]:
    """Return all expenses matching the given month (1-12) and year."""
    filtered = []
    for exp in expenses:
        try:
            dt = datetime.strptime(exp.date, "%Y-%m-%d")
            if dt.month == month and dt.year == year:
                filtered.append(exp)
        except ValueError:
            continue
    return filtered


def filter_by_year(expenses: List[Expense], year: int) -> List[Expense]:
    """Return all expenses matching the given year."""
    filtered = []
    for exp in expenses:
        try:
            dt = datetime.strptime(exp.date, "%Y-%m-%d")
            if dt.year == year:
                filtered.append(exp)
        except ValueError:
            continue
    return filtered


def generate_ascii_bar(percentage: float, width: int = 15) -> str:
    """Generate an ASCII progress bar for terminal visualization."""
    clamped_pct = max(0.0, min(100.0, percentage))
    filled_len = int(round(width * clamped_pct / 100.0))
    bar = "#" * filled_len + "-" * (width - filled_len)
    return f"|{bar}|"


def check_budget_status(current_spent: float, monthly_budget: Optional[float]) -> Dict[str, Any]:
    """Calculate budget usage and status flags."""
    if monthly_budget is None or monthly_budget <= 0:
        return {
            "has_budget": False,
            "monthly_budget": None,
            "spent": round(current_spent, 2),
            "remaining": None,
            "percentage": None,
            "is_over_budget": False,
        }

    remaining = monthly_budget - current_spent
    pct = (current_spent / monthly_budget) * 100.0
    is_over = current_spent > monthly_budget

    return {
        "has_budget": True,
        "monthly_budget": round(monthly_budget, 2),
        "spent": round(current_spent, 2),
        "remaining": round(remaining, 2),
        "percentage": round(pct, 1),
        "is_over_budget": is_over,
    }


def get_top_expenses(expenses: List[Expense], limit: int = 5) -> List[Expense]:
    """Return the top N most expensive expenses."""
    sorted_expenses = sorted(expenses, key=lambda e: e.amount, reverse=True)
    return sorted_expenses[:limit]
