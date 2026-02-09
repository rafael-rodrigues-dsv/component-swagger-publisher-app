# OpenAPI Documentation Publisher

🚀 **Automated OpenAPI/Swagger specification publisher for collaborative documentation platforms**

## Overview

This tool reads OpenAPI specifications (2.0 and 3.x) in JSON/YAML format, maps them to a canonical domain model, and generates elegant, responsive HTML documentation with support for publishing to various platforms.

## Features

✅ **Support for OpenAPI 2.0 (Swagger) and 3.x**
✅ **Parse from URL or local files** (JSON/YAML)
✅ **Elegant, responsive HTML preview** with inline CSS
✅ **Automatic extraction** of title, version, tags, and endpoints
✅ **Minimal CLI interface** - just URL + Publisher choice
✅ **Clean Architecture** - SOLID principles, extensible design

## MVP - Phase 1: Local Preview

The current version generates beautiful HTML documentation locally. Future phases will add direct publishing to Confluence, GitHub Pages, and other platforms.

## Installation

### Option 1: Auto-setup Script (Recommended) 🚀

**Windows:**
```cmd
execute_doc_generation.bat
```

**Linux/Mac:**
```bash
chmod +x execute_doc_generation.sh
./execute_doc_generation.sh
```

The script will:
- ✅ Create `.venv` automatically if not exists
- ✅ Install all dependencies
- ✅ Activate virtual environment
- ✅ Run the application

### Option 2: Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd component-swagger-publisher-app

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Option 1: Using Auto-execution Script

**Windows:**
```cmd
execute_doc_generation.bat
```

**Linux/Mac:**
```bash
./execute_doc_generation.sh
```

### Option 2: Manual Execution

```bash
# Activate virtual environment (if not already activated)
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac

# Run the application
py main.py
```

You'll be prompted for:
1. **OpenAPI Specification URL** (default: Petstore example)
2. **Publisher** (default: confluence)
3. **Mode** (preview or publish)

The tool will:
- Parse and validate your OpenAPI spec
- Generate responsive HTML documentation
- Save it to `output/publisher/confluence/` (preview) or publish to Confluence (publish)
- Open the preview in your browser (preview mode)

## 🎯 Tested & Working APIs

We've tested the system with these public APIs:

### Quick Test (Small):
```bash
# Petstore (classic example)
https://petstore.swagger.io/v2/swagger.json

# The Cat API (fun!)
https://raw.githubusercontent.com/APIs-guru/openapi-directory/main/APIs/thecatapi.com/1.0.0/openapi.yaml
```

### Real-World (Medium):
```bash
# Spotify Web API
https://raw.githubusercontent.com/sonallux/spotify-web-api/main/fixed-spotify-open-api.yml

# WordPress API
https://raw.githubusercontent.com/APIs-guru/openapi-directory/main/APIs/wordpress.com/1.0/swagger.yaml
```

### Complex (Large):
```bash
# GitHub API (1000+ endpoints)
https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json

# Stripe API (500+ endpoints)
https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json
```

**See full list:** `docs/VERIFIED_APIS.md`

## Usage Examples

### Example 1: Default (Petstore API)

```bash
py main.py
# Press Enter twice to use defaults
```

### Example 2: Custom API

```bash
py main.py
# Enter your OpenAPI spec URL
# Select publisher: confluence
```

### Example 3: Local File

```bash
py main.py
# Enter: ./my-api-spec.yaml
# Select publisher: confluence
```

## Output Structure

```
output/
└── publisher/
    └── confluence/
        ├── index.html      # 📄 Responsive HTML preview
        ├── index.xml       # 📋 Confluence Storage Format (future)
        └── styles.css      # 🎨 CSS styles (embedded in HTML)
```

## Architecture

The project follows **Clean Architecture** principles with clear separation of concerns:

