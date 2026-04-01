import os
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://rgcmxhvomatsdapcgdzd.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def diagnostic():
    print(f"--- NEBULA DIAGNOSTIC 2.0 ---")
    
    if not SUPABASE_KEY:
        print("ERROR: SUPABASE_KEY is missing!")
        return

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Client initialized.")
        
        # 1. Test Select
        try:
            response = supabase.table("users").select("*").limit(1).execute()
            print("✓ Table 'users' exists and is readable.")
        except Exception as e:
            print(f"✗ Table 'users' check failed: {e}")
            return

        # 2. Test Insert (Speculative check for RLS)
        print("\nChecking for Write Permissions (RLS)...")
        try:
            # We try a dummy insert that we expect to fail or succeed
            # If it fails with a 403 or similar, it's definitely RLS
            test_user = {"username": "test_connection_probe", "password_hash": "test", "name": "test"}
            supabase.table("users").insert(test_user).execute()
            print("✓ Write permission verified! (Wait, why did the app fail then?)")
            # Cleanup
            supabase.table("users").delete().eq("username", "test_connection_probe").execute()
        except Exception as e:
            error_str = str(e)
            print(f"✗ Write failed: {error_str}")
            if "new row violates row-level security" in error_str.lower() or "403" in error_str:
                print("\n🚨 CAUSE DETECTED: Row Level Security (RLS) is blocking the write.")
                print("FIX: Run the 'DISABLE RLS' command in your Supabase SQL Editor (see below).")
            else:
                print(f"\nPOSSIBLE CAUSE: {error_str}")

    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == "__main__":
    diagnostic()
