# How to Upload Multiple Files Using Postman

## Endpoint Information
- **URL**: `http://localhost:8000/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

## Step-by-Step Instructions

### 1. Open Postman and Create a New Request
- Click on "New" → "HTTP Request"
- Set the method to **POST**
- Enter the URL: `http://localhost:8000/upload`

### 2. Configure the Request Body
- Go to the **Body** tab
- Select **form-data** (NOT raw or x-www-form-urlencoded)

### 3. Add Files
- Click on the first row in the form-data table
- In the **KEY** column, type: `files`
- Hover over the right side of the KEY field and change the type from "Text" to **File** using the dropdown
- In the **VALUE** column, click "Select Files"
- **Select multiple files** (you can select 2 or more files at once by holding Ctrl/Cmd while clicking)

### 4. Add Category Parameter
- Click on the next row
- In the **KEY** column, type: `category`
- Keep the type as "Text"
- In the **VALUE** column, type either: `hr` or `product`

### 5. Send the Request
- Click the **Send** button
- Wait for the response

## Expected Response

### Success Response (200 OK)
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

### Partial Success Response
```json
{
  "message": "Processed 2 file(s): 1 successful, 1 failed",
  "total_chunks_processed": 23,
  "category": "hr",
  "files": [
    {
      "filename": "document1.pdf",
      "status": "success",
      "chunks_processed": 23
    },
    {
      "filename": "corrupted.pdf",
      "status": "failed",
      "error": "Failed to load file: PDF parsing error"
    }
  ]
}
```

## Supported File Types
- PDF (`.pdf`)
- Text files (`.txt`)
- Word documents (`.docx`)

## Notes
- You can upload as many files as you want in a single request
- All files will be processed for the same category (hr or product)
- If you want to upload files to different categories, make separate requests
- Each file is processed independently - if one fails, others will still be processed
- The backend is running on `http://localhost:8000`
