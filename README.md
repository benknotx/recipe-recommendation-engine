# Recipe Recommendation Engine

A FastAPI-based backend API that recommends recipes based on user ingredients and dietary goals. This educational project demonstrates practical backend engineering concepts including intelligent caching, scoring algorithms, and third-party API integration.

## 🛠️ Tech Stack

- Python 3.12
- FastAPI
- Redis
- httpx
- SlowAPI
- Loguru
- Pydantic
- Docker (Redis container)


## 🎯 Features

- Ingredient-based recipe recommendation engine
- Dietary goal filtering (`high_protein`, `low_carb`, `low_fat`, `balanced`)
- Custom scoring algorithm combining ingredient matching and macronutrient alignment
- Bulk nutrition aggregation to eliminate N+1 external API request patterns
- Asynchronous API architecture using FastAPI + httpx
- Shared async dependency management using FastAPI lifespan context
- Redis-based caching with TTL expiration to reduce external API usage and comply with Spoonacular storage limits
- RESTful API design using query parameters for search endpoints
- Ingredient substitution suggestions
- Structured logging and observability using Loguru
- Health monitoring and cache metrics endpoints
- Rate limiting using SlowAPI middleware

## Quick Example

Get recipe recommendations based on ingredients and a dietary goal:

```bash
GET recipes?goal=high_protein&ingredients=chicken&ingredients=rice&ingredients=broccoli
```

```json
[
  {
    "title": "High Protein Chicken Bowl",
    "overall_score": 0.91,
    "protein": 45.0,
    "calories": 520.0
  }
]
```

## 📋 Prerequisites

- Python 3.12+
- [Spoonacular API Key](https://spoonacular.com/food-api/)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/recipe-recommendation-engine.git
cd recipe-recommendation-engine
```

### 2. Set Up a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

1. Get your free Spoonacular API key from [https://spoonacular.com/food-api/](https://spoonacular.com/food-api/)
2. Create a `.env` file in the project root:

```env
SPOON_KEY=your_api_key_here
```
### 5. Start Redis
Run Redis locally with Docker:
```bash
docker run -d -p 6379:6379 redis
```

### 6. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`
FastAPI automatically generates interactive API documentation.
Available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Welcome Endpoint

**GET** `/`

Returns a welcome message.

```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "message": "Welcome to the Recipe Recommendation Engine!"
}
```

### Health Check

**GET** `/health`

Check if the API is running.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "API": "OK",
  "REDIS": "OK",
  "SPOONACULAR": "OK"
}
```

**GET** `/metrics`
```bash
curl http://localhost:8000/metrics
```
**Response:**
```json
{
  "Cache_hits": 20,
  "Cache_misses": 15,
  "Hit_Ratio": "57.14%"
}
```
### Get Recipes by Ingredients

**GET** /recipes?goal=high_protein&ingredients=chicken&ingredients=rice&ingredients=broccoli`

Find recipes based on available ingredients and dietary goal.

**Query Parameters:**
- `ingredients` (required): Repeated query parameter (e.g., `ingredients=chicken&ingredients=rice`)
- `goal` (required): Dietary goal (`high_protein`, `low_carb`, `low_fat`, `balanced`)


**Response:**
```json
[
  {
    "id": 123456,
    "title": "Grilled Chicken Pasta",
    "match_score": 0.85,
    "goal_alignment_score": 0.95,
    "overall_score": 0.89,
    "calories": 450.0,
    "carbs": 45.0,
    "fat": 12.0,
    "protein": 42.0,
    "percentage_protein": 37.3,
    "percentage_carbs": 40.0,
    "percentage_fat": 22.7
  }
]
```

### Get Recipes by Goal

**GET** `/recipes/goal?goal=low_carb`

Get recipes filtered by dietary goal (regardless of ingredients).

**Response:** Same as `/recipes` endpoint

### Get Recipe Instructions

**GET** `/recipes/{id}`

Get detailed cooking instructions and information for a specific recipe.

**Path Parameters:**
- `id` (required): Recipe ID from a previous request

**Response:**
```json
{
  "id": 123456,
  "title": "Grilled Chicken Pasta",
  "servings": 4,
  "ingredients": "4 Chicken Brea..",
  "instructions": "Step 1: Preheat oven..."
}
```

### Get Ingredient Substitutes

**GET** `/substitutes?ingredient=butter`

Get alternative ingredients for a specific ingredient.

**Response:**
```json
{
  "ingredient": "butter",
  "substitutes": ["oil", "coconut oil", "margarine"]
}
```

### Get Recipe Instructions

**GET** `/recipes/{id}`

Get detailed instructions and ingredients for a specific recipe.

**URL Parameters:**
- `id` (required): Recipe ID (from previous recipe search results)

**Response:**
```json
{
  "id": 123456,
  "title": "Grilled Chicken Pasta",
  "servings": 2,
  "ingredients": ["2 chicken breasts", "1 cup pasta", "1 tomato", "2 tbsp olive oil"],
  "instructions": "1. Grill chicken...\n2. Cook pasta..."
}
```

## 🎓 Dietary Goals Explained

- **High Protein**: Prioritizes protein-rich meals
- **Low Carb**: Minimizes carbohydrate content
- **Low Fat**: Reduces fat content
- **Balanced**: Even macronutrient distribution

