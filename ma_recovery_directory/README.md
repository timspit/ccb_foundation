# Massachusetts Recovery Services Directory

A centralized directory of addiction recovery services across Massachusetts, built with Python, Flask, and modern web technologies.

## 🐳 Docker Setup (Recommended)

This project is containerized for consistent development and deployment environments.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (version 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+)

### Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd ma_recovery_directory
   ```

2. **Build and start the application:**
   ```bash
   make build
   make up
   ```

3. **Access the application:**
   - Web App: http://localhost:5000
   - Health Check: http://localhost:5000/health

### Development Environment

For development with hot-reload and additional tools:

```bash
make dev          # Start development environment
make dev-logs     # View development logs
make dev-shell    # Open shell in container
make dev-down     # Stop development environment
```

### Available Commands

Use the Makefile for common operations:

```bash
make help         # Show all available commands
make build        # Build Docker image
make up           # Start application
make down         # Stop application
make logs         # View logs
make shell        # Open container shell
make test         # Run tests
make test-cov     # Run tests with coverage
make format       # Format code with black
make lint         # Run flake8 linting
make clean        # Clean up Docker resources
```

### Manual Docker Commands

If you prefer direct Docker commands:

```bash
# Build and start
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Execute commands in container
docker-compose exec app python -m pytest
docker-compose exec app bash

# Stop services
docker-compose down
```

## 🔧 Traditional Setup (Alternative)

If you prefer not to use Docker, you can set up a virtual environment:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m flask run
```

## 📁 Project Structure

```
ma_recovery_directory/
├── config/                 # Configuration files
├── data_collection/        # Data processing and scraping
├── web_app/               # Flask web application
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Production Docker setup
├── docker-compose.dev.yml # Development Docker setup
├── Makefile               # Development commands
└── requirements.txt       # Python dependencies
```

## 🚀 Features

- **Web Scraping**: Automated collection from multiple recovery service sources
- **Data Processing**: Clean and validate recovery service information
- **Web Interface**: User-friendly search and browse interface
- **API Endpoints**: RESTful API for integration
- **Data Export**: Multiple format support (CSV, Excel, PDF)

## 🧪 Testing

Run tests using Docker:

```bash
make test           # Run all tests
make test-cov       # Run tests with coverage report
```

## 📊 Data Sources

- BSAS (Bureau of Substance Addiction Services)
- SAMHSA (Substance Abuse and Mental Health Services Administration)
- Massachusetts Helpline

## 🔒 Security

- Non-root container user
- Health checks for monitoring
- Secure dependency management
- Environment variable configuration

## 📝 Development

### Adding Dependencies

1. Add to `requirements.txt`
2. Rebuild the container: `make build`

### Code Quality

```bash
make format    # Format code with black
make lint      # Run flake8 linting
```

### Database (Future)

The Docker setup includes Redis for caching and session management. PostgreSQL can be easily added by uncommenting the relevant sections in `docker-compose.yml`.

## 🚀 Deployment

The Docker setup is production-ready. For deployment:

1. Use `docker-compose.yml` (not the dev version)
2. Set appropriate environment variables
3. Configure reverse proxy (nginx) if needed
4. Set up monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the Docker logs: `make logs`
- Verify container health: `make health`
- Review the configuration files
- Check the troubleshooting section below

## 🔧 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using port 5000
lsof -i :5000
# Kill the process or change the port in docker-compose.yml
```

**Container won't start:**
```bash
# Check logs
make logs
# Rebuild the image
make build
```

**Permission issues:**
```bash
# Clean up and restart
make clean
make build
make up
```

**Selenium/Chrome issues:**
The Dockerfile includes Chrome and ChromeDriver. If you encounter issues, try rebuilding the image.