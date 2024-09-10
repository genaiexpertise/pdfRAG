import os
import tempfile
import boto3
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.vectorstores.pgvector import PGVector
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# AWS S3 Configuration
s3_bucket_name = os.getenv("S3_BUCKET_NAME") # Specify the S3 bucket name
s3_folder = os.getenv("S3_FOLDER_NAME")  # Specify the S3 folder containing the PDFs

# Initialize S3 client
s3_client = boto3.client('s3')

def download_pdfs_from_s3(bucket_name, folder, local_dir):
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder)
    if 'Contents' not in response:
        return []

    pdf_paths = []
    for item in response['Contents']:
        file_name = os.path.basename(item['Key'])
        if file_name.endswith('.pdf'):
            local_path = os.path.join(local_dir, file_name)
            s3_client.download_file(bucket_name, item['Key'], local_path)
            pdf_paths.append(local_path)
    
    return pdf_paths

# Create a temporary directory to download PDFs
with tempfile.TemporaryDirectory() as temp_dir:
    pdf_files = download_pdfs_from_s3(s3_bucket_name, s3_folder, temp_dir)
    
    # Load the PDFs using UnstructuredPDFLoader
    docs = []
    for pdf_file in pdf_files:
        loader = UnstructuredPDFLoader(filepath=pdf_file)
        docs.extend(loader.load())

    # Proceed with embeddings and text splitting
    embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')
    
    text_splitter = SemanticChunker(embeddings=embeddings)
    
    flattened_docs = [doc[0] for doc in docs if doc]
    chunks = text_splitter.split_documents(flattened_docs)
    
    PGVector.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="nglegaldocs",
        connection_string="postgresql+psycopg://user12:pass12@192.168.1.96:5432/vector_db",
        pre_delete_collection=True,
    )


