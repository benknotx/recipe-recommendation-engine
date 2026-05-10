# Recipe Recommendation Engine

A FastAPI-based backend API that recommends recipes based on user ingredients and dietary goals. This v1 educational project demonstrates practical backend engineering concepts including intelligent caching, scoring algorithms, and third-party API integration.

## 🎯 Features

- Ingredient-based recipe search
- Dietary goal filtering (high protein, low carb, low fat, balanced)
- Custom scoring algorithm (ingredient match + nutrition alignment)
- Ingredient substitution suggestions
- Redis-based caching layer with TTL to minimize external API usage and comply with rate limits
- RESTful API design using query parameters for search endpoints
- Detailed recipe instructions and nutrition data
- Structured logging via Loguru for debugging and observability

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

- Python 3.8+
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

### 5. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

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
curl https://localhost:8000/metrics
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

**GET** /recipes/recipes?goal=high_protein&ingredients=chicken&ingredients=rice&ingredients=broccoli`

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

**GET** `/recipes?goal=low_carb`

Get recipes filtered by dietary goal (regardless of ingredients).

**Response:** Same as `/recipes` endpoint

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

Recipes are ranked using:
- **Ingredient Match (60%)** – how many provided ingredients are used
- **Goal Alignment (40%)** – how well the recipe matches the selected dietary goal
Weights are configurable and can be tuned based on user preference or feedback.

### Overall Score
Final score combines both components to rank recipes by relevance and suitability.
If no ingredients are provided:
- Ingredient match score defaults to 0
- Overall score is based entirely on goal alignment
- Recipe ranking uses O(n log n) sorting after scoring.

## 💾 Caching Strategy

The API uses Redis-based caching to optimize performance and manage external API rate limits.

- **Cache Backend**: Redis (in-memory data store)
- **Cache Expiration**: 1 hour (3600 seconds) to comply with Spoonacular API terms
- **Key Strategy**: Normalized ingredient lists + dietary goal
- **Filtering**: Common pantry items (oil, salt, pepper, sugar, flour, water, butter) are excluded from cache keys to improve hit rates

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

## 📊 Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Pydantic**: Data validation and parsing
- **Requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management
- **loguru**: Logging library
- **uvicorn**: ASGI web server

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
- Designed to comply with third-party API constraints (1-hour storage limit)
- Chose synchronous requests in V1 for simplicity; async considered for V2 performance improvements
- Local scoring system used instead of relying solely on external API ranking
- Separation of concerns via service layer architecture
- External API calls minimized to respect rate limits

## ⚠️ API Rate Limit Considerations

Spoonacular enforces a strict daily quota.

This project minimizes usage by:
- Caching responses
- Avoiding duplicate nutrition calls
- Using bulk endpoints where possible

## ⚡ Performance Improvements
- Eliminated redundant external API calls using Redis caching
- ~~Reduced N+1 request pattern by leveraging bulk endpoints~~
- Improved response consistency through data normalization


## 🚀 Future Enhancements

- Async API calls for improved performance (httpx + asyncio)
- Docker containerization for reproducible environments
- Database layer for storing user inputs (not third-party data)
- Rate limiting to protect API endpoints

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎓 Educational Purpose

This is a v1 educational project created to demonstrate:
- RESTful API design with FastAPI
- Third-party API integration
- Caching strategies and optimization
- Scoring and ranking algorithms
- Error handling and validation
- Project structure and best practices

Designed to demonstrate practical backend engineering concepts and real-world API constraints.
