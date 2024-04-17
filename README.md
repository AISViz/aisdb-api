# aisdb-api

Welcome to `aisdb-api`, the official Web API for interfacing with AISdb. This API provides robust tools for querying and downloading AIS data efficiently via HTTP protocols. It is designed for developers, researchers, and enthusiasts who require access to AIS data for their projects or analyses.

## Features

- **Data Query**: Retrieve specific AIS data based on user-defined parameters.
- **Data Download**: Download AIS data in various formats for offline analysis.
- **High Performance**: Built on top of FastAPI and Uvicorn for rapid request handling and data serving.

## Dependencies

Ensure your system has the following dependencies installed for optimal performance and compatibility:

- **[FastAPI](https://fastapi.tiangolo.com/)**: A modern, fast web framework for building APIs with Python 3.7+, designed for high performance and easy to use.
- **[Uvicorn](https://www.uvicorn.org/)**: A lightning-fast ASGI server implementation, using uvloop and httptools for superior speed.
- **[AISdb](https://github.com/AISViz/AISdb)**: A Python package designed for smart storage and interaction with AIS data.

## Installation

To install `aisdb-api` and its dependencies, run the following commands:

```bash
pip install fastapi
pip install "uvicorn[standard]"
pip install aisdb
```

## Quick Start

1. Start the Server:

```bash
python main.py
```

2. Access the API: Navigate to http://127.0.0.1:8000 in your web browser. The API runs on port 8000 by default. To change the port or other web server settings, edit the configurations in the main.py file.
