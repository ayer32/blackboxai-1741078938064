=======
[Previous imports...]
from rbac_manager import (
    RBACManager,
    Role,
    Permission,
    User,
    get_current_active_user,
    require_permission
)
from face_verification import FaceVerificationSystem
=======

# Initialize components
[Previous initializations...]
rbac_manager = RBACManager(
    mongodb_url=os.getenv("MONGODB_URL", "mongodb://localhost:27017"),
    jwt_secret=os.getenv("JWT_SECRET", "your-secret-key")
)
face_verification = FaceVerificationSystem()

# Additional Models
class FaceRegistrationRequest(BaseModel):
    image_data: str
    user_id: str

class FaceVerificationRequest(BaseModel):
    image_data: str
    user_id: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    roles: List[Role]

class UserUpdate(BaseModel):
    roles: Optional[List[Role]]
    metadata: Optional[Dict[str, Any]]

class LoginRequest(BaseModel):
    username: str
    password: str

# User Management endpoints
@app.post("/api/auth/register")
@require_permission(Permission.MANAGE_USERS)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Register a new user"""
    try:
        user = await rbac_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            roles=user_data.roles
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    user = await rbac_manager.authenticate_user(
        request.username,
        request.password
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = rbac_manager.create_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/users/me")
async def get_current_user(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return current_user

@app.get("/api/users")
@require_permission(Permission.VIEW_USERS)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[Role] = None,
    current_user: User = Depends(get_current_active_user)
):
    """List users"""
    return await rbac_manager.list_users(skip, limit, role)

@app.put("/api/users/{user_id}")
@require_permission(Permission.MANAGE_USERS)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user"""
    if user_data.roles:
        user = await rbac_manager.update_user_roles(
            user_id,
            user_data.roles,
            current_user
        )
    
    if user_data.metadata:
        user = await rbac_manager.update_user_metadata(
            user_id,
            user_data.metadata
        )
    
    return user

@app.delete("/api/users/{user_id}")
@require_permission(Permission.MANAGE_USERS)
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate user"""
    success = await rbac_manager.deactivate_user(user_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"}

# Update existing endpoints with RBAC

@app.post("/api/speech-to-text")
@require_permission(Permission.USE_VOICE)
async def speech_to_text(
    audio: UploadFile = File(...),
    voice_id: Optional[str] = None,
    voice_settings: Optional[VoiceSettings] = None,
    source_lang: Optional[str] = "en",
    current_user: User = Depends(get_current_active_user)
):
    """Convert speech to text with RBAC"""
    [Previous implementation...]

@app.post("/api/face/register")
@require_permission(Permission.USE_FACE)
async def register_face(
    request: FaceRegistrationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Register a new face for biometric authentication"""
    try:
        # Validate user has permission to register face for the given user_id
        if current_user.id != request.user_id and not current_user.has_permission(Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to register face for other users"
            )

        result = face_verification.register_face(
            image_data=request.image_data,
            user_id=request.user_id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result["error"]
            )

        return {
            "status": "success",
            "message": result["message"]
        }

    except Exception as e:
        logger.error(f"Face registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Face registration failed: {str(e)}"
        )

@app.post("/api/face/verify")
@require_permission(Permission.USE_FACE)
async def verify_face(
    request: FaceVerificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Verify face for biometric authentication"""
    try:
        # Validate user has permission to verify face for the given user_id
        if current_user.id != request.user_id and not current_user.has_permission(Permission.MANAGE_USERS):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to verify face for other users"
            )

        result = face_verification.verify_face(
            image_data=request.image_data,
            user_id=request.user_id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=401,
                detail=result["error"]
            )

        return {
            "status": "success",
            "message": result["message"],
            "confidence": result.get("confidence", 1.0)
        }

    except Exception as e:
        logger.error(f"Face verification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Face verification failed: {str(e)}"
        )

@app.post("/api/process-command")
@require_permission(Permission.USE_AI)
async def process_command(
    text_request: TextRequest,
    voice_id: Optional[str] = None,
    voice_settings: Optional[VoiceSettings] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Process command with RBAC"""
    [Previous implementation...]

@app.post("/api/workflows/execute")
@require_permission(Permission.USE_AUTOMATION)
async def execute_workflow(
    execution: WorkflowExecute,
    current_user: User = Depends(get_current_active_user)
):
    """Execute workflow with RBAC"""
    [Previous implementation...]

@app.post("/api/plugins/{plugin_name}/enable")
@require_permission(Permission.MANAGE_PLUGINS)
async def enable_plugin(
    plugin_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Enable plugin with RBAC"""
    [Previous implementation...]

# System management endpoints
@app.get("/api/system/status")
@require_permission(Permission.VIEW_SYSTEM)
async def get_system_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get system status"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "nlu": "running",
            "voice": "running",
            "face": "running"
        }
    }

@app.post("/api/system/maintenance")
@require_permission(Permission.MANAGE_SYSTEM)
async def trigger_maintenance(
    current_user: User = Depends(get_current_active_user)
):
    """Trigger system maintenance"""
    # Add maintenance logic here
    return {"status": "maintenance scheduled"}

[Rest of the previous main.py content...]

# Startup event
@app.on_event("startup")
async def startup_event():
    await rbac_manager.initialize()
    [Previous startup code...]
