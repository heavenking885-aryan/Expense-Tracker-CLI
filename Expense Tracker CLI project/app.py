"""
app.py - Main entry point for Expense Tracker CLI
Provides both an interactive visual menu and direct CLI command-line flags.
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

# Ensure UTF-8 output on Windows consoles to prevent charmap encoding errors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.markup import escape
    from rich import box
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    escape = lambda x: x

from tracker import Expense, ExpenseTracker
from report import (
    calculate_summary,
    category_breakdown,
    monthly_breakdown,
    filter_by_month,
    generate_ascii_bar,
    check_budget_status,
    get_top_expenses,
)


tracker = ExpenseTracker("expenses.csv")


# ==============================================================================
# Helper Formatting and Display Functions
# ==============================================================================

def print_message(text: str, status: str = "info") -> None:
    """Print formatted status messages with color styling."""
    prefix_map = {
        "success": ("[+]", "green"),
        "error": ("[!]", "red"),
        "warning": ("[*]", "yellow"),
        "info": ("[i]", "cyan"),
    }
    symbol, color = prefix_map.get(status, ("[*]", "white"))

    if RICH_AVAILABLE:
        console.print(f"[{color}][bold]{symbol}[/bold] {text}[/{color}]")
    else:
        print(f"{symbol} {text}")


def display_expense_table(expenses: List[Expense], title: str = "Expenses") -> None:
    """Render a formatted table of expenses."""
    if not expenses:
        print_message("No expenses found matching the criteria.", "warning")
        return

    if RICH_AVAILABLE:
        table = Table(title=title, box=box.ROUNDED, header_style="bold cyan")
        table.add_column("ID", justify="center", style="bold yellow", width=6)
        table.add_column("Date", justify="center", style="blue", width=12)
        table.add_column("Category", justify="left", style="magenta", width=15)
        table.add_column("Amount ($)", justify="right", style="green bold", width=12)
        table.add_column("Description", justify="left", style="white")

        for exp in expenses:
            table.add_row(
                str(exp.id),
                exp.date,
                exp.category,
                f"${exp.amount:,.2f}",
                exp.description,
            )

        console.print(table)
    else:
        print(f"\n=== {title} ===")
        print(f"{'ID':<6} {'Date':<12} {'Category':<15} {'Amount ($)':>12} {'Description'}")
        print("-" * 65)
        for exp in expenses:
            print(f"{exp.id:<6} {exp.date:<12} {exp.category:<15} {exp.amount:>12.2f} {exp.description}")
        print("-" * 65)


def display_summary_report(expenses: List[Expense], month_label: Optional[str] = None) -> None:
    """Display comprehensive summary cards and category distributions."""
    summary = calculate_summary(expenses)
    categories = category_breakdown(expenses)
    budget = tracker.get_monthly_budget()
    budget_info = check_budget_status(summary["total_spent"], budget)

    title_suffix = f" ({month_label})" if month_label else " (All Time)"

    if RICH_AVAILABLE:
        # Summary Overview Panel
        stats_text = Text()
        stats_text.append(f"Total Transactions: ", style="bold")
        stats_text.append(f"{summary['count']}\n", style="cyan")
        stats_text.append(f"Total Expenditure:  ", style="bold")
        stats_text.append(f"${summary['total_spent']:,.2f}\n", style="green bold")
        stats_text.append(f"Average Expense:    ", style="bold")
        stats_text.append(f"${summary['average']:,.2f}\n", style="yellow")

        if summary['max_expense']:
            stats_text.append(f"Highest Expense:    ", style="bold")
            stats_text.append(
                f"${summary['max_expense'].amount:,.2f} on {summary['max_expense'].category} ('{summary['max_expense'].description}')\n",
                style="red"
            )

        if budget_info["has_budget"]:
            stats_text.append(f"\nMonthly Budget:     ", style="bold")
            stats_text.append(f"${budget_info['monthly_budget']:,.2f}\n", style="magenta")
            stats_text.append(f"Budget Used:        ", style="bold")
            color = "red bold" if budget_info["is_over_budget"] else "green"
            stats_text.append(f"{budget_info['percentage']}% ({generate_ascii_bar(budget_info['percentage'])})\n", style=color)
            if budget_info["is_over_budget"]:
                stats_text.append(f"Status:             OVER BUDGET by ${abs(budget_info['remaining']):,.2f}!\n", style="red bold")
            else:
                stats_text.append(f"Remaining Budget:   ${budget_info['remaining']:,.2f}\n", style="green")

        console.print(Panel(stats_text, title=f"[bold cyan]Spending Overview{title_suffix}[/bold cyan]", box=box.ROUNDED))

        # Category Breakdown Table with Visual Bar
        if categories:
            cat_table = Table(title="Category Breakdown", box=box.ROUNDED, header_style="bold magenta")
            cat_table.add_column("Category", style="cyan bold", width=16)
            cat_table.add_column("Total ($)", justify="right", style="green bold", width=12)
            cat_table.add_column("Count", justify="center", width=8)
            cat_table.add_column("Avg ($)", justify="right", width=10)
            cat_table.add_column("Share", justify="right", style="yellow", width=8)
            cat_table.add_column("Distribution", justify="center", style="blue bold", width=19)

            for cat in categories:
                bar = generate_ascii_bar(cat["percentage"], width=12)
                cat_table.add_row(
                    cat["category"],
                    f"${cat['total']:,.2f}",
                    str(cat["count"]),
                    f"${cat['average']:,.2f}",
                    f"{cat['percentage']}%",
                    escape(bar),
                )
            console.print(cat_table)

    else:
        print(f"\n================ Spending Overview{title_suffix} ================")
        print(f"Total Transactions: {summary['count']}")
        print(f"Total Expenditure:  ${summary['total_spent']:,.2f}")
        print(f"Average Expense:    ${summary['average']:,.2f}")
        if budget_info["has_budget"]:
            print(f"Monthly Budget:     ${budget_info['monthly_budget']:,.2f}")
            print(f"Budget Used:        {budget_info['percentage']}% {generate_ascii_bar(budget_info['percentage'])}")
            if budget_info["is_over_budget"]:
                print(f"WARNING: OVER BUDGET by ${abs(budget_info['remaining']):,.2f}!")
            else:
                print(f"Remaining Budget:   ${budget_info['remaining']:,.2f}")
        print("============================================================\n")

        if categories:
            print(f"{'Category':<16} {'Total ($)':>12} {'Count':>6} {'Share':>8} {'Distribution'}")
            print("-" * 65)
            for cat in categories:
                bar = generate_ascii_bar(cat["percentage"], width=12)
                print(f"{cat['category']:<16} {cat['total']:>12.2f} {cat['count']:>6} {cat['percentage']:>7.1f}% {bar}")
            print("-" * 65)


def display_monthly_report() -> None:
    """Display history of spending by month."""
    expenses = tracker.get_all_expenses()
    breakdown = monthly_breakdown(expenses)

    if not breakdown:
        print_message("No historical expenses to analyze.", "warning")
        return

    if RICH_AVAILABLE:
        table = Table(title="Monthly Spending Trends", box=box.ROUNDED, header_style="bold blue")
        table.add_column("Month (YYYY-MM)", justify="center", style="cyan bold", width=16)
        table.add_column("Total ($)", justify="right", style="green bold", width=14)
        table.add_column("Transactions", justify="center", width=14)
        table.add_column("Average / Item ($)", justify="right", style="yellow", width=18)

        for row in breakdown:
            table.add_row(
                row["month"],
                f"${row['total']:,.2f}",
                str(row["count"]),
                f"${row['average']:,.2f}",
            )
        console.print(table)
    else:
        print("\n=== Monthly Spending Trends ===")
        print(f"{'Month':<16} {'Total ($)':>14} {'Transactions':>14} {'Average ($)':>14}")
        print("-" * 60)
        for row in breakdown:
            print(f"{row['month']:<16} {row['total']:>14.2f} {row['count']:>14} {row['average']:>14.2f}")
        print("-" * 60)


# ==============================================================================
# Interactive Terminal Menu
# ==============================================================================

def interactive_add() -> None:
    """Prompt user to add an expense with guided inputs."""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]--- Add New Expense ---[/bold cyan]")
    else:
        print("\n--- Add New Expense ---")

    # Amount
    while True:
        try:
            amt_input = input("Enter amount ($): ").strip()
            if not amt_input:
                print_message("Amount cannot be empty.", "warning")
                continue
            amount = tracker.validate_amount(amt_input)
            break
        except ValueError as err:
            print_message(str(err), "error")

    # Category
    categories = tracker.get_categories()
    print("\nCommon Categories: " + ", ".join(f"[{i+1}] {c}" for i, c in enumerate(categories[:6])))
    cat_input = input("Enter category (or type a new one) [Food]: ").strip()
    if cat_input.isdigit() and 1 <= int(cat_input) <= len(categories[:6]):
        category = categories[int(cat_input) - 1]
    elif cat_input:
        category = cat_input
    else:
        category = "Food"

    # Description
    desc_input = input("Enter description: ").strip()
    if not desc_input:
        desc_input = "N/A"

    # Date
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"Enter date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_input:
        date_input = today_str
    else:
        try:
            date_input = tracker.validate_date(date_input)
        except ValueError as err:
            print_message(f"{err}. Using today's date instead.", "warning")
            date_input = today_str

    try:
        new_exp = tracker.add_expense(
            amount=amount,
            category=category,
            description=desc_input,
            date=date_input,
        )
        print_message(f"Expense #{new_exp.id} successfully added! (${new_exp.amount:.2f} for {new_exp.category})", "success")
    except Exception as err:
        print_message(f"Failed to add expense: {err}", "error")


def interactive_update() -> None:
    """Prompt user to update an existing expense."""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]--- Update Existing Expense ---[/bold cyan]")
    else:
        print("\n--- Update Existing Expense ---")

    id_input = input("Enter Expense ID to update: ").strip()
    if not id_input.isdigit():
        print_message("Expense ID must be a valid number.", "error")
        return

    exp_id = int(id_input)
    expense = tracker.get_expense_by_id(exp_id)
    if not expense:
        print_message(f"No expense found with ID {exp_id}.", "error")
        return

    display_expense_table([expense], title=f"Selected Expense #{exp_id}")

    print("Leave field blank to keep current value.")
    new_amt = input(f"New amount [current: ${expense.amount:.2f}]: ").strip()
    new_cat = input(f"New category [current: {expense.category}]: ").strip()
    new_desc = input(f"New description [current: {expense.description}]: ").strip()
    new_date = input(f"New date (YYYY-MM-DD) [current: {expense.date}]: ").strip()

    amt_val = None
    if new_amt:
        try:
            amt_val = tracker.validate_amount(new_amt)
        except ValueError as err:
            print_message(str(err), "error")
            return

    date_val = None
    if new_date:
        try:
            date_val = tracker.validate_date(new_date)
        except ValueError as err:
            print_message(str(err), "error")
            return

    updated = tracker.update_expense(
        expense_id=exp_id,
        amount=amt_val,
        category=new_cat if new_cat else None,
        description=new_desc if new_desc else None,
        date=date_val,
    )

    if updated:
        print_message(f"Expense #{exp_id} updated successfully!", "success")
        display_expense_table([updated], title=f"Updated Expense #{exp_id}")
    else:
        print_message("Update failed.", "error")


def interactive_delete() -> None:
    """Prompt user to delete an expense by ID."""
    if RICH_AVAILABLE:
        console.print("\n[bold red]--- Delete Expense ---[/bold red]")
    else:
        print("\n--- Delete Expense ---")

    id_input = input("Enter Expense ID to delete: ").strip()
    if not id_input.isdigit():
        print_message("Expense ID must be an integer.", "error")
        return

    exp_id = int(id_input)
    expense = tracker.get_expense_by_id(exp_id)
    if not expense:
        print_message(f"Expense #{exp_id} not found.", "error")
        return

    display_expense_table([expense], title=f"Expense #{exp_id} to be deleted")
    confirm = input(f"Are you sure you want to permanently delete Expense #{exp_id}? (y/N): ").strip().lower()
    if confirm in ("y", "yes"):
        if tracker.delete_expense(exp_id):
            print_message(f"Expense #{exp_id} was deleted successfully.", "success")
        else:
            print_message("Failed to delete expense.", "error")
    else:
        print_message("Deletion canceled.", "info")


def interactive_search() -> None:
    """Search and filter records by keyword, category, or dates."""
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]--- Search & Filter Expenses ---[/bold cyan]")
    else:
        print("\n--- Search & Filter Expenses ---")

    kw = input("Enter search keyword (or press Enter to skip): ").strip() or None
    cat = input("Filter by category (or press Enter to skip): ").strip() or None
    s_date = input("Start date YYYY-MM-DD (or Enter to skip): ").strip() or None
    e_date = input("End date YYYY-MM-DD (or Enter to skip): ").strip() or None

    try:
        results = tracker.search_expenses(
            keyword=kw,
            category=cat,
            start_date=s_date,
            end_date=e_date,
        )
        display_expense_table(results, title="Filtered Search Results")
    except ValueError as err:
        print_message(str(err), "error")


def interactive_budget() -> None:
    """View and adjust monthly budget settings."""
    if RICH_AVAILABLE:
        console.print("\n[bold magenta]--- Monthly Budget Settings ---[/bold magenta]")
    else:
        print("\n--- Monthly Budget Settings ---")

    current_budget = tracker.get_monthly_budget()
    if current_budget:
        print(f"Current Monthly Budget: ${current_budget:,.2f}")
    else:
        print("No monthly budget currently set.")

    opt = input("Would you like to set or update your monthly budget? (y/N): ").strip().lower()
    if opt in ("y", "yes"):
        val_input = input("Enter monthly budget limit ($): ").strip()
        try:
            new_b = tracker.set_monthly_budget(float(val_input))
            print_message(f"Monthly budget set to ${new_b:,.2f}!", "success")
        except ValueError as err:
            print_message(str(err), "error")


def export_data(format_type: str = "csv", out_path: Optional[str] = None) -> None:
    """Export expenses to CSV or JSON format."""
    expenses = tracker.get_all_expenses()
    if not out_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"expenses_export_{timestamp}.{format_type}"

    if format_type.lower() == "json":
        data = [e.to_dict() for e in expenses]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=tracker.FIELDNAMES)
            writer.writeheader()
            for exp in expenses:
                writer.writerow(exp.to_dict())

    print_message(f"Successfully exported {len(expenses)} records to '{out_path}'.", "success")


def run_interactive_menu() -> None:
    """Interactive loop for console menu."""
    while True:
        try:
            # Banner Header
            now = datetime.now()
            month_expenses = filter_by_month(tracker.get_all_expenses(), now.month, now.year)
            month_total = sum(e.amount for e in month_expenses)
            month_name = now.strftime("%B %Y")
            budget = tracker.get_monthly_budget()

            if RICH_AVAILABLE:
                budget_status = ""
                if budget:
                    pct = (month_total / budget) * 100
                    color = "red bold" if month_total > budget else "green"
                    budget_status = f" | Budget: [magenta]${budget:,.2f}[/magenta] ([{color}]{pct:.1f}%[/{color}])"

                header_text = (
                    f"[bold white]EXPENSE TRACKER CLI[/bold white] "
                    f"| Current Month ([cyan]{month_name}[/cyan]): [green bold]${month_total:,.2f}[/green bold]"
                    f"{budget_status}"
                )
                console.print()
                console.print(Panel(header_text, style="bold blue", box=box.DOUBLE))

                console.print("[bold yellow]Menu Options:[/bold yellow]")
                console.print("  [cyan][1][/cyan] List All Expenses")
                console.print("  [cyan][2][/cyan] Add New Expense")
                console.print("  [cyan][3][/cyan] Update Expense")
                console.print("  [cyan][4][/cyan] Delete Expense")
                console.print("  [cyan][5][/cyan] Search & Filter")
                console.print("  [cyan][6][/cyan] Summary & Category Analytics")
                console.print("  [cyan][7][/cyan] Monthly Trends")
                console.print("  [cyan][8][/cyan] Monthly Budget Manager")
                console.print("  [cyan][9][/cyan] Export Expenses (CSV / JSON)")
                console.print("  [cyan][0][/cyan] Exit")
            else:
                print("\n" + "=" * 50)
                print(f"EXPENSE TRACKER CLI | {month_name}: ${month_total:,.2f}")
                print("=" * 50)
                print("1. List All Expenses")
                print("2. Add New Expense")
                print("3. Update Expense")
                print("4. Delete Expense")
                print("5. Search & Filter")
                print("6. Summary & Category Analytics")
                print("7. Monthly Trends")
                print("8. Monthly Budget Manager")
                print("9. Export Expenses")
                print("0. Exit")

            choice = input("\nSelect an option [0-9]: ").strip()

            if choice == "1":
                expenses = tracker.get_all_expenses(sort_by_date=True, reverse=True)
                display_expense_table(expenses, title="All Recorded Expenses (Newest First)")
            elif choice == "2":
                interactive_add()
            elif choice == "3":
                interactive_update()
            elif choice == "4":
                interactive_delete()
            elif choice == "5":
                interactive_search()
            elif choice == "6":
                expenses = tracker.get_all_expenses()
                display_summary_report(expenses)
            elif choice == "7":
                display_monthly_report()
            elif choice == "8":
                interactive_budget()
            elif choice == "9":
                fmt = input("Export format (csv/json) [csv]: ").strip().lower() or "csv"
                export_data(format_type=fmt)
            elif choice in ("0", "exit", "quit", "q"):
                print_message("Thank you for using Expense Tracker! Goodbye.", "info")
                break
            else:
                print_message("Invalid selection. Please choose an option between 0 and 9.", "warning")

        except (KeyboardInterrupt, EOFError):
            print("\n")
            print_message("Session closed. Goodbye!", "info")
            break


# ==============================================================================
# CLI Argument Parser Subcommands
# ==============================================================================

def build_cli_parser() -> argparse.ArgumentParser:
    """Build command line argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Expense Tracker CLI - Manage and analyze your personal finances.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: interactive
    subparsers.add_parser("interactive", help="Start the interactive terminal UI menu")

    # Command: add
    add_parser = subparsers.add_parser("add", help="Add a new expense")
    add_parser.add_argument("-a", "--amount", type=float, required=True, help="Expense amount in dollars")
    add_parser.add_argument("-c", "--category", type=str, required=True, help="Expense category (e.g. Food, Transport)")
    add_parser.add_argument("-d", "--description", type=str, default="N/A", help="Expense description")
    add_parser.add_argument("-t", "--date", type=str, default=None, help="Date in YYYY-MM-DD format (default: today)")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List stored expenses")
    list_parser.add_argument("-c", "--category", type=str, help="Filter by category")
    list_parser.add_argument("-m", "--month", type=int, help="Filter by month (1-12)")
    list_parser.add_argument("-y", "--year", type=int, help="Filter by year (YYYY)")
    list_parser.add_argument("--sort-date", action="store_true", help="Sort entries by date")
    list_parser.add_argument("--desc", action="store_true", help="Sort in descending order")

    # Command: delete
    del_parser = subparsers.add_parser("delete", help="Delete an expense by ID")
    del_parser.add_argument("--id", type=int, required=True, help="ID of the expense to delete")

    # Command: update
    upd_parser = subparsers.add_parser("update", help="Update an existing expense")
    upd_parser.add_argument("--id", type=int, required=True, help="ID of the expense to update")
    upd_parser.add_argument("-a", "--amount", type=float, help="New amount")
    upd_parser.add_argument("-c", "--category", type=str, help="New category")
    upd_parser.add_argument("-d", "--description", type=str, help="New description")
    upd_parser.add_argument("-t", "--date", type=str, help="New date (YYYY-MM-DD)")

    # Command: search
    srch_parser = subparsers.add_parser("search", help="Search expenses by text or date")
    srch_parser.add_argument("-q", "--query", type=str, help="Search keyword")
    srch_parser.add_argument("-c", "--category", type=str, help="Filter by category")
    srch_parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    srch_parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")

    # Command: summary
    sum_parser = subparsers.add_parser("summary", help="Display spending overview and category distribution")
    sum_parser.add_argument("-m", "--month", type=int, help="Month number (1-12)")
    sum_parser.add_argument("-y", "--year", type=int, help="Year (YYYY)")

    # Command: report
    rep_parser = subparsers.add_parser("report", help="View monthly trends or top expenses")
    rep_parser.add_argument("--monthly", action="store_true", help="Display monthly trend table")
    rep_parser.add_argument("--top", type=int, default=0, help="Display top N highest expenses")

    # Command: budget
    bud_parser = subparsers.add_parser("budget", help="View or set monthly budget limit")
    bud_parser.add_argument("--set", type=float, help="Set new monthly budget limit in dollars")

    # Command: export
    exp_parser = subparsers.add_parser("export", help="Export expenses to file")
    exp_parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Export file format")
    exp_parser.add_argument("-o", "--output", type=str, help="Output destination file path")

    return parser


