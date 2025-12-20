#!/usr/bin/env python3
"""
Script to check word count in the Physical AI & Humanoid Robotics Textbook.
"""

import os
import re
import argparse
from pathlib import Path

def count_words_in_file(file_path):
    """Count words in a single markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove frontmatter if present
        if content.startswith('---'):
            frontmatter_end = content.find('---', 3)
            if frontmatter_end != -1:
                content = content[frontmatter_end + 3:]

        # Remove markdown code blocks
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        # Remove inline code
        content = re.sub(r'`.*?`', '', content)
        # Remove markdown links but keep the text
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

        # Count words
        words = re.findall(r'\b\w+\b', content)
        return len(words)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def count_words_in_directory(directory):
    """Count words in all markdown files in a directory."""
    total_words = 0
    file_counts = {}

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.md', '.mdx')):
                file_path = Path(root) / file
                word_count = count_words_in_file(file_path)
                total_words += word_count
                file_counts[str(file_path)] = word_count

    return total_words, file_counts

def main():
    parser = argparse.ArgumentParser(description='Check word count in textbook')
    parser.add_argument('--min', type=int, default=15000, help='Minimum word count (default: 15000)')
    parser.add_argument('--max', type=int, default=20000, help='Maximum word count (default: 20000)')
    parser.add_argument('--dir', type=str, default='docs', help='Directory to check (default: docs)')

    args = parser.parse_args()

    total_words, file_counts = count_words_in_directory(args.dir)

    print(f"Word count in {args.dir}/ directory:")
    print(f"Total words: {total_words}")
    print(f"Target range: {args.min} - {args.max}")

    # Print individual file counts
    print("\nFile breakdown:")
    for file_path, count in sorted(file_counts.items()):
        print(f"  {file_path}: {count} words")

    if total_words < args.min:
        print(f"\n❌ ERROR: Word count ({total_words}) is below minimum ({args.min})")
        return 1
    elif total_words > args.max:
        print(f"\n❌ ERROR: Word count ({total_words}) exceeds maximum ({args.max})")
        return 1
    else:
        print(f"\n✅ SUCCESS: Word count ({total_words}) is within target range")
        return 0

if __name__ == "__main__":
    exit(main())