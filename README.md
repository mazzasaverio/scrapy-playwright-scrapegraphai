# Web Crawler with Scrapy and Playwright

## Description
This project implements a configurable web crawler using Scrapy and Playwright. It's designed to handle different types of URL crawling patterns and can store the results in a PostgreSQL database.

## Features
- Multiple URL crawling strategies
- Playwright integration for JavaScript-rendered content
- PostgreSQL storage
- Configurable crawling patterns and depths
- Docker support
- Terraform infrastructure

## Configuration
The crawler behavior is configured through `config/crawler_config.yaml`. Each crawling target is defined by a category with the following structure:

```yaml
categories:
  - url_seed_root_id: 0
    name: "Category Name"
    description: "Category Description"
    urls:
      - url: "https://example.com"
        type: 1
        target_patterns:
          - ".*\\.pdf$"
        seed_pattern: null
        max_depth: 0
```

### URL Types
- Type 0: Direct target URL
- Type 1: Single page with target URLs
- Type 2: Pages with both seed and target URLs

## Running the Spider

### Basic Usage
To run the spider and process all categories in the configuration:

```bash
python src/run_spider.py
```

### Selective Category Processing
You can process a specific category by providing its `url_seed_root_id`:

```bash
python src/run_spider.py --url_seed_root_id 0
```

This will only process the URLs from the category with the matching `url_seed_root_id` in the configuration file. This is useful when you want to:
- Test changes on a single category
- Debug specific crawling patterns
- Resume processing for a particular category
- Split processing across different instances

For example, if your config has:
```yaml
categories:
  - url_seed_root_id: 0
    name: "Torino"
    ...
  - url_seed_root_id: 1
    name: "Bologna"
    ...
```

Running `python src/run_spider.py --url_seed_root_id 0` will only process the "Torino" category.

## Environment Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables by copying `env.example` to `.env` and filling in the values:
```bash
cp env.example .env
```

## Docker Support
To run using Docker:

```bash
docker-compose -f infrastructure/docker/docker-compose.yml up
```

## Database Management
To clean the database:

```bash
python src/tools/clean_db.py
```

## Logging
The project uses logfire for structured logging. Log level can be configured through the `LEVEL_DEEP_LOGGING` environment variable.

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[License details here]