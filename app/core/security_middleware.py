from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from typing import Dict, List
from collections import defaultdict, deque
import re


class RateLimitMiddleware:
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
        self.clients: Dict[str, deque] = defaultdict(deque)

    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        while self.clients[client_ip] and self.clients[client_ip][0] <= now - self.period:
            self.clients[client_ip].popleft()
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Add current request
        self.clients[client_ip].append(now)
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
        return response


class InputValidationMiddleware:
    def __init__(self):
        # Common XSS patterns
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)', re.IGNORECASE),
            re.compile(r'(\b(OR|AND)\s+\d+\s*=\s*\d+)', re.IGNORECASE),
            re.compile(r'[\'";]', re.IGNORECASE),
        ]

    def validate_string(self, value: str) -> bool:
        """Check if string contains malicious patterns"""
        if not isinstance(value, str):
            return True
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(value):
                return False
        
        # Check for SQL injection patterns (basic)
        for pattern in self.sql_patterns:
            if pattern.search(value):
                return False
        
        return True

    def sanitize_dict(self, data: dict) -> dict:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                if not self.validate_string(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid input detected in field: {key}"
                    )
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_dict(item) if isinstance(item, dict)
                    else item if self.validate_string(str(item))
                    else None
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def __call__(self, request: Request, call_next):
        # Skip validation for certain endpoints
        skip_paths = ['/docs', '/redoc', '/openapi.json', '/health']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if not self.validate_string(value):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid input detected in query parameter: {key}"
                )
        
        # For POST/PUT requests, validate JSON body
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body:
                        import json
                        data = json.loads(body)
                        if isinstance(data, dict):
                            self.sanitize_dict(data)
                except json.JSONDecodeError:
                    pass  # Let FastAPI handle JSON parsing errors
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid input detected in request body"
                    )
        
        response = await call_next(request)
        return response


# File upload security
class FileUploadValidator:
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.txt', '.jpg', '.jpeg', '.png'
    }
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # File signature validation
    FILE_SIGNATURES = {
        b'\x25\x50\x44\x46': '.pdf',
        b'\xD0\xCF\x11\xE0': '.doc',  # MS Office
        b'\x50\x4B\x03\x04': '.docx',  # ZIP-based (docx, xlsx)
        b'\xFF\xD8\xFF': '.jpg',
        b'\x89\x50\x4E\x47': '.png',
    }

    @classmethod
    def validate_file(cls, filename: str, content: bytes) -> tuple[bool, str]:
        """Validate uploaded file"""
        
        # Check file extension
        file_ext = '.' + filename.split('.')[-1].lower()
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed"
        
        # Check file size
        if len(content) > cls.MAX_FILE_SIZE:
            return False, "File size exceeds maximum allowed size"
        
        # Check file signature
        if len(content) >= 4:
            signature_match = False
            for signature, ext in cls.FILE_SIGNATURES.items():
                if content.startswith(signature):
                    signature_match = True
                    break
            
            # For now, we'll be lenient with signature checking
            # In production, you might want stricter validation
        
        # Additional security checks
        if cls._contains_malicious_content(content):
            return False, "File contains potentially malicious content"
        
        return True, "File is valid"

    @classmethod
    def _contains_malicious_content(cls, content: bytes) -> bool:
        """Check for malicious content in file"""
        
        # Check for embedded scripts in text-based files
        try:
            text_content = content.decode('utf-8', errors='ignore').lower()
            malicious_patterns = [
                '<script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
                'eval(', 'document.cookie', 'window.location'
            ]
            
            for pattern in malicious_patterns:
                if pattern in text_content:
                    return True
        except:
            pass  # Binary files will fail decode, which is fine
        
        return False


# Password strength validation
class PasswordValidator:
    MIN_LENGTH = 8
    
    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', 'qwerty', 'admin', 'letmein',
            'welcome', 'monkey', '1234567890'
        ]
        
        if password.lower() in weak_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors