import os
import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Get Supabase URL and anon key from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

security = HTTPBearer()

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify the JWT token from Supabase"""
    token = credentials.credentials
    try:
        # Use Supabase client to validate the token
        # The Supabase Auth getUser method validates the JWT and returns user data
        response = supabase.auth.get_user(token)
        
        # If we got here, the token is valid
        user_data = response.user
        
        # Return user info from the token
        return {
            "sub": user_data.id,
            "email": user_data.email,
            "user_metadata": user_data.user_metadata,
            "access_token": token
        }
    
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")