import os
import bcrypt
import logging
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables (for local dev)
load_dotenv()

# Supabase Configuration
def get_credential(key, default=None):
    try:
        return st.secrets.get(key) or os.getenv(key) or default
    except Exception:
        return os.getenv(key) or default

SUPABASE_URL = get_credential("SUPABASE_URL", "https://rgcmxhvomatsdapcgdzd.supabase.co")
SUPABASE_KEY = get_credential("SUPABASE_KEY")

def get_supabase() -> Client:
    """Initializes the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase credentials missing. Please configure SUPABASE_URL and SUPABASE_KEY.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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
