import csv
import pathlib

input_path = pathlib.Path('/Users/maples/Github/power-radar-lab/data/Book1.csv')
output_path = input_path

# Read with utf-8-sig to strip BOM
with input_path.open('r', encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    rows = []
    for row in reader:
        # Strip leading/trailing whitespace from each cell
        cleaned_row = [cell.strip() if isinstance(cell, str) else cell for cell in row]
        rows.append(cleaned_row)

# Write back with all fields quoted, Unix line endings
with output_path.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
    writer.writerows(rows)

print(f"Cleaned {len(rows)} rows written to {output_path}")
