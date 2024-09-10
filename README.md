# RAG PDF Query Web Application
*** 

### Overview
This web application enables users to interact with their private PDF documents through a Retrieval-Augmented Generation (RAG) model. Users can upload their PDF documents via the web interface, which are then processed and stored for semantic search. The backend, developed using Langserve, handles document processing and semantic search functionalities, while the frontend is built with React and TypeScript for a modern user experience.


### Features
- Upload PDFs: Users can upload their private PDF documents through the web interface.
- Document Storage: Uploaded PDFs are stored in an S3 bucket for secure and scalable storage.
- Semantic Search: Processed documents are stored in a vector database for efficient semantic search.
- Interactive Query: Users can query their documents and get responses from the RAG model.


### Directory Structure
- backend: Contains the backend code developed using Langserve.
- frontend: Contains the frontend code developed using React and TypeScript.


### Getting Started
**Prerequisites**
- Node.js (for frontend development)
- Python (for backend development)
- AWS CLI (for S3 operations)
- Postgres as the vector database service 


### Setup
#### Backend
- Navigate to the backend directory.
- Install the required Python packages
```
pip install -r requirements.txt

```

- Configure the environment variables for S3 and vector database
```
export AWS_ACCESS_KEY_ID=<your-access-key-id>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export VECTOR_DB_URL=<your-vector-db-url>

```

- Run the server

```
langchain serve
```


#### Frontend
- Navigate to the frontend directory.
- Install the required Node.js packages
```
npm install

```

- Start the frontend development server:
```
npm start

```


### Usage
- Open your web browser and navigate to http://localhost:3000.
- Use the upload feature to add your PDF documents.
- Once uploaded, the PDFs are processed and stored.
- Use the query interface to interact with your documents and get responses from the RAG model.


### Deployment
To deploy the application, you will need to set up both the frontend and backend on your chosen hosting platforms. Ensure that the environment variables for S3 and the vector database are properly configured in your deployment environment.

