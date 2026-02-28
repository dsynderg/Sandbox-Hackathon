"""
RAG Database builder for formatted textbook using Chroma.
Parses the markdown structured textbook and stores sections with metadata.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from chroma_db import add_to_database


def parse_textbook(file_path: str) -> tuple[List[str], List[str], List[Dict]]:
    """
    Parse the formatted textbook and extract sections with metadata.
    
    Returns:
        Tuple of (ids, documents, metadatas)
        - ids: Incrementing paragraph numbers (1, 2, 3, ...)
        - documents: The text content for each subsection
        - metadatas: Metadata dicts containing chapter, section, subsection info
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    ids = []
    documents = []
    metadatas = []
    paragraph_counter = 1
    
    # Split by section dividers (---)
    sections = content.split('\n---\n')
    
    current_chapter = None
    current_section = None
    
    for section_content in sections:
        lines = section_content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for chapter header (# CHAPTER)
            if line.startswith('# '):
                current_chapter = line.replace('# ', '').strip()
                i += 1
                continue
            
            # Check for section header (## SECTION)
            if line.startswith('## '):
                current_section = line.replace('## ', '').strip()
                i += 1
                continue
            
            # Check for subsection header (### Subsection)
            if line.startswith('### '):
                subsection_title = line.replace('### ', '').strip()
                
                # Extract the subsection content (everything until next header or end)
                subsection_content_lines = []
                i += 1
                
                while i < len(lines):
                    if lines[i].startswith('###') or lines[i].startswith('##') or lines[i].startswith('#'):
                        break
                    subsection_content_lines.append(lines[i])
                    i += 1
                
                subsection_text = '\n'.join(subsection_content_lines).strip()
                
                if subsection_text:  # Only add if there's content
                    # Use incrementing paragraph number as ID
                    ids.append(str(paragraph_counter))
                    documents.append(subsection_text)
                    
                    # Create metadata
                    metadata = {
                        'chapter': current_chapter or 'Unknown',
                        'section': current_section or 'Unknown',
                        'subsection': subsection_title
                    }
                    metadatas.append(metadata)
                    
                    paragraph_counter += 1
                
                continue
            
            i += 1
    
    return ids, documents, metadatas

def create_textbook_database(
    textbook_path: str,
    collection_name: str = "textbook-chapters",
    persist_dir: str = None
):
    """
    Create a Chroma database from the formatted textbook.
    
    Args:
        textbook_path: Path to the formatted textbook file
        collection_name: Name for the Chroma collection
        persist_dir: Directory to persist the database (optional)
    """
    print(f"Parsing textbook from {textbook_path}...")
    ids, documents, metadatas = parse_textbook(textbook_path)
    
    print(f"Found {len(ids)} subsections")
    print("\nSubsections found:")
    for para_id, metadata in zip(ids, metadatas):
        print(f"  Paragraph {para_id}: {metadata['subsection']}")
    
    print(f"\nAdding to Chroma database '{collection_name}'...")
    add_to_database(
        collection_name=collection_name,
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        persist_dir=persist_dir
    )
    
    print(f"✓ Successfully created RAG database with {len(ids)} documents!")
    return ids, documents, metadatas


if __name__ == "__main__":
    # Set up paths
    dexter_dir = Path(__file__).parent
    textbook_file = dexter_dir / "chapter_1_textbook_formatted.txt"
    db_dir = dexter_dir / "chroma_db_persistent"
    
    # Create the database
    ids, documents, metadatas = create_textbook_database(
        str(textbook_file),
        collection_name="chapter-1-functions",
        persist_dir=str(db_dir)
    )
    
    # Print example
    print("\n" + "="*60)
    print("Example: First subsection")
    print("="*60)
    if ids:
        print(f"ID: {ids[0]}")
        print(f"Metadata: {metadatas[0]}")
        print(f"Content preview (first 200 chars):\n{documents[0][:200]}...")
