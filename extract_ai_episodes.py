#!/usr/bin/env python3
"""
Script to extract AI-related episodes from index/ai.md
Creates a new folder with AI episodes and an aggregated markdown file.
"""
import os
import re
import shutil
import yaml
from pathlib import Path
from datetime import datetime

def parse_ai_index(ai_md_path):
    """Parse ai.md to extract guest folder names."""
    with open(ai_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract guest folder names from markdown links
    # Pattern: ../episodes/guest-name/transcript.md
    pattern = r'\.\./episodes/([^/]+)/transcript\.md'
    guest_folders = re.findall(pattern, content)

    return guest_folders

def normalize_guest_name(folder_name):
    """Convert folder name to match guest name in frontmatter."""
    # Convert dhanji-r-prasanna -> Dhanji R. Prasanna
    # Convert dharmesh-shah -> Dharmesh Shah
    parts = folder_name.split('-')

    normalized = []
    for part in parts:
        # Handle special cases like middle initials
        if len(part) == 1 or (len(part) == 2 and part[1] == '.'):
            normalized.append(part.upper() + '.')
        else:
            normalized.append(part.capitalize())

    return ' '.join(normalized).replace('. ', '.')

def find_episode_file(guest_folder_name, episodes_dir):
    """Find the episode file for a given guest folder name."""
    normalized_guest = normalize_guest_name(guest_folder_name)

    # Search for files matching this guest
    for file_path in episodes_dir.glob('*.md'):
        # Extract guest name from filename
        # Format: YYYY-MM-DD_Guest-Name_Title.md
        filename = file_path.name

        # Read frontmatter to get the actual guest name
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                frontmatter = yaml.safe_load(match.group(1))
                guest = frontmatter.get('guest', '')

                # Check if guest name matches
                if guest.lower() == normalized_guest.lower():
                    return file_path

                # Also check if the folder name is in the filename (fallback)
                guest_slug = guest.lower().replace(' ', '-').replace('.', '')
                folder_slug = guest_folder_name.lower().replace('.', '')
                if guest_slug == folder_slug:
                    return file_path
        except Exception as e:
            continue

    return None

def extract_frontmatter(file_path):
    """Extract YAML frontmatter from transcript file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return None, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = match.group(2)
        return frontmatter, body
    except yaml.YAMLError:
        return None, content

def create_aggregated_markdown(episode_files, output_path):
    """Create an aggregated markdown file from all AI episodes."""
    with open(output_path, 'w', encoding='utf-8') as out_f:
        out_f.write("# AI Episodes - Aggregated Transcripts\n\n")
        out_f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        out_f.write(f"Total Episodes: {len(episode_files)}\n\n")
        out_f.write("---\n\n")

        for i, file_path in enumerate(sorted(episode_files), 1):
            frontmatter, body = extract_frontmatter(file_path)

            if not frontmatter:
                print(f"⚠️  Could not parse frontmatter for {file_path.name}")
                continue

            # Write episode header
            out_f.write(f"## Episode {i}: {frontmatter.get('guest', 'Unknown')}\n\n")
            out_f.write(f"**Title:** {frontmatter.get('title', 'Unknown')}\n\n")
            out_f.write(f"**Published:** {frontmatter.get('publish_date', 'Unknown')}\n\n")
            out_f.write(f"**Duration:** {frontmatter.get('duration', 'Unknown')}\n\n")
            out_f.write(f"**YouTube:** {frontmatter.get('youtube_url', 'N/A')}\n\n")

            if frontmatter.get('description'):
                out_f.write(f"**Description:** {frontmatter['description']}\n\n")

            out_f.write("### Transcript\n\n")
            out_f.write(body)
            out_f.write("\n\n---\n\n")

            print(f"✅ Added episode {i}: {frontmatter.get('guest', 'Unknown')}")

def main():
    # Paths
    ai_md_path = Path('index/ai.md')
    episodes_dir = Path('episodes')
    output_dir = Path('ai-episodes')
    aggregated_file = output_dir / 'AI_EPISODES_AGGREGATED.md'

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    # Parse ai.md
    print("Parsing index/ai.md...")
    guest_folders = parse_ai_index(ai_md_path)
    print(f"Found {len(guest_folders)} AI episodes listed")

    # Find and copy episode files
    print("\nFinding and copying episode files...")
    found_files = []
    missing_guests = []

    for guest_folder in guest_folders:
        episode_file = find_episode_file(guest_folder, episodes_dir)

        if episode_file:
            # Copy to output directory
            dest_path = output_dir / episode_file.name
            shutil.copy2(episode_file, dest_path)
            found_files.append(episode_file)
            print(f"✅ {guest_folder} -> {episode_file.name}")
        else:
            missing_guests.append(guest_folder)
            print(f"⚠️  Could not find episode for: {guest_folder}")

    # Create aggregated markdown
    print(f"\nCreating aggregated markdown file...")
    create_aggregated_markdown(found_files, aggregated_file)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✅ Successfully copied: {len(found_files)} episodes")
    print(f"⚠️  Missing episodes: {len(missing_guests)}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Aggregated file: {aggregated_file}")
    print(f"📊 Aggregated file size: {aggregated_file.stat().st_size / 1024 / 1024:.2f} MB")

    if missing_guests:
        print(f"\nMissing guests:")
        for guest in missing_guests:
            print(f"  - {guest}")

if __name__ == '__main__':
    main()
