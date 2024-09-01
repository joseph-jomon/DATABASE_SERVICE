Yes, that's correct. The explanation and the implementation provided relate specifically to functions that you want to use as dependencies in FastAPI routes. 

### Key Points to Clarify:

1. **Dependency Functions**:
   - In FastAPI, functions that are used as dependencies (via `Depends`) need to be structured in a way that FastAPI can properly handle and inject them into your route handlers.
   - When using `Depends`, FastAPI expects the function to return a value that it can inject into the route handler as an argument. These dependency functions can also access shared application state or resources using mechanisms like the `Request` object.

2. **Regular Functions**:
   - Functions that are not used as dependencies can be defined and used normally without needing to worry about FastAPI’s dependency injection system.
   - Regular functions don't need to follow the specific patterns required for dependency injection and can directly use objects or variables passed to them in the standard Python way.

### Example of a Dependency Function:

If you want a function to be used as a dependency in a FastAPI route, you might write it like this:

```python
from fastapi import Request, Depends

def get_smtp_server(request: Request) -> SMTPClient:
    smtp_server = request.app.state.smtp_server
    smtp_port = request.app.state.smtp_port
    smtp_client = SMTPClient(smtp_server=smtp_server, port=smtp_port)
    return smtp_client
```

This function can then be used as a dependency in a route like this:

```python
@app.post("/send-email/")
async def send_email(
    smtp_client: SMTPClient = Depends(get_smtp_server),  # Dependency Injection
    recipient: str,
    content: str
):
    smtp_client.send_email(recipient=recipient, content=content)
    return {"status": "Email sent"}
```

### Example of a Regular Function:

A regular function that isn’t used as a dependency might look like this:

```python
def format_email(content: str, recipient: str) -> str:
    return f"To: {recipient}\n\n{content}"
```

This function can be used normally within your code:

```python
formatted_content = format_email(content="Hello, World!", recipient="user@example.com")
print(formatted_content)
```

### Summary:
- **Dependency Functions**: These are functions designed to be injected into FastAPI routes using the `Depends` function. They often interact with `Request` or `app.state` to retrieve shared resources or configurations.
- **Regular Functions**: These are standard Python functions that you use normally within your application. They don't interact with FastAPI's dependency injection system and are used directly in your code.

The distinction is important because the way you write and structure dependency functions needs to align with FastAPI’s expectations, while regular functions don’t have such constraints.