def handle_cli_command(args: argparse.Namespace) -> None:
    """Execute direct non-interactive CLI actions."""
    cmd = args.command

    if cmd == "interactive":
        run_interactive_menu()

    elif cmd == "add":
        try:
            exp = tracker.add_expense(
                amount=args.amount,
                category=args.category,
                description=args.description,
                date=args.date,
            )
            print_message(f"Added expense #{exp.id}: ${exp.amount:.2f} [{exp.category}] '{exp.description}' on {exp.date}", "success")
        except Exception as e:
            print_message(str(e), "error")

    elif cmd == "list":
        expenses = tracker.get_all_expenses(sort_by_date=args.sort_date, reverse=args.desc)
        if args.category:
            expenses = [e for e in expenses if e.category.lower() == args.category.lower()]
        if args.month and args.year:
            expenses = filter_by_month(expenses, args.month, args.year)
        elif args.year:
            expenses = [e for e in expenses if datetime.strptime(e.date, "%Y-%m-%d").year == args.year]

        display_expense_table(expenses, title="Expense List")

    elif cmd == "delete":
        if tracker.delete_expense(args.id):
            print_message(f"Expense #{args.id} deleted successfully.", "success")
        else:
            print_message(f"Expense #{args.id} not found.", "error")

    elif cmd == "update":
        updated = tracker.update_expense(
            expense_id=args.id,
            amount=args.amount,
            category=args.category,
            description=args.description,
            date=args.date,
        )
        if updated:
            print_message(f"Expense #{args.id} updated successfully.", "success")
            display_expense_table([updated], title=f"Updated Expense #{args.id}")
        else:
            print_message(f"Expense #{args.id} not found or failed to update.", "error")

    elif cmd == "search":
        results = tracker.search_expenses(
            keyword=args.query,
            category=args.category,
            start_date=args.start,
            end_date=args.end,
        )
        display_expense_table(results, title="Search Results")

    elif cmd == "summary":
        expenses = tracker.get_all_expenses()
        label = None
        if args.month and args.year:
            expenses = filter_by_month(expenses, args.month, args.year)
            label = f"{args.year}-{args.month:02d}"
        display_summary_report(expenses, month_label=label)

    elif cmd == "report":
        if args.monthly:
            display_monthly_report()
        elif args.top > 0:
            expenses = tracker.get_all_expenses()
            top_list = get_top_expenses(expenses, limit=args.top)
            display_expense_table(top_list, title=f"Top {args.top} Expenses")
        else:
            display_monthly_report()

    elif cmd == "budget":
        if args.set is not None:
            new_b = tracker.set_monthly_budget(args.set)
            print_message(f"Monthly budget set to ${new_b:,.2f}", "success")
        else:
            b = tracker.get_monthly_budget()
            if b:
                print_message(f"Current monthly budget: ${b:,.2f}", "info")
            else:
                print_message("No monthly budget currently configured.", "warning")

    elif cmd == "export":
        export_data(format_type=args.format, out_path=args.output)


def main() -> None:
    """Entry point determining whether to start interactive menu or CLI command."""
    parser = build_cli_parser()
    if len(sys.argv) == 1:
        # Default to interactive menu if no arguments are passed
        run_interactive_menu()
    else:
        args = parser.parse_args()
        handle_cli_command(args)


if __name__ == "__main__":
    main()
