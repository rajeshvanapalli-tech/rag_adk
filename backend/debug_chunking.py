
import sys
import os

# Add parent dir to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.advanced_chunker import DynamicChunker

# Sample "ConvertRite" text based on user description
sample_text = """
# ConvertRite User Manual

## Introduction
ConvertRite is a powerful data migration tool for Oracle Cloud.

## Project Creation
To create a project in ConvertRite, follow these steps:

1. Login to ConvertRite application.
2. Navigate to the Dashboard.
3. Click on the "Projects" tab.
4. Click "New Project".
5. Select the "POD" from the dropdown. 
   ![Image: pod_selection](/static/images/pod.png)
6. Enter the Project Name and Description.
7. Click Save.

## Loading Data
Once the project is created, you can load data.

### FBDI Templates
Download the FBDI template for your object.
a. Go to "Templates".
b. Search for "Journal Import".
c. Click "Download".

"""


output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunk_debug_out.txt")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("=== DEBUGGING CHUNKING LOGIC ===\n")

    chunker = DynamicChunker()

    # Test Product Category (ProceduralChunker)
    f.write("\n--- Testing Product Category (ProceduralChunker) ---\n")
    product_chunks = chunker.chunk(sample_text, category="product")

    for i, chunk in enumerate(product_chunks):
        f.write(f"\n[Chunk {i}] Type: {chunk.metadata.get('chunk_type')}\n")
        f.write(f"Metadata: {chunk.metadata}\n")
        f.write("-" * 20 + "\n")
        f.write(chunk.text + "\n")
        f.write("-" * 20 + "\n")

    # Test HR Category (StructureAwareChunker)
    f.write("\n--- Testing HR Category (StructureAwareChunker) ---\n")
    hr_chunks = chunker.chunk(sample_text, category="hr")

    for i, chunk in enumerate(hr_chunks):
        f.write(f"\n[Chunk {i}] Type: {chunk.metadata.get('chunk_type')}\n")
        f.write(f"Metadata: {chunk.metadata}\n")
        f.write("-" * 20 + "\n")
        f.write(chunk.text + "\n")
        f.write("-" * 20 + "\n")
    
    print(f"Debug output written to {output_file}")