```
📁 Project Structure
├── src/                 # 🎯 Source code (all algorithm)
│   ├── domain/         # 🧠 Core business logic (models, interfaces)
│   │   ├── core/
│   │   │   ├── models/     # Domain entities (ApiSpecification, Operation, etc.)
│   │   │   └── services/   # Domain services (DomainMapper)
│   │   ├── ports/          # Interfaces/contracts
│   │   └── utils/          # Utilities (JsonLoader)
│   │
│   ├── infrastructure/ # ⚙️ Technical implementations
│   │   ├── parsing/    # Parsers (Swagger2Parser, OpenApi3Parser)
│   │   ├── rendering/  # Renderers (HtmlRenderer)
│   │   ├── publishing/ # Publishers (ConfluencePublisher)
│   │   └── repository/ # Static resources (templates, CSS)
│   │
│   └── application/    # 🎯 Application services (orchestration)
│       └── services/   # PublishingService
│
├── main.py             # 🖥️ Application entry point
├── docs/               # 📖 Documentation
│   ├── ARCHITECTURE.md
│   └── SUMMARY.md
│
└── tests/              # 🧪 Tests
    └── test_automated.py
```

## Key Components

### Domain Models

- **ApiSpecification**: Root canonical model (version-independent)
- **Info, Server, PathItem, Operation**: Core API elements
- **Parameter, RequestBody, Response**: Request/response details
- **Schema, SecurityScheme**: Data types and security

### Parsers

- **Swagger2Parser**: Parses OpenAPI 2.0 specifications
- **OpenApi3Parser**: Parses OpenAPI 3.x specifications
- **ParserFactory**: Auto-detects version and selects parser

### Renderers

- **HtmlRenderer**: Generates responsive HTML with elegant styling

### Publishers

- **ConfluencePublisher**: Saves documentation locally (MVP)
  - Future: Direct Confluence API publishing

## Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp config/.env.example config/.env
```

```env
# For future Confluence publishing (Phase 2)
CONFLUENCE_BASE_URL=https://confluence.your-company.com
CONFLUENCE_USERNAME=your_username
CONFLUENCE_TOKEN=your_api_token
CONFLUENCE_SPACE_KEY=DEV
```

## Roadmap

### ✅ Phase 1: Local Preview (Current - MVP)
- Parse OpenAPI 2.0 and 3.x
- Generate responsive HTML
- Automatic metadata extraction
- Open preview in browser

### 🔜 Phase 2: Confluence Publishing
- Direct API integration with Confluence
- Create/update pages automatically
- Idempotent operations
- Multi-page documentation structure

### 🔜 Phase 3: Extended Platforms
- GitHub Pages
- GitBook
- Notion
- MkDocs
- Custom themes
- Internationalization (i18n)

## Development

### Project Principles

- **Separation of Concerns**: Domain, Application, Infrastructure layers
- **SOLID**: Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion
- **Extensibility**: Easy to add new parsers, renderers, publishers
- **Testability**: Interfaces enable unit and integration tests

### Adding a New Publisher

1. Create class implementing `Publisher` interface
2. Register in `PublisherFactory`
3. Add templates if needed
4. Done! ✨

### Adding a New Parser

1. Create class implementing `OpenApiParser` interface
2. Register in `ParserFactory`
3. Implement version detection
4. Done! ✨

## Testing

```bash
# Run tests (when implemented)
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## Dependencies

- **requests**: HTTP client for fetching remote specs
- **pyyaml**: YAML parsing
- **jinja2**: Template engine for HTML generation
- **colorama**: Colored terminal output
- **python-dotenv**: Environment configuration

## Examples

### Swagger 2.0 (Petstore)
```
https://petstore.swagger.io/v2/swagger.json
```

### OpenAPI 3.0 (Petstore)
```
https://petstore3.swagger.io/api/v3/openapi.json
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow the existing architecture
4. Add tests for new features
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in `doc/ARCHITECTURE.md`

---

**Made with ❤️ by the API Documentation Team**

*Simplifying API documentation, one spec at a time* 🚀

