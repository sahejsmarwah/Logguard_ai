"""
demo_crash.py
-------------
A deliberate buggy script to test LogGuard AI.
It has a common mistake: trying to access a dictionary key that doesn't exist
without checking, which raises a KeyError.
"""
import time

def process_data(data):
    # This will crash if 'user_id' is missing
    user_id = data['user_id']
    print(f"Processing user: {user_id}")
    
    # Another potential crash: integer division by zero
    # (LogGuard can fix this too!)
    result = 100 / data.get('divisor', 1)
    print(f"Calculation result: {result}")

if __name__ == "__main__":
    print("🚀 Starting Demo App...")
    
    # Simulate some work
    time.sleep(1)
    
    # Buggy input
    bad_input = {
        "name": "Jane Doe",
        # Missing 'user_id' will cause a KeyError
    }
    
    print("📥 Processing input data...")
    process_data(bad_input)
    
    print("✅ Finished successfully!")
