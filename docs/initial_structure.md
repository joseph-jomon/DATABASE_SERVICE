Creating a separate service to handle writing data to an Elasticsearch database from a batch vectorization service involves several steps. Below is a high-level approach to building this service as a standalone project.

### 1. **Designing the Architecture**

The architecture will include two main services:
- **Vectorization Service**: Responsible for processing data (e.g., text vectorization) and sending the results to the database service.
- **Database Service**: A separate service responsible for receiving vectorized data and writing it to an Elasticsearch database.

### 2. **Setting Up the Database Service**

#### a. **Project Structure**
Create a new project for the database service. You might structure it as follows:

```
elasticsearch_service/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py
│   └── services/
│       ├── __init__.py
│       ├── elasticsearch_client.py
│
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

#### b. **Environment Setup**
Create a `.env` file to store configuration variables like Elasticsearch endpoint, index name, etc.

```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=vector_data
```

#### c. **Dependencies**
Add necessary dependencies to your `requirements.txt`:

```plaintext
fastapi
uvicorn
pydantic
elasticsearch
python-dotenv
```

Install them using `pip`:

```bash
pip install -r requirements.txt
```

#### d. **Elasticsearch Client Setup**
Create an `elasticsearch_client.py` in the `services` directory to handle connections and operations with Elasticsearch.

```python
from elasticsearch import Elasticsearch
import os

class ElasticsearchClient:
    def __init__(self):
        self.host = os.getenv("ELASTICSEARCH_HOST")
        self.port = os.getenv("ELASTICSEARCH_PORT")
        self.index = os.getenv("ELASTICSEARCH_INDEX")
        self.client = Elasticsearch([{'host': self.host, 'port': self.port}])

    def insert_data(self, data):
        response = self.client.index(index=self.index, body=data)
        return response
```

#### e. **API Endpoint to Ingest Data**
Create an `ingest.py` router in the `routers` directory for the API endpoint that receives the vectorized data.

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.elasticsearch_client import ElasticsearchClient

router = APIRouter()

class VectorData(BaseModel):
    id: str
    vector: list[float]

client = ElasticsearchClient()

@router.post("/ingest")
def ingest_data(data: VectorData):
    response = client.insert_data(data.dict())
    if response['result'] == 'created':
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Failed to insert data")
```

#### f. **Main Application Setup**
Finally, set up the `main.py` file to run the FastAPI app and include the ingest router.

```python
from fastapi import FastAPI
from app.routers import ingest

app = FastAPI()

app.include_router(ingest.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. **Deploying the Database Service**

#### a. **Dockerize the Service**
Create a `Dockerfile` to containerize the service:

```Dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run the Docker image:

```bash
docker build -t elasticsearch_service .
docker run -d --name elasticsearch_service -p 8000:8000 --env-file .env elasticsearch_service
```

#### b. **Testing the Service**
Write test cases in the `tests/test_ingest.py` file and run them to ensure the service is functioning correctly.

### 4. **Integration with the Vectorization Service**

In your vectorization service, send POST requests to the `/ingest` endpoint of the database service whenever you have data ready to be stored in Elasticsearch. Here's an example of how this might look:

```python
import requests

def send_to_elasticsearch(vector_data):
    response = requests.post("http://elasticsearch_service:8000/ingest", json=vector_data)
    if response.status_code == 200:
        print("Data sent successfully")
    else:
        print("Failed to send data")
```

### 5. **Considerations for Production**
- **Security**: Implement authentication (e.g., API keys, OAuth) for the API.
- **Error Handling and Logging**: Enhance the service with robust error handling and logging.
- **Scalability**: Consider deploying the service using orchestration tools like Kubernetes to ensure scalability.
- **Monitoring**: Use monitoring tools like Prometheus and Grafana to track the performance and health of your service.

This approach creates a clean separation of concerns, making your services easier to manage, deploy, and scale. Each service can evolve independently, and this architecture supports microservices principles.