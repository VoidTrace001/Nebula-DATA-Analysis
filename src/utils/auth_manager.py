import os
import bcrypt
import logging
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables (for local dev)
load_dotenv()

def get_supabase() -> Client:
    """Initializes the Supabase client with robust secret handling."""
    
    # 1. Attempt to pull from Streamlit Secrets
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    
    # 2. Fallback to Environment Variables (Local)
    if not url: url = os.getenv("SUPABASE_URL")
    if not key: key = os.getenv("SUPABASE_KEY")
    
    # 3. Last Resort: Hardcoded URL default (Your Project ID)
    if not url: url = "https://rgcmxhvomatsdapcgdzd.supabase.co"

    # Validate presence
    if not url or not key:
        st.error("🌌 **NEBULA OS | CONNECTION ERROR**")
        st.info("Supabase credentials are not detected in Streamlit Secrets or .env file.")
        st.code("""# Streamlit Cloud Secrets Format:
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key" """, language="toml")
        return None
        
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {e}")
        return None

def register_user(username, password, name=""):
    """Registers a new entity into Supabase 'users' table."""
    supabase = get_supabase()
    if not supabase: return False, "System offline: Link to Supabase failed."

    # Check if user exists
    try:
        response = supabase.table("users").select("username").eq("username", username).execute()
        if response.data:
            return False, "Entity already exists in neural stream."
    except Exception as e:
        logging.error(f"Supabase Select Error: {e}")
        return False, "Network latency: Could not verify identity existence."

    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Insert new user
    try:
        supabase.table("users").insert({
            "username": username,
            "password_hash": hashed,
            "name": name if name else username
        }).execute()
        return True, "Identity synthesized successfully."
    except Exception as e:
        logging.error(f"Supabase Insert Error: {e}")
        return False, "Synthesis failed: Supabase write error."

def authenticate_user(username, password):
    """Verifies quantum ID and cypher key against Supabase."""
    supabase = get_supabase()
    if not supabase: return False, "System offline: Link to Supabase failed."

    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        if not response.data:
            return False, "Quantum ID not found."
        
        user = response.data[0]
        hashed = user['password_hash'].encode('utf-8')
        
        if bcrypt.checkpw(password.encode('utf-8'), hashed):
            return True, user['name']
        
        return False, "Cypher key mismatch."
    except Exception as e:
        logging.error(f"Supabase Auth Error: {e}")
        return False, "Network latency: Authentication protocol failed."
