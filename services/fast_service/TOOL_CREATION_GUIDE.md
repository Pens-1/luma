# New Tool Creation Guide

You are an expert engineer. When asked to create a new tool, you MUST follow this guide to ensure it is correctly integrated into the system.

## 1. Create the Tool Module

Create a new Python file in `tools/<tool_name>.py`.

**Template:**

```python
# tools/<tool_name>.py
from typing import Any, Dict

async def run(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Description of what the tool does.

    Args:
        param1 (str): Description...
        param2 (int): Description...

    Returns:
        Dict[str, Any]: The result of the operation.
    """
    # ... implementation ...
    return {"result": "some_value", "status": "success"}
```

## 2. Register the Tool in `main.py` (MANDATORY)

You **MUST** edit `services/fast_service/main.py` (or just `main.py`) to register the new tool. **If you do not register it, the tool will NOT work.**

**Step 2a: Import the module**

```python
from tools import weather, forecast, <tool_name>  # <--- Add your tool here
```

**Step 2b: Add `ToolInfo` to `get_tools`**
Add a new `ToolInfo` entry in the `get_tools` function.

```python
        ToolInfo(
            name="<tool_name>",
            description="Short description of the tool",
            parameters={
                "param1": "str (description)",
                "param2": "int (description)"
            }
        ),
```

**Step 2c: Add Execution Logic to `execute_tool`**
Add an `elif` block in the `execute_tool` function.

```python
        elif tool_name == "<tool_name>":
            # Extract parameters
            p1 = request.parameters.get("param1")
            p2 = request.parameters.get("param2", 0)

            # Validation (Optional but recommended)
            if not p1:
                 raise HTTPException(status_code=400, detail="Missing 'param1'")

            # Execute
            result = await <tool_name>.run(p1, p2)
```

## 3. Verify

Ensure `main.py` has no syntax errors. The system will automatically reload, but you should double-check your edits.
