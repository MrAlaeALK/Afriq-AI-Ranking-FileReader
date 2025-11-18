# 📊 Afriq AI Ranking - FileReader Service

FastAPI microservice for processing and normalizing country indicator data for the Afriq AI Ranking system.

## 🎯 Purpose

This service handles:
- **Column Detection** - Automatically identifies country and indicator columns in uploaded files
- **Country Matching** - Maps country names to ISO3 codes using fuzzy matching
- **Data Normalization** - Applies various normalization techniques (Min-Max, Z-Score, Robust Scaling, Quantile Transformation)
- **African Country Filtering** - Filters and processes data specifically for African countries

## 🔧 Technology Stack

- **Python 3.11**
- **FastAPI** - Modern, fast web framework
- **Pandas** - Data manipulation and analysis
- **RapidFuzz** - Fast fuzzy string matching
- **Country Converter** - Country name standardization
- **Uvicorn** - ASGI server

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Afriq-AI-Ranking-FileReader
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Application

```bash
# Development
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## 📋 API Endpoints

### Health Check

```bash
GET /docs - Swagger documentation
GET /redoc - ReDoc documentation
```

### Main Endpoints

#### 1. Detect Columns

Analyzes uploaded file and suggests country and indicator columns.

```bash
POST /detect-columns
Content-Type: multipart/form-data

Parameters:
- file: CSV or Excel file

Response:
{
  "countryColumns": ["Country", "Nation", "..."],
  "indicatorColumns": ["GDP", "Population", "..."]
}
```

#### 2. Process Confirmed Data

Processes file with confirmed column mappings and normalization settings.

```bash
POST /process-confirmed
Content-Type: multipart/form-data

Parameters:
- file: CSV or Excel file
- columns: JSON string with configuration

Response: Array of processed scores
[
  {
    "countryName": "Nigeria",
    "countryCode": "NGA",
    "indicatorId": "123",
    "score": 85.5
  },
  ...
]
```

## 🔍 Normalization Methods

### 1. Min-Max Normalization
- Scales values to 0-100 range
- Formula: `(x - min) / (max - min) * 100`

### 2. Z-Score Normalization
- Standardizes using mean and standard deviation
- Clips to ±3 standard deviations

### 3. Robust Scaling
- Uses median and IQR (Interquartile Range)
- Resistant to outliers

### 4. Quantile Transformation
- Maps values to percentile ranks
- Uniform distribution

## 🌍 Supported African Countries

The service recognizes 54 African countries by various name formats:
- Algeria, Angola, Benin, Botswana, Burkina Faso, Burundi...
- (See `ISO3_TO_COUNTRY` mapping in `main.py`)

## 📝 Example Usage

### Python Client

```python
import requests

# Detect columns
with open("data.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/detect-columns",
        files={"file": f}
    )
    print(response.json())

# Process data
import json

config = {
    "countryColumn": "Country",
    "indicatorColumns": [
        {
            "columnName": "GDP",
            "indicatorId": "1",
            "normalizationType": "minmax normalisation"
        }
    ]
}

with open("data.csv", "rb") as f:
    response = requests.post(
        "http://localhost:8000/process-confirmed",
        files={"file": f},
        data={"columns": json.dumps(config)}
    )
    scores = response.json()
```

### cURL

```bash
# Detect columns
curl -X POST "http://localhost:8000/detect-columns" \
  -F "file=@data.csv"

# Process data
curl -X POST "http://localhost:8000/process-confirmed" \
  -F "file=@data.csv" \
  -F 'columns={"countryColumn":"Country","indicatorColumns":[{"columnName":"GDP","indicatorId":"1","normalizationType":"minmax normalisation"}]}'
```

## 🐳 Docker

```bash
# Build image
docker build -t afriqai-filereader .

# Run container
docker run -p 8000:8000 afriqai-filereader
```

## 🚀 Deployment

This service is configured for deployment on **Render** using Docker:

### Automatic Deployment

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically deploy using `render.yaml`

3. **Get Service URL**
   - After deployment, note the service URL (e.g., `https://afriqai-filereader.onrender.com`)
   - Use this URL in your backend's `FASTAPI_BASE_URL` environment variable

See `render.yaml` for full deployment configuration.

## 🧪 Testing

### Test Column Detection

```bash
# Prepare test file
echo "Country,GDP,Population
Nigeria,500,200
Kenya,100,50" > test.csv

# Test endpoint
curl -X POST "http://localhost:8000/detect-columns" \
  -F "file=@test.csv"
```

### Test Data Processing

```bash
curl -X POST "http://localhost:8000/process-confirmed" \
  -F "file=@test.csv" \
  -F 'columns={"countryColumn":"Country","indicatorColumns":[{"columnName":"GDP","indicatorId":"1","normalizationType":"minmax normalisation"}]}'
```

## 📊 Performance

- **File Format Support**: CSV, Excel (.xls, .xlsx)
- **Encoding**: UTF-8, Latin-1 (auto-detected)
- **Fuzzy Matching**: Uses RapidFuzz for fast country name matching
- **Normalization**: Vectorized operations using Pandas

## 🛠️ Development

### Prerequisites

- Python 3.11 or higher
- pip or conda for package management

### Project Structure

```
Afriq-AI-Ranking-FileReader/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── render.yaml         # Render deployment config
└── README.md           # This file
```

### Adding Dependencies

```bash
# Add new package
pip install <package-name>

# Update requirements
pip freeze > requirements.txt
```

## 🆘 Support

For issues and questions:
- Check API documentation at `/docs` endpoint
- Review `render.yaml` for deployment configuration
- Open an issue on GitHub
- Contact your team administrator

---

**Built with ❤️ for African AI Development**