## 🧮 Scoring Algorithm

Recipes are ranked using a composite scoring system combining:

- Ingredient Match Score — measures how effectively a recipe utilizes user-provided ingredients
- Goal Alignment Score — evaluates macronutrient distribution against the selected dietary goal
The scoring system prioritizes recipes that:
- maximize ingredient usage
- align with nutritional goals
- reduce unnecessary ingredient mismatch
Final recipe ranking uses score-based sorting after normalization.

### Overall Score
Final score combines both components to rank recipes by relevance and suitability.
If no ingredients are provided:
- Ingredient match score defaults to 0
- Overall score is based entirely on goal alignment
- Recipe ranking uses O(n log n) sorting after scoring.

## 📈 Observability

The application includes lightweight observability tooling:

- Structured request and debugging logs via Loguru
- /health endpoint for dependency health checks
- /metrics endpoint exposing cache hit/miss statistics
- Redis connectivity monitoring
- External API availability verification
Note: Metrics reset on application restart.

## 💾 Caching Strategy

The API uses Redis-based caching to optimize performance and manage external API rate limits.

- Cache Backend: Redis (in-memory data store)
- Cache Expiration: 1 hour (3600 seconds) to comply with Spoonacular API terms
- Key Strategy: Normalized ingredient lists + dietary goal
- Ingredient normalization improves cache hit rates by removing duplicate/common pantry variations
- Shared Redis client managed through FastAPI lifespan context

### Cache Behavior
- Cache hits significantly reduce API calls to Spoonacular
- Cache misses trigger fresh API calls and cache updates
- TTL-based expiration ensures compliance with third-party API constraints

## 📁 Project Structure

```
recipe-recommendation-engine/
├── main.py                          # FastAPI application and endpoints
├── schemas.py                       # Pydantic models for request/response
├── services/
│   ├── spoonacular_service.py      # Spoonacular API integration
│   ├── cache_service.py            # Caching logic and management
│   ├── scoring_service.py          # Recipe scoring algorithms
│   └── helper.py                   # Utility functions
├── .env                            # Environment variables (API key)
├── requirements.txt                # Python dependencies
├── LICENSE                         # License
└── README.md                       # This file
```

## 🔧 Environment Variables

Create a `.env` file with:

```env
SPOON_KEY=your_spoonacular_api_key_here
SPOON_HOST=api.spoonacular.com
REDIS_HOST=localhost
REDIS_PORT= 6379
```

## 🔄 Request Flow
```
Client → FastAPI Endpoint → Redis Cache Check  
           ↓ miss  
        Spoonacular API → Normalize → Score → Redis Cache → Response
```
## 🎯 Use Cases

- **Meal Planning**: Find recipes that match available ingredients and dietary goals
- **Dietary Management**: Discover recipes aligned with nutritional targets
- **Ingredient Substitution**: Adapt recipes based on ingredient availability or preferences
- **Portfolio Project**: Demonstrates backend engineering fundamentals

## 🧠 Key Design Decisions

- Redis caching used for TTL-based, distributed cache management
- Async I/O introduced to improve concurrency during external API and Redis operations
- Designed to comply with third-party API constraints (1-hour storage limit)
- Local scoring system used instead of relying solely on external API ranking
- Separation of concerns via service layer architecture
- External API calls minimized to respect rate limits
- Bulk nutrition retrieval implemented to eliminate inefficient N+1 API request patterns

## ⚠️ API Rate Limit Considerations

Spoonacular enforces a strict daily quota.

This project minimizes usage by:
- Caching responses
- Avoiding duplicate nutrition calls
- Using bulk endpoints where possible

## ⚡ Performance Improvements
- Migrated from per-recipe nutrition requests to Spoonacular bulk nutrition endpoint aggregation
- Added Redis caching to minimize repeated API calls
- Implemented async I/O using FastAPI + httpx
- Reduced redundant cache entries through ingredient normalization

## 🏗️ Engineering Evolution

This project evolved through multiple backend architecture refactors:

- Started with synchronous HTTP requests and local in-memory caching
- Refactored to asynchronous I/O using shared httpx.AsyncClient
- Migrated caching from Python dictionaries to Redis with TTL expiration
- Introduced FastAPI lifespan context management for shared dependency lifecycle handling
- Eliminated inefficient N+1 nutrition API request patterns using Spoonacular bulk endpoints
- Added rate limiting, metrics, and structured observability tooling



## 🚀 Future Enhancements

- Full application Dockerization
- Automated unit and integration testing
- CI/CD pipeline integration
- Persistent metrics and monitoring dashboards
- User authentication and saved recipe preferences
- Database layer for user-generated data

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Educational Purpose

This project was built to demonstrate practical backend engineering concepts including:

- RESTful API architecture with FastAPI
- Asynchronous I/O and concurrency patterns
- Shared dependency lifecycle management
- External API integration and optimization
- Redis caching strategies and TTL management
- N+1 request elimination through bulk aggregation
- Rate limiting and API protection
- Data normalization and scoring pipelines
- Structured logging and observability
- Service-layer architecture and separation of concerns

The project intentionally focuses on real-world API constraints, performance optimization, and scalable backend design patterns.
