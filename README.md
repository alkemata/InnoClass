## Project Description

InnoClass is a system designed to process patent documents by extracting relevant text and generating embeddings using SBERT. It leverages Elasticsearch for efficient searching and matching of these patents, potentially against Sustainable Development Goals (SDGs), and provides an API and UI for user interaction.

## Key Components

**InnoNotebooks: Patent Processing Notebook in TIP:** A Jupyter notebook designed for the TIP platform to load patents, extract key information using regex and keywords, and save the results. The current extraction method relies on regex and keywords, which may benefit from future performance enhancements.

**Backend Services (OVH Server):** Dockerized backend components including Elasticsearch for data storage and search, SBERT for text embeddings, and a FastAPI application for API services. These are located in the `backend` directory (see "Getting Started" for setup).
To start Elasticsearch independently: `docker-compose up -d elasticsearch` (within the `backend` directory).
The system's integration (e.g., API connecting to Elasticsearch, embedding processes) can be verified by running the services (like `api-server` or `embedsearch`) and testing their interactions as described in "Getting Started". For example, the `api-server` is designed to connect to Elasticsearch, utilize SBERT embeddings (via `embedsearch` or integrated logic), and perform search operations.

## Getting Started

This section guides you through setting up and running the InnoClass application locally.

### Prerequisites

*   **Docker and Docker Compose:** Ensure you have Docker and Docker Compose installed on your system. Visit the official Docker website for installation instructions.
*   **Git:** Required for cloning the repository.
*   **Linux-based Environment:** The system is primarily designed for a Linux-based environment, and some scripts or commands might rely on `bash`.
*   **Environment File (.env):**
    Create a file named `.env` in the `backend/` directory. This file will store necessary credentials for the services. Add the following content to it, replacing `<your_strong_password>` with a secure password:
    ```bash
    ELASTIC_PASSWORD=<your_strong_password>
    ELASTICSEARCH_USER=elastic
    ELASTICSEARCH_PASSWORD=<your_strong_password>
    DAGSTER_UI_USER=<user_name>
    DAGSTER_UI_PASSWORD_HASH=<hashed_password>
    TRAEFIK_PASSWORD=<hashed_password>
    TRAEFIK_USER=<user_name>
    ```
    The hash is obtained with the following command:
    ```bash
    echo $(htpasswd -nb youruser yourpassword) | sed -e 's/\$/\$\$/g'
    ```
    
    *Note: Ensure `ELASTICSEARCH_PASSWORD` is the same as `ELASTIC_PASSWORD` for the services to connect correctly.*
    

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/InnoClass.git # Replace with the actual repository URL
    ```
2.  **Navigate to the Backend Directory:**
    ```bash
    cd InnoClass/backend
    ```
    *(Assuming `InnoClass` is the root folder of the cloned repository).*

### Running the Application

The `docker-compose.yml` file in the `backend/` directory is configured to manage and run the entire application stack.

**1. Full Stack:**

*   To build and start all services (Elasticsearch, API server, frontend, etc.):
    ```bash
    docker-compose up -d
    ```
*   On the first run, Docker will download the necessary base images and build the application images, which might take some time.
*   This command starts the following key services:
    *   **Elasticsearch:** Database for storing and searching patent data.
    *   **api-server:** Backend API for application logic.
    *   **embedsearch:** Service for processing and embedding patent text (works in conjunction with the API).
    *   **frontend-server:** Serves the user interface.
    *   **traefik:** Reverse proxy for routing traffic (primarily for deployed environments but included in the compose).

**2. Accessing the Services:**

The services are running on an OVH server and accessible through:

*   **webapp:** `https://innoclass.alkemata.com`

Username and code for the demonstrator: epo and codechallenge25

**3. Development / Specific Services (Optional):**

You can also start specific services if needed:

*   To start only Elasticsearch:
    ```bash
    docker-compose up -d elasticsearch
    ```
*   To start only the API server (ensure Elasticsearch is already running):
    ```bash
    docker-compose up -d api-server
    ```
*   To start the text embedding service (ensure Elasticsearch is already running):
    ```bash
    docker-compose up -d embedsearch
    ```

**4. Stopping the Application:**

*   To stop all running services managed by Docker Compose:
    ```bash
    docker-compose down
    ```
    This command will stop and remove the containers.

### Structure of the files

- Source code
        -> classEngine
            -> app: the fastapi server to provide the interface between the web app and the dagster pipeline
            -> data: store data transfered from and to TIP via scp
            -> frontend
                -> src React pages
            -> dagster_home: the code to create the pipelines for Dagster specific to the SDG classification
            -> InnoNotebooks: the notebooks for querying data and finetuning LLMs

