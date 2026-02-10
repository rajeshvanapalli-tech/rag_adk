from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from typing import List

class StructureAwareChunker:
    """
    Robust Semantic Chunker for HR Policy documents.
    Prioritizes paragraph breaks (\n\n) to keep related content together.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Standard Semantic Splitter
        # Priority: 1. Double Newline (Paragraphs) -> 2. Newline -> 3. Sentences -> 4. Words
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                r"\n\n",       # Paragraphs (Strongest separator)
                r"\n",         # Line breaks
                r"(?<=\. )",   # Sentences (after period+space)
                r" ",          # Words
                ""             # Fallback
            ],
            is_separator_regex=True,
        )

    def clean_text(self, text: str) -> str:
        """
        Standardizes text format for consistent chunking.
        """
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Fix multiple spaces but keep structure (newlines)
        lines = []
        for line in text.split('\n'):
            clean_line = re.sub(r'\s+', ' ', line).strip()
            lines.append(clean_line)
            
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\s+([.,;!?])', r'\1', text)
        text = re.sub(r'^\s*[-*•]\s+', '- ', text, flags=re.MULTILINE)
        
        return text

    def chunk(self, text: str) -> List[str]:
        """
        Chunks text using robust semantic splitting.
        """
        cleaned_text = self.clean_text(text)
        chunks = self.splitter.split_text(cleaned_text)
        return [c for c in chunks if len(c) > 50]


class ProceduralChunker:
    """
    Step-Aware + Hierarchical + Image-Aware Procedural Chunker for product manuals.
    Preserves sequential steps, parent-child relationships, and image references.
    """
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Patterns for detecting structure
        self.step_pattern = re.compile(
            r'(?:^|\n)\s*(?:Step\s*\d+[.:]?|^\d+\.\s+[A-Z])',
            re.IGNORECASE | re.MULTILINE
        )
        self.header_pattern = re.compile(
            r'(?:^|\n)\s*(?:#+\s+.*|(?:\d+(?:\.\d+)*\s+[A-Z][A-Z\s]+))',
            re.MULTILINE
        )
        # Image pattern to detect markdown images
        self.image_pattern = re.compile(r'!\[.*?\]\(.*?\)')
        
        # Fallback splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[r"\n\n", r"\n", r"(?<=\. )", r" ", ""],
            is_separator_regex=True
        )

    def clean_text(self, text: str) -> str:
        """Clean and normalize text while preserving image references."""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        lines = []
        for line in text.split('\n'):
            # Don't strip whitespace from image lines - preserve them
            if self.image_pattern.search(line):
                lines.append(line.strip())
            else:
                clean_line = re.sub(r'\s+', ' ', line).strip()
                lines.append(clean_line)
        
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Don't mess with punctuation near image references
        text = re.sub(r'\s+([.,;!?])', r'\1', text)
        
        return text

    def parse_hierarchy(self, text: str) -> List[dict]:
        """
        Parse text into hierarchical sections with steps and images.
        Returns list of sections with their content, steps, and image metadata.
        """
        sections = []
        current_section = {"header": "Introduction", "content": "", "steps": [], "images": []}
        
        lines = text.split('\n')
        current_step = None
        
        for line in lines:
            # Check if it's an image
            if self.image_pattern.search(line):
                image_ref = line.strip()
                current_section["images"].append(image_ref)
                # Also add to current step if in one
                if current_step is not None:
                    current_step += line + '\n'
                else:
                    current_section["content"] += line + '\n'
            # Check if it's a header
            elif self.header_pattern.match(line):
                # Save previous section if it has content
                if current_section["content"].strip() or current_section["steps"]:
                    sections.append(current_section)
                
                # Start new section
                current_section = {"header": line.strip(), "content": "", "steps": [], "images": []}
                current_step = None
            # Check if it's a step
            elif self.step_pattern.match(line):
                if current_step:
                    current_section["steps"].append(current_step)
                current_step = line.strip() + '\n'
            else:
                # Regular content
                if current_step is not None:
                    current_step += line + '\n'
                else:
                    current_section["content"] += line + '\n'
        
        # Add last step and section
        if current_step:
            current_section["steps"].append(current_step)
        if current_section["content"].strip() or current_section["steps"]:
            sections.append(current_section)
        
        return sections

    def chunk(self, text: str) -> List[str]:
        """
        IMAGE-ANCHORED + STEP-AWARE Chunking.
        Images serve as anchor points - each image gets context before and after.
        Steps are preserved as complete units with their images.
        """
        cleaned_text = self.clean_text(text)
        
        # Parse into hierarchical sections
        sections = self.parse_hierarchy(cleaned_text)
        
        if not sections:
            # Fallback to standard splitting
            return self.splitter.split_text(cleaned_text)
        
        chunks = []
        
        for section in sections:
            header = section["header"]
            content = section["content"]
            steps = section["steps"]
            images = section["images"]
            
            # IMAGE-ANCHORED STRATEGY:
            # If section has images, ensure each image gets context
            if images and steps:
                # Combine header + content + steps
                section_text = f"{header}\n\n{content}\n\n" + "\n".join(steps)
                
                # Check if we need to split
                if len(section_text) > self.chunk_size:
                    # Smart splitting: Keep images with their steps
                    # Add header + content (may have images)
                    if content.strip():
                        intro_chunk = f"{header}\n\n{content}"
                        chunks.append(intro_chunk)
                    
                    # Process steps individually, grouping when possible
                    current_chunk = f"{header}\n\n"
                    for step in steps:
                        # Check if step has an image
                        has_image = any(img in step for img in images)
                        
                        # If adding this step exceeds size
                        if len(current_chunk) + len(step) > self.chunk_size:
                            # Save current chunk if it has content
                            if current_chunk.strip() != f"{header}":
                                chunks.append(current_chunk.strip())
                            
                            # Start new chunk with header + this step
                            # This ensures image-containing steps get header context
                            current_chunk = f"{header}\n\n{step}\n"
                        else:
                            # Add step to current chunk
                            current_chunk += step + "\n"
                    
                    # Add final chunk
                    if current_chunk.strip() != f"{header}":
                        chunks.append(current_chunk.strip())
                else:
                    # Small enough - keep entire section together
                    chunks.append(section_text.strip())
                    
            elif images:
                # Has images but no steps - anchor around images
                section_text = f"{header}\n\n{content}".strip()
                
                if len(section_text) > self.chunk_size:
                    # Split carefully around images
                    # Find image positions
                    image_positions = []
                    for img in images:
                        pos = section_text.find(img)
                        if pos >= 0:
                            image_positions.append((pos, img))
                    
                    if image_positions:
                        # Sort by position
                        image_positions.sort()
                        
                        # Create chunks anchored around images
                        last_end = 0
                        for pos, img in image_positions:
                            # Context before image (at least 200 chars if possible)
                            context_start = max(0, pos - 300)
                            context_end = min(len(section_text), pos + len(img) + 300)
                            
                            chunk_text = section_text[context_start:context_end]
                            # Prepend header
                            chunk_text = f"{header}\n\n{chunk_text}"
                            chunks.append(chunk_text.strip())
                            last_end = context_end
                    else:
                        # Fallback
                        chunks.extend(self.splitter.split_text(section_text))
                else:
                    chunks.append(section_text)
                    
            elif steps:
                # Steps but no images - regular step-aware chunking
                section_text = f"{header}\n\n{content}\n\n" + "\n".join(steps)
                
                if len(section_text) > self.chunk_size:
                    if content.strip():
                        chunks.append(f"{header}\n\n{content}")
                    
                    current_chunk = f"{header}\n\n"
                    for step in steps:
                        if len(current_chunk) + len(step) > self.chunk_size and current_chunk.strip() != f"{header}":
                            chunks.append(current_chunk.strip())
                            current_chunk = f"{header}\n\n"
                        current_chunk += step + "\n"
                    
                    if current_chunk.strip() != f"{header}":
                        chunks.append(current_chunk.strip())
                else:
                    chunks.append(section_text.strip())
            else:
                # No images, no steps - standard content
                section_text = f"{header}\n\n{content}".strip()
                if len(section_text) > self.chunk_size:
                    chunks.extend(self.splitter.split_text(section_text))
                else:
                    chunks.append(section_text)
        
        # Filter and return
        return [c for c in chunks if len(c) > 50]




class DynamicChunker:
    """
    Intelligent Chunker that auto-detects document type and applies the appropriate strategy.
    - HR Documents: Uses StructureAwareChunker (paragraph-based)
    - Product Manuals: Uses ProceduralChunker (step-aware hierarchical)
    """
    def __init__(self):
        self.structure_chunker = StructureAwareChunker()
        self.procedural_chunker = ProceduralChunker()
        
        # Detection patterns
        self.step_indicators = re.compile(
            r'(?:step\s*\d+|navigate|click|select|configure|installation|setup|procedure|manual)',
            re.IGNORECASE
        )
        self.policy_indicators = re.compile(
            r'(?:policy|leave|entitlement|eligibility|employee|benefits|conduct|regulations)',
            re.IGNORECASE
        )
    
    def detect_document_type(self, text: str) -> str:
        """
        Analyzes text to determine if it's a Product Manual or HR Policy.
        Returns: 'product' or 'hr'
        """
        # Sample first 2000 chars for analysis
        sample = text[:2000].lower()
        
        step_count = len(self.step_indicators.findall(sample))
        policy_count = len(self.policy_indicators.findall(sample))
        
        # Check for explicit step markers
        if re.search(r'step\s*\d+', sample, re.IGNORECASE):
            return 'product'
        
        # Compare keyword density
        if step_count > policy_count:
            return 'product'
        else:
            return 'hr'
    
    def chunk(self, text: str) -> List[str]:
        """
        Automatically detects document type and applies optimal chunking strategy.
        """
        doc_type = self.detect_document_type(text)
        
        if doc_type == 'product':
            print(f"[DynamicChunker] Detected: Product Manual → Using ProceduralChunker")
            return self.procedural_chunker.chunk(text)
        else:
            print(f"[DynamicChunker] Detected: HR Policy → Using StructureAwareChunker")
            return self.structure_chunker.chunk(text)


class TaskBasedChunker(StructureAwareChunker):
    """
    Inherits robust splitting logic.
    """
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
