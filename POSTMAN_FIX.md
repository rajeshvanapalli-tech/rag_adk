# ✅ POSTMAN FIX - Upload Files

## The Problem
You're getting a "422 Unprocessable Entity" error because:
- The key name is `File` (singular, capitalized)
- The endpoint expects `files` (plural, lowercase)

## The Solution

### Step 1: Fix the Key Name
In the form-data table, change:
- ❌ **WRONG**: `File` 
- ✅ **CORRECT**: `files` (lowercase, plural)

### Step 2: Your Form-Data Should Look Like This

| Key      | Type | Value                    |
|----------|------|--------------------------|
| files    | File | [Select your files here] |
| category | Text | hr                       |

### Step 3: Detailed Instructions

1. In Postman, go to the **Body** tab
2. Select **form-data**
3. **First Row:**
   - Key: Type `files` (all lowercase, plural)
   - Type: Change dropdown to **File**
   - Value: Click "Select Files" and choose your PDF/TXT/DOCX files
4. **Second Row:**
   - Key: Type `category`
   - Type: Keep as **Text**
   - Value: Type `hr` or `product`
5. Click **Send**

## Expected Success Response

```json
{
  "message": "Processed 2 file(s): 2 successful, 0 failed",
  "total_chunks_processed": 45,
  "category": "hr",
  "files": [
    {
      "filename": "document1.pdf",
      "status": "success",
      "chunks_processed": 23
    },
    {
      "filename": "document2.txt",
      "status": "success",
      "chunks_processed": 22
    }
  ]
}
```

## Common Mistakes to Avoid

❌ Using `File` (capitalized)
❌ Using `file` (singular)
❌ Selecting "Text" type instead of "File" type
❌ Forgetting to add the `category` field

✅ Use `files` (lowercase, plural)
✅ Set type to "File"
✅ Select multiple files if needed
✅ Add `category` with value `hr` or `product`

## Still Not Working?

Check these:
1. Backend is running on `http://localhost:8000`
2. URL is exactly: `http://localhost:8000/upload`
3. Method is **POST**
4. Body type is **form-data** (not raw, not x-www-form-urlencoded)
