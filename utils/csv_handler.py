import csv
import os

def read_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv(filepath, data, fieldnames):
    write_header = not os.path.exists(filepath)
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(data)

def update_csv(filepath, id_value, new_data):
    rows = read_csv(filepath)
    updated = False
    for row in rows:
        if row.get('id') == id_value:
            row.update(new_data)
            updated = True
    if updated:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    return updated

def delete_csv(filepath, id_value):
    rows = read_csv(filepath)
    new_rows = [r for r in rows if r.get('id') != id_value]
    if len(new_rows) != len(rows):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(new_rows)
        return True
    return False
