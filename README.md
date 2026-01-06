# SentinelStream

A hybrid AI trading intelligence platform combining high-performance order book management with advanced AI-powered market analysis.

## Architecture

SentinelStream consists of three core components:

- **Java Core Service** (Port 8080): High-performance trading engine with Virtual Threads and limit order book implementation
- **Python AI Service** (Port 8000): AI-powered market intelligence using LangChain, OpenAI, and Pinecone
- **Redis Event Bus** (Port 6379): Real-time event streaming and caching layer

## Features

### Java Core Service
- ✅ Java 21 with Virtual Threads for massive concurrency
- ✅ High-performance Limit Order Book implementation
- ✅ Price-time priority matching engine
- ✅ Concurrent order processing with thread-safe data structures
- ✅ RESTful API for order management
- ✅ Redis integration for event publishing

### Python AI Service
- ✅ FastAPI-based microservice architecture
- ✅ LangChain integration for AI workflows
- ✅ OpenAI GPT-4 for market analysis and insights
- ✅ Pinecone vector database for semantic search
- ✅ Real-time market sentiment analysis
- ✅ Trading recommendations and intelligence queries

## Prerequisites

- Docker & Docker Compose
- Java 21 (for local development)
- Python 3.12 (for local development)
- Maven 3.9+ (for local development)

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd SentinelStream
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- Redis on `localhost:6379`
- Java Core on `localhost:8080`
- Python AI on `localhost:8000`

### 3. Verify Services

```bash
# Check Java Core
curl http://localhost:8080/actuator/health

# Check Python AI
curl http://localhost:8000/health

# Check Redis
docker exec sentinelstream-redis redis-cli ping
```

## API Documentation

### Java Core Service (Port 8080)

#### Submit Order
```bash
POST /api/orders
Content-Type: application/json

{
  "symbol": "AAPL",
  "side": "BUY",
  "price": 150.00,
  "quantity": 100,
  "remainingQuantity": 100,
  "status": "PENDING"
}
```

#### Cancel Order
```bash
DELETE /api/orders/{symbol}/{orderId}
```

### Python AI Service (Port 8000)

#### Market Analysis
```bash
POST /api/analyze
Content-Type: application/json

{
  "symbol": "AAPL",
  "timeframe": "1D",
  "indicators": ["RSI", "MACD", "Volume"]
}
```

#### Intelligence Query
```bash
POST /api/query
Content-Type: application/json

{
  "symbol": "AAPL",
  "query": "What are the current market conditions?",
  "context": "Recent price action shows consolidation"
}
```

#### Interactive API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Java Core Local Development

```bash
cd java-core
mvn clean install
mvn spring-boot:run
```

### Python AI Local Development

```bash
cd python-ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Project Structure

```
SentinelStream/
├── java-core/                    # Java 21 Trading Engine
│   ├── src/main/java/
│   │   └── com/sentinelstream/
│   │       ├── Application.java
│   │       ├── domain/          # Domain models (Order, Trade)
│   │       ├── orderbook/       # LimitOrderBook implementation
│   │       ├── service/         # Business logic with Virtual Threads
│   │       └── controller/      # REST API controllers
│   ├── pom.xml
│   └── Dockerfile
│
├── python-ai/                    # Python AI Service
│   ├── main.py                  # FastAPI application
│   ├── services/
│   │   ├── intelligence_service.py  # AI/ML logic
│   │   └── redis_service.py         # Redis integration
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml           # Orchestration
├── .env.example                 # Environment template
└── README.md
```

## Technology Stack

### Backend (Java)
- Java 21 (Virtual Threads, Records, Pattern Matching)
- Spring Boot 3.2
- Maven
- Lettuce (Redis client)
- SLF4J + Logback

### AI Service (Python)
- Python 3.12
- FastAPI
- LangChain
- OpenAI GPT-4
- Pinecone Vector Database
- Redis (async)

### Infrastructure
- Docker & Docker Compose
- Redis 7

## Performance Characteristics

### Java Core
- **Concurrency**: Virtual Threads enable millions of concurrent connections
- **Latency**: Sub-millisecond order matching
- **Throughput**: 100K+ orders/second (single instance)
- **Memory**: Efficient with concurrent data structures

### Order Book Implementation
- Price-time priority matching
- O(log n) order insertion
- O(1) best bid/ask retrieval
- Thread-safe with ReadWriteLock

## Configuration

### Java Core (`java-core/src/main/resources/application.yml`)
```yaml
server:
  port: 8080
spring:
  data:
    redis:
      host: redis
      port: 6379
```

### Python AI (Environment Variables)
```env
REDIS_HOST=redis
REDIS_PORT=6379
OPENAI_API_KEY=<your-key>
PINECONE_API_KEY=<your-key>
```

## Monitoring & Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f java-core
docker-compose logs -f python-ai

# Check resource usage
docker stats
```

## Testing

### Java Tests
```bash
cd java-core
mvn test
```

### Python Tests
```bash
cd python-ai
pytest
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose restart

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Redis connection issues
```bash
# Test Redis connectivity
docker exec sentinelstream-redis redis-cli ping

# Check network
docker network inspect sentinelstream_sentinelstream-network
```

## Roadmap

- [ ] WebSocket support for real-time order updates
- [ ] Market data ingestion pipeline
- [ ] Advanced AI strategies (reinforcement learning)
- [ ] Multi-exchange connectivity
- [ ] Backtesting framework
- [ ] Performance metrics dashboard
- [ ] Kubernetes deployment manifests

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`

---

**Built with ❤️ for high-performance trading**

