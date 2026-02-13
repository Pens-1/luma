import asyncio
import os
import sys

# パスを通す
sys.path.append("/app")
from app.services.aider_evolver import run_aider_evolution

async def test_loop():
    target_file = "app/broken_code.py"
    
    # 1. Create a broken file
    print(f"🔥 Creating broken file: {target_file}")
    with open(target_file, "w") as f:
        f.write("def foo()\n    print('Syntax Error!')") # Missing colon
        
    # 2. Run evolution
    print("🚀 Starting evolution loop...")
    instruction = "Fix the syntax error in app/broken_code.py. It is missing a colon."
    result = await run_aider_evolution(instruction, target_file)
    
    # 3. Check result
    print("\n--- Evolution Result ---")
    print(result)
    
    print(f"\n--- Content of {target_file} ---")
    with open(target_file, "r") as f:
        content = f.read()
        print(content)
        
    # Final Check
    try:
        compile(content, target_file, "exec")
        print("\n✅ Final Syntax Check: PASSED")
    except SyntaxError:
        print("\n❌ Final Syntax Check: FAILED")

if __name__ == "__main__":
    asyncio.run(test_loop())
