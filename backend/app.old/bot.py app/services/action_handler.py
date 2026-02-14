import os

def handle_action():
    # Create temporary file before executing
    with open('.evolution_pending', 'w') as f:
        f.write('pending')
    
    # ... rest of action handling logic
    
    # Remove temporary file after execution
    if os.path.exists('.evolution_pending'):
        os.remove('.evolution_pending')
