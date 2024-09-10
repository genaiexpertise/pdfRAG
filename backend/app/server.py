from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from starlette.staticfiles import StaticFiles
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import subprocess
from app.rag_chain import final_chain

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
        "https://rag.genaiexpertise.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client('s3')

@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded_files = []
    for file in files:
        try:
            # Upload file to S3
            s3_client.upload_fileobj(
                file.file,
                s3_bucket_name,
                file.filename,
                ExtraArgs={"ContentType": file.content_type}
            )
            uploaded_files.append(file.filename)
        except NoCredentialsError:
            raise HTTPException(status_code=403, detail="AWS credentials not found")
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Could not upload file: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    
    return {"message": "Files uploaded successfully", "filenames": uploaded_files}

@app.post("/load-and-process-pdfs")
async def load_and_process_pdfs():
    try:
        # Assuming you have a script that processes files after they're uploaded to S3
        subprocess.run(["python", "./rag-data-loader/rag_load_and_process.py"], check=True)
        return {"message": "PDFs loaded and processed successfully"}
    except subprocess.CalledProcessError as e:
        return {"error": "Failed to execute script"}

# Edit this to add the chain you want to add
add_routes(app, final_chain, path="/rag")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
