# Sort, search, and form validation helpers
from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from database import VALID_EMAIL_DOMAIN


# R9: keep asking until the user enters a valid menu option
def read_choice(prompt: str, valid: set[str]) -> str:
    while True:
        choice = input(prompt).strip()
        if choice in valid:
            return choice
        print("Invalid choice. Please try again.")


# --- Algorithms ---

# bubble sort - required for coursework
def bubble_sort(
    data: list[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], Any],
    reverse: bool = False,
) -> list[dict[str, Any]]:
    rows = list(data)
    for i in range(len(rows) - 1):
        for j in range(len(rows) - 1 - i):
            left = key_fn(rows[j])
            right = key_fn(rows[j + 1])
            should_swap = (left > right and not reverse) or (left < right and reverse)
            if should_swap:
                rows[j], rows[j + 1] = rows[j + 1], rows[j]
    return rows


# search rows where any field contains the search text
def linear_search(
    data: list[dict[str, Any]],
    term: str,
    fields: list[str],
) -> list[dict[str, Any]]:
    query = term.lower()
    matches = []
    for row in data:
        for field in fields:
            if query in str(row.get(field, "")).lower():
                matches.append(row)
                break
    return matches


_GRADE_THRESHOLDS = [
    (90, "A+"),
    (85, "A"),
    (80, "A-"),
    (75, "B+"),
    (70, "B"),
    (65, "B-"),
    (60, "C+"),
    (55, "C"),
    (50, "C-"),
    (45, "D"),
]


# turn number grade into letter (A+, B, etc.)
def grade_to_letter(grade: float) -> str:
    for threshold, letter in _GRADE_THRESHOLDS:
        if grade >= threshold:
            return letter
    return "F"


# --- Validators ---

def validate_name(name: str) -> str | None:
    if not name.strip():
        return "Name cannot be empty."
    if not name[0].isupper():
        return "Name must start with a capital letter."
    if not re.match(r"^[A-Za-z\-' ]+$", name):
        return "Name may only contain letters, hyphens, apostrophes, spaces."
    return None


def validate_email(email: str) -> str | None:
    if not email.strip():
        return "Email cannot be empty."
    if not email.endswith(VALID_EMAIL_DOMAIN):
        return f"Email must end with {VALID_EMAIL_DOMAIN}"
    local = email[: -len(VALID_EMAIL_DOMAIN)]
    if not re.match(r"^[a-z][a-z0-9._]*$", local):
        return "Email local part must be lowercase letters, digits, dots or underscores."
    return None


def validate_dob(dob_str: str) -> str | None:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        return "Date of birth must be YYYY-MM-DD format."

    today = date.today()
    age = (today - dob).days // 365
    if not (1900 <= dob.year <= today.year):
        return f"Year must be between 1900 and {today.year}."
    if age < 16:
        return "Student must be at least 16 years old."
    if age > 100:
        return "Please enter a realistic date of birth."
    return None


def validate_grade(grade_str: str) -> str | None:
    try:
        grade = float(grade_str)
    except ValueError:
        return "Grade must be a number."

    if not 0 <= grade <= 100:
        return "Grade must be between 0 and 100."
    return None
