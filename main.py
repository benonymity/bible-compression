import xml.etree.ElementTree as ET
import gzip
import bz2
import lzma
import zlib
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Dict, List, Tuple
from tqdm import tqdm
import pickle
import os
import csv
import inquirer

def compress_text(text: str) -> Dict[str, int]:
    """Compress text using various algorithms and return compressed sizes."""
    return {
        'gzip': len(gzip.compress(text.encode())),
        'bzip2': len(bz2.compress(text.encode())),
        'lzma': len(lzma.compress(text.encode())),
        'zlib': len(zlib.compress(text.encode()))
    }

def parse_bible(file_path: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    """Parse the XML Bible file and return a nested dictionary structure."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    bible = {}
    
    for book in tqdm(root.findall('.//BIBLEBOOK'), desc="Parsing Bible"):
        book_name = book.get('bname')
        bible[book_name] = {}
        
        for chapter in book.findall('.//CHAPTER'):
            chapter_num = chapter.get('cnumber')
            bible[book_name][chapter_num] = {}
            
            for verse in chapter.findall('.//VERS'):
                verse_num = verse.get('vnumber')
                bible[book_name][chapter_num][verse_num] = verse.text.strip()
    
    return bible

def calculate_compression_stats(bible: Dict[str, Dict[str, Dict[str, str]]]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
    """Calculate compression statistics for books, chapters, and verses."""
    book_stats = defaultdict(lambda: defaultdict(float))
    chapter_stats = defaultdict(lambda: defaultdict(float))
    verse_stats = defaultdict(lambda: defaultdict(float))
    
    for book, chapters in tqdm(bible.items(), desc="Processing books"):
        book_text = ' '.join([verse for chapter in chapters.values() for verse in chapter.values()])
        book_compressed = compress_text(book_text)
        for algo, size in book_compressed.items():
            book_stats[book][algo] = size / len(book_text)
        
        for chapter, verses in chapters.items():
            chapter_text = ' '.join(verses.values())
            chapter_compressed = compress_text(chapter_text)
            for algo, size in chapter_compressed.items():
                chapter_stats[f"{book} {chapter}"][algo] = size / len(chapter_text)
            
            for verse_num, verse_text in verses.items():
                verse_compressed = compress_text(verse_text)
                for algo, size in verse_compressed.items():
                    verse_stats[f"{book} {chapter}:{verse_num}"][algo] = size / len(verse_text) if len(verse_text) > 0 else 0
    
    return dict(book_stats), dict(chapter_stats), dict(verse_stats)

def print_stats(stats: Dict[str, Dict[str, float]], title: str, top_bottom: int = None):
    """Print compression statistics in a formatted table, sorted by average ratio."""
    print(f"\n{title}")
    print("-" * 80)
    print(f"{'Item':<30} {'gzip':>10} {'bzip2':>10} {'lzma':>10} {'zlib':>10} {'Average':>10}")
    print("-" * 80)
    
    sorted_items = sorted(stats.items(), key=lambda x: sum(x[1].values()) / len(x[1]))
    
    if top_bottom:
        items_to_print = sorted_items[:top_bottom] + sorted_items[-top_bottom:]
    else:
        items_to_print = sorted_items
    
    for item, algos in items_to_print:
        avg_ratio = sum(algos.values()) / len(algos)
        print(f"{item:<30} {algos['gzip']:>10.2f} {algos['bzip2']:>10.2f} {algos['lzma']:>10.2f} {algos['zlib']:>10.2f} {avg_ratio:>10.2f}")
    
    print("\nNote: Compression ratio is the size of the compressed text divided by the size of the original text.")
    print("A lower ratio indicates better compression efficiency.")

def plot_stats(stats: Dict[str, Dict[str, float]], title: str, filename: str, top_bottom: int = None):
    """Create and save a bar plot of compression statistics, sorted by average ratio."""
    sorted_items = sorted(stats.items(), key=lambda x: sum(x[1].values()) / len(x[1]))
    
    if top_bottom:
        items_to_plot = sorted_items[:top_bottom] + sorted_items[-top_bottom:]
    else:
        items_to_plot = sorted_items
    
    items = [item[0] for item in items_to_plot]
    
    gzip_ratios = [stats[item]['gzip'] for item in items]
    bzip2_ratios = [stats[item]['bzip2'] for item in items]
    lzma_ratios = [stats[item]['lzma'] for item in items]
    zlib_ratios = [stats[item]['zlib'] for item in items]

    x = range(len(items))
    width = 0.2

    fig, ax = plt.subplots(figsize=(15, 10))
    ax.bar([i - 1.5*width for i in x], gzip_ratios, width, label='gzip')
    ax.bar([i - 0.5*width for i in x], bzip2_ratios, width, label='bzip2')
    ax.bar([i + 0.5*width for i in x], lzma_ratios, width, label='lzma')
    ax.bar([i + 1.5*width for i in x], zlib_ratios, width, label='zlib')

    ax.set_ylabel('Compression Ratio')
    ax.set_title(f"{title} (Lower is Better)")
    ax.set_xticks(x)
    ax.set_xticklabels(items, rotation=45, ha='right')
    ax.legend()

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

    print(f"\nPlot saved as {filename}")
    print("\nNote: The graph shows compression ratios for different algorithms.")
    print("Each bar represents the ratio of compressed size to original size.")
    print("Lower bars indicate better compression efficiency.")

def save_stats(stats, filename):
    """Save statistics to a file using pickle."""
    with open(filename, 'wb') as f:
        pickle.dump(stats, f)

def load_stats(filename):
    """Load statistics from a file using pickle."""
    with open(filename, 'rb') as f:
        return pickle.load(f)

def save_stats_to_text(stats: Dict[str, Dict[str, float]], filename: str):
    """Save statistics to a text file."""
    with open(filename, 'w') as f:
        for item, algos in sorted(stats.items(), key=lambda x: sum(x[1].values()) / len(x[1])):
            avg_ratio = sum(algos.values()) / len(algos)
            f.write(f"{item:<30} {algos['gzip']:>10.2f} {algos['bzip2']:>10.2f} {algos['lzma']:>10.2f} {algos['zlib']:>10.2f} {avg_ratio:>10.2f}\n")
    print(f"Statistics saved to {filename}")

def save_stats_to_csv(stats: Dict[str, Dict[str, float]], filename: str):
    """Save statistics to a CSV file."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Item', 'gzip', 'bzip2', 'lzma', 'zlib', 'Average'])
        for item, algos in sorted(stats.items(), key=lambda x: sum(x[1].values()) / len(x[1])):
            avg_ratio = sum(algos.values()) / len(algos)
            writer.writerow([item, algos['gzip'], algos['bzip2'], algos['lzma'], algos['zlib'], avg_ratio])
    print(f"Statistics saved to {filename}")

def main():
    stats_file = 'bible_compression_stats.pkl'
    
    if os.path.exists(stats_file):
        print("Loading pre-computed statistics...")
        book_stats, chapter_stats, verse_stats = load_stats(stats_file)
    else:
        print("Parsing Bible...")
        bible = parse_bible('bible.xml')
        print("Calculating compression statistics...")
        book_stats, chapter_stats, verse_stats = calculate_compression_stats(bible)
        print("Saving statistics...")
        save_stats((book_stats, chapter_stats, verse_stats), stats_file)

    print("\nWelcome to the Bible Compression Analysis Tool!")
    print("This tool analyzes how well different compression algorithms perform on various parts of the Bible.")
    print("Compression ratio is calculated as (compressed size) / (original size).")
    print("A lower ratio indicates better compression efficiency.")

    questions = [
        inquirer.List(
            'analysis_type',
            message="What type of analysis would you like to perform?",
            choices=['Books', 'Chapters', 'Verses'],
        ),
        inquirer.List(
            'output_type',
            message="How would you like to output the results?",
            choices=['Print', 'Plot', 'Save as Text', 'Save as CSV'],
        ),
        inquirer.Text(
            'top_bottom',
            message="How many top and bottom items to show? (Enter 0 for all)",
            validate=lambda _, x: x.isdigit(),
        ),
    ]

    answers = inquirer.prompt(questions)

    analysis_type = answers['analysis_type']
    output_type = answers['output_type']
    top_bottom = int(answers['top_bottom'])

    if analysis_type == 'Books':
        stats = book_stats
        title = "Book Compression Ratios"
        filename = "book_compression"
    elif analysis_type == 'Chapters':
        stats = chapter_stats
        title = "Chapter Compression Ratios"
        filename = "chapter_compression"
    else:
        stats = verse_stats
        title = "Verse Compression Ratios"
        filename = "verse_compression"

    if top_bottom > 0:
        title += f" (Top and Bottom {top_bottom})"
        filename += f"_top_bottom_{top_bottom}"

    if output_type == 'Print':
        print_stats(stats, title, top_bottom if top_bottom > 0 else None)
    elif output_type == 'Plot':
        plot_stats(stats, title, f"{filename}_ratios.png", top_bottom if top_bottom > 0 else None)
    elif output_type == 'Save as Text':
        save_stats_to_text(stats, f"{filename}_stats.txt")
    else:  # Save as CSV
        save_stats_to_csv(stats, f"{filename}_stats.csv")

    print("\nThank you for using the Bible Compression Analysis Tool.")

if __name__ == "__main__":
    main()
