from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import subprocess
from . import models, crud
from .database import SessionLocal, engine
from typing import Optional
from langserve import add_routes

from app.rag_chain import final_chain

# Secret key to encode JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI instance
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://rag.genaiexpertise.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
s3_bucket_name = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client('s3')

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer instance for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    full_name: Optional[str] = None


class UserInDB(User):
    hashed_password: str


@app.post("/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(SessionLocal)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/register")
async def register_user(username: str, password: str, full_name: Optional[str] = None, db: Session = Depends(SessionLocal)):
    user = crud.get_user_by_username(db, username)
    if user:
        raise HTTPException(status_code=400, detail="User already registered")
    crud.create_user(db, username, password, full_name)
    return {"message": "User registered successfully"}



@app.post("/auth/login")
async def login(username: str, password: str, db: Session = Depends(SessionLocal)):
    user = authenticate_user
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
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
async def load_and_process_pdfs(current_user: User = Depends(get_current_user)):
    try:
        # Assuming you have a script that processes files after they're uploaded to S3
        subprocess.run(["python", "./rag-data-loader/rag_load_and_process.py"], check=True)
        return {"message": "PDFs loaded and processed successfully"}
    except subprocess.CalledProcessError as e:
        return {"error": "Failed to execute script"}


# Initialize the database
@app.on_event("startup")
async def startup():
    models.Base.metadata.create_all(bind=engine)


# Edit this to add the chain you want to add
add_routes(app, final_chain, path="/rag")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
