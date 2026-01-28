#!/usr/bin/env python3
"""
Script to flatten episodes directory structure.
Renames transcript.md files to: YYYY-MM-DD_Guest-Name_Title.md
"""
import os
import re
import yaml
from pathlib import Path

def sanitize_filename(text):
    """Convert text to safe filename format."""
    # Remove special characters and replace spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def extract_frontmatter(file_path):
    """Extract YAML frontmatter from transcript file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter between --- markers
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {file_path}: {e}")
        return None

def create_new_filename(frontmatter):
    """Create new filename from frontmatter data."""
    publish_date = frontmatter.get('publish_date', 'UNKNOWN-DATE')
    guest = frontmatter.get('guest', 'Unknown-Guest')
    title = frontmatter.get('title', 'Unknown-Title')

    # Extract main title (before | if present)
    if '|' in title:
        title = title.split('|')[0].strip()

    # Sanitize components
    guest_clean = sanitize_filename(guest)
    title_clean = sanitize_filename(title)

    # Limit title length to avoid extremely long filenames
    if len(title_clean) > 80:
        title_clean = title_clean[:80].rsplit('-', 1)[0]

    return f"{publish_date}_{guest_clean}_{title_clean}.md"

def main():
    episodes_dir = Path('episodes')

    # Find all transcript.md files in subdirectories
    transcript_files = list(episodes_dir.glob('*/transcript.md'))

    print(f"Found {len(transcript_files)} transcript files")

    renamed_count = 0
    error_count = 0

    for old_path in transcript_files:
        # Extract frontmatter
        frontmatter = extract_frontmatter(old_path)
        if not frontmatter:
            print(f"⚠️  Skipping {old_path}: Could not parse frontmatter")
            error_count += 1
            continue

        # Create new filename
        new_filename = create_new_filename(frontmatter)
        new_path = episodes_dir / new_filename

        # Check for conflicts
        if new_path.exists():
            print(f"⚠️  Conflict: {new_filename} already exists")
            error_count += 1
            continue

        # Rename (move) the file
        try:
            old_path.rename(new_path)
            renamed_count += 1
            if renamed_count % 50 == 0:
                print(f"Progress: {renamed_count}/{len(transcript_files)} files renamed")
        except Exception as e:
            print(f"❌ Error renaming {old_path}: {e}")
            error_count += 1

    print(f"\n✅ Successfully renamed {renamed_count} files")
    if error_count > 0:
        print(f"⚠️  Encountered {error_count} errors")

    # Show sample of renamed files
    print("\nSample of renamed files:")
    renamed_files = sorted(episodes_dir.glob('*.md'))[:5]
    for f in renamed_files:
        print(f"  - {f.name}")

if __name__ == '__main__':
    main()
