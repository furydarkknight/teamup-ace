"""
TeamUp by ACE - View Registered Users & Sign-ups CLI
Usage:
    python view_users.py            # View last 15 sign-ups
    python view_users.py --all      # View all users
    python view_users.py --search "priya"   # Search by name or email
    python view_users.py --export   # Export all sign-ups to signups_export.csv
"""

import sqlite3
import sys
import csv
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teamup.db")

def print_table(rows, headers):
    if not rows:
        print("\n[!] No users found.\n")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    str_rows = []
    for r in rows:
        s_row = [str(val) if val is not None else "—" for val in r]
        str_rows.append(s_row)
        for i, val in enumerate(s_row):
            widths[i] = min(max(widths[i], len(val)), 32)  # Cap width at 32

    # Divider line
    div = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    # Header
    print(div)
    header_str = "| " + " | ".join(h.ljust(widths[i])[:widths[i]] for i, h in enumerate(headers)) + " |"
    print(header_str)
    print(div)

    # Rows
    for r in str_rows:
        row_str = "| " + " | ".join(r[i].ljust(widths[i])[:widths[i]] for i in range(len(widths))) + " |"
        print(row_str)

    print(div)
    print(f"Total matching users: {len(rows)}\n")

def main():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file not found at: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    args = sys.argv[1:]

    if "--export" in args:
        cur.execute("""
            SELECT id, name, username, email, role, college, city, year,
                   is_verified, reliability_score, points, created_at
            FROM users
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        headers = ["ID", "Name", "Username", "Email", "Role", "College", "City", "Year", "Verified", "Reliability", "Points", "Created At"]
        out_file = "signups_export.csv"
        with open(out_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"\n[SUCCESS] Exported {len(rows)} users to {out_file}\n")
        conn.close()
        return

    headers = ["ID", "Name", "Email", "Role", "College", "Created At"]

    if "--search" in args:
        idx = args.index("--search")
        if idx + 1 < len(args):
            term = f"%{args[idx + 1]}%"
            cur.execute("""
                SELECT id, name, email, role, college, created_at
                FROM users
                WHERE name LIKE ? OR email LIKE ? OR username LIKE ?
                ORDER BY id DESC
            """, (term, term, term))
        else:
            print("Please provide a search term: python view_users.py --search <term>")
            conn.close()
            return
    elif "--all" in args:
        cur.execute("""
            SELECT id, name, email, role, college, created_at
            FROM users
            ORDER BY id DESC
        """)
    else:
        # Default: last 15 sign-ups
        cur.execute("""
            SELECT id, name, email, role, college, created_at
            FROM users
            ORDER BY id DESC
            LIMIT 15
        """)

    rows = cur.fetchall()
    print("\n=== TEAMUP BY ACE - RECENT SIGN-UPS ===")
    print_table(rows, headers)
    conn.close()

if __name__ == "__main__":
    main()
