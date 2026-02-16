import os
import shutil
import uuid
import time
import traceback
from pypdf import PdfReader
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

def load_file(filepath: str) -> str:
    """Loads text from a file. Supports .txt and .pdf"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
            
    elif ext == '.pdf':
        text = ""
        try:
            reader = PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            raise RuntimeError(f"Error reading PDF {filepath}: {e}")
        return text

    elif ext == '.docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
             raise RuntimeError(f"Error reading DOCX {filepath}: {e}")
    
    elif ext == '.doc':
        # Try textract first
        try:
            import textract
            text = textract.process(filepath).decode('utf-8')
            return text
        except Exception as textract_error:
            # If textract fails, try using pywin32 COM automation (requires MS Word installed)
            try:
                import win32com.client
                import pythoncom
                
                pythoncom.CoInitialize()
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                
                # Convert to absolute path
                abs_path = os.path.abspath(filepath)
                doc = word.Documents.Open(abs_path)
                text = doc.Content.Text
                doc.Close(False)
                word.Quit()
                pythoncom.CoUninitialize()
                
                return text
            except Exception as com_error:
                raise RuntimeError(
                    f"Error reading DOC {filepath}. Tried textract: {str(textract_error)}. "
                    f"Tried Word COM: {str(com_error)}. "
                    f"Please convert the file to .docx or .txt format."
                )
    
    elif ext == '.csv':
        try:
            import pandas as pd
            df = pd.read_csv(filepath)
            return df.to_string()
        except Exception as e:
            raise RuntimeError(f"Error reading CSV {filepath}: {e}")
    
    elif ext == '.xlsx' or ext == '.xls':
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            return df.to_string()
        except Exception as e:
            raise RuntimeError(f"Error reading Excel {filepath}: {e}")
    
    elif ext == '.json':
        try:
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception as e:
            raise RuntimeError(f"Error reading JSON {filepath}: {e}")
        
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .txt, .pdf, .docx, .csv, .xlsx, .json")


def load_file_with_structure(filepath: str, output_image_dir: str = None) -> str:
    """
    Loads text from a file preserving structure and extracting images (for .doc/.docx).
    Returns Markdown-formatted text.
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.doc', '.docx']:
        import win32com.client
        import pythoncom
        
        if BeautifulSoup is None:
            raise ImportError("The 'beautifulsoup4' library is required for structure-aware loading. Please run: pip install beautifulsoup4")

        temp_html_path = filepath + ".temp.html"
        abs_path = os.path.abspath(filepath)
        abs_html_path = os.path.abspath(temp_html_path)
        
        try:
            pythoncom.CoInitialize()
            word = None
            try:
                try:
                    word = win32com.client.DispatchEx("Word.Application")
                except:
                    word = win32com.client.Dispatch("Word.Application")
                
                word.Visible = False
                word.DisplayAlerts = 0 
                
                # Retry loop for 'Call rejected by callee'
                doc = None
                for i in range(5):
                    try:
                        doc = word.Documents.Open(abs_path, ReadOnly=True)
                        break
                    except Exception as e:
                        if "rejected by callee" in str(e).lower() and i < 4:
                            time.sleep(1)
                            continue
                        raise e

                doc.SaveAs2(abs_html_path, FileFormat=10) 
                doc.Close(False)
                word.Quit()
            except Exception as com_err:
                if word:
                    try: word.Quit()
                    except: pass
                raise RuntimeError(f"Word COM extraction failed: {com_err}")
            finally:
                pythoncom.CoUninitialize()

            # 2. Parse HTML
            if not os.path.exists(abs_html_path):
                raise RuntimeError("HTML conversion failed - output file missing.")
                
            try:
                with open(abs_html_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
            except:
                with open(abs_html_path, 'r', encoding='latin-1', errors='replace') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                
            markdown_content = ""
            
            # Process paragraphs, headers, and tables
            for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol']):
                text = element.get_text().strip()
                if not text and not element.find('img'): continue
                
                tag_name = element.name.lower()
                prefix = ""
                
                if tag_name.startswith('h') and len(tag_name) == 2:
                    prefix = "#" * int(tag_name[1]) + " "
                elif tag_name == 'table':
                    # Simple table to markdown
                    md_table = "\n"
                    rows = element.find_all('tr')
                    for i, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        row_text = "| " + " | ".join([c.get_text().strip() for c in cells]) + " |"
                        md_table += row_text + "\n"
                        if i == 0: # Add separator after header row
                            md_table += "| " + " | ".join(["---"] * len(cells)) + " |\n"
                    markdown_content += md_table + "\n"
                    continue # Skip general text processing for tables
                elif tag_name in ['ul', 'ol']:
                    for li in element.find_all('li'):
                        bullet = "* " if tag_name == 'ul' else "1. "
                        markdown_content += f"{bullet}{li.get_text().strip()}\n"
                    markdown_content += "\n"
                    continue
                else:
                    classes = element.get('class', [])
                    if classes:
                        cls_str = " ".join(classes).lower()
                        if "heading1" in cls_str or "heading 1" in cls_str: prefix = "# "
                        elif "heading2" in cls_str or "heading 2" in cls_str: prefix = "## "
                        elif "heading3" in cls_str or "heading 3" in cls_str: prefix = "### "
                
                # Extract images
                import urllib.parse
                images = element.find_all('img')
                for img in images:
                    src = img.get('src')
                    if src and output_image_dir:
                        # Decode URL encoded src (e.g. %20 -> space)
                        src = urllib.parse.unquote(src)
                        
                        img_abs_path = os.path.join(os.path.dirname(abs_html_path), src)
                        
                        # Fallback: sometimes Word exports images to a fixed 'document_files' folder 
                        # regardless of HTML filename if it's not well-formed
                        if not os.path.exists(img_abs_path):
                             print(f"Image not found at {img_abs_path}")
                             
                        if os.path.exists(img_abs_path):
                             new_img_name = f"{os.path.basename(filepath)}_{os.path.basename(img_abs_path)}"
                             dest_path = os.path.join(output_image_dir, new_img_name)
                             shutil.copy2(img_abs_path, dest_path)
                             markdown_content += f"\n![Image](/static/images/{new_img_name})\n"
                
                if text and tag_name not in ['table', 'ul', 'ol']:
                    markdown_content += f"\n{prefix}{text}\n"

            return markdown_content

        except Exception as e:
            traceback.print_exc()
            raise RuntimeError(f"Error processing document structure: {e}")
        finally:
            # Cleanup temp files
            if os.path.exists(abs_html_path):
                os.remove(abs_html_path)
            possible_dir = abs_html_path.rsplit('.', 1)[0] + "_files"
            if os.path.exists(possible_dir):
                shutil.rmtree(possible_dir)

    else:
        return load_file(filepath)
