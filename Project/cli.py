# This is a no GUI version of the program

from __future__ import annotations

from database import DB_GATEWAY, DatabaseError
from utils import bubble_sort, linear_search, read_choice

# Calls a database and shows errors in if it fails
def _db(proc: str, args: tuple = ()):
    try:
        return DB_GATEWAY.run(proc, args)
    except DatabaseError as exc:
        print(f"Database error: {exc}")
        return None

# Prints the list of records in the terminal
def _print_list(rows: list[dict], keys: tuple[str, ...]) -> None:
    if not rows:
        print("  (no records)")
        return
    for row in rows:
        print("  " + " | ".join(str(row.get(k, "")) for k in keys))


# Main console menu loop to run it in cmd
def run_console() -> None:
    while True:
        print("\n--- School Management (console) ---")
        print("1 View students   2 View teachers   3 View courses")
        print("4 View registrations   5 Search students   6 Sort students by name")
        print("0 Exit")
        choice = read_choice("Enter choice: ", {"0", "1", "2", "3", "4", "5", "6"})
        if choice == "0":
            print("Goodbye.")
            return
        try:
            if choice == "1":
                _print_list(
                    bubble_sort(_db("sp_read_students") or [], lambda r: r["student_id"]),
                    ("student_id", "first_name", "last_name", "group_name"),
                )
            elif choice == "2":
                _print_list(
                    bubble_sort(_db("sp_read_teachers") or [], lambda r: r["teacher_id"]),
                    ("teacher_id", "first_name", "last_name", "department"),
                )
            elif choice == "3":
                _print_list(
                    bubble_sort(_db("sp_read_courses") or [], lambda r: r["course_id"]),
                    ("course_id", "course_code", "course_name", "teacher_name"),
                )
            elif choice == "4":
                _print_list(
                    bubble_sort(_db("sp_read_registrations") or [], lambda r: r["registration_id"]),
                    ("registration_id", "student_name", "course_name"),
                )
            elif choice == "5":
                term = input("Search (id, name, email, group): ").strip()
                data = _db("sp_read_students") or []
                fields = ["student_id", "first_name", "last_name", "email", "group_name"]
                hits = linear_search(data, term, fields) if term else data
                _print_list(hits, ("student_id", "first_name", "last_name", "email"))
            elif choice == "6":
                data = _db("sp_read_students") or []
                sorted_rows = bubble_sort(data, lambda r: r["last_name"].lower())
                _print_list(sorted_rows, ("student_id", "last_name", "first_name"))
        except Exception as exc:
            print(f"Error: {exc}")
