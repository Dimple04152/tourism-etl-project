import re

MONTH_MAP = {
    "january": "January",
    "february": "February",
    "march": "March",
    "april": "April",
    "may": "May",
    "june": "June",
    "july": "July",
    "august": "August",
    "september": "September",
    "october": "October",
    "november": "November",
    "december": "December",
}

def parse_filename(filename):
    """
    Extract month and year from filenames like:
        January 2025.pdf
        March 2023.pdf
    """

    name = filename.replace(".pdf", "").strip()
    parts = name.split()

    if len(parts) != 2:
        raise ValueError(f"Invalid file format: {filename}")

    month_raw, year = parts

    month_lower = month_raw.lower()

    if month_lower not in MONTH_MAP:
        raise ValueError(f"Unknown month: {month_raw} in {filename}")

    month_clean = MONTH_MAP[month_lower]

    # year must be 4 digits
    if not re.match(r"^\d{4}$", year):
        raise ValueError(f"Invalid year: {year} in {filename}")

    return month_clean, year

