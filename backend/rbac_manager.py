from typing import Dict, List, Set, Optional
from enum import Enum
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
import logging

class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"

class Permission(str, Enum):
    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Plugin Management
    MANAGE_PLUGINS = "manage_plugins"
    USE_PLUGINS = "use_plugins"
    
    # System Management
    MANAGE_SYSTEM = "manage_system"
    VIEW_SYSTEM = "view_system"
    
    # Data Access
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    
    # Feature Access
    USE_AI = "use_ai"
    USE_VOICE = "use_voice"
    USE_FACE = "use_face"
    USE_AUTOMATION = "use_automation"

class User(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    roles: List[Role]
    permissions: List[Permission]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime]
    metadata: Dict = {}

class RBACManager:
    def __init__(self, mongodb_url: str, jwt_secret: str):
        self.client = AsyncIOMotorClient(mongodb_url)
        self.db = self.client.krish_ai
        self.jwt_secret = jwt_secret
        self.logger = logging.getLogger("rbac_manager")
        
        # Role hierarchy and default permissions
        self.role_hierarchy = {
            Role.ADMIN: {
                "inherits": [Role.MANAGER, Role.USER, Role.GUEST],
                "permissions": [
                    Permission.MANAGE_USERS,
                    Permission.MANAGE_PLUGINS,
                    Permission.MANAGE_SYSTEM
                ]
            },
            Role.MANAGER: {
                "inherits": [Role.USER, Role.GUEST],
                "permissions": [
                    Permission.VIEW_USERS,
                    Permission.USE_PLUGINS,
                    Permission.VIEW_SYSTEM
                ]
            },
            Role.USER: {
                "inherits": [Role.GUEST],
                "permissions": [
                    Permission.USE_AI,
                    Permission.USE_VOICE,
                    Permission.USE_FACE,
                    Permission.USE_AUTOMATION
                ]
            },
            Role.GUEST: {
                "inherits": [],
                "permissions": [
                    Permission.READ_DATA
                ]
            }
        }

    async def initialize(self):
        """Initialize RBAC system"""
        # Create indexes
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index("email", unique=True)
        
        # Create default admin if none exists
        if not await self.db.users.find_one({"roles": Role.ADMIN}):
            await self.create_user(
                username="admin",
                email="admin@krishai.com",
                password="admin",  # Should be changed immediately
                roles=[Role.ADMIN]
            )

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[Role]
    ) -> User:
        """Create a new user"""
        # Hash password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        
        # Calculate permissions based on roles
        permissions = await self.calculate_permissions(roles)
        
        user = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "roles": roles,
            "permissions": permissions,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "metadata": {}
        }
        
        try:
            result = await self.db.users.insert_one(user)
            user["id"] = str(result.inserted_id)
            return User(**user)
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=400, detail="User creation failed")

    async def calculate_permissions(self, roles: List[Role]) -> List[Permission]:
        """Calculate all permissions for given roles including inherited ones"""
        permissions: Set[Permission] = set()
        
        for role in roles:
            # Add direct permissions
            permissions.update(self.role_hierarchy[role]["permissions"])
            
            # Add inherited permissions
            for inherited_role in self.role_hierarchy[role]["inherits"]:
                permissions.update(self.role_hierarchy[inherited_role]["permissions"])
        
        return list(permissions)

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object"""
        user_doc = await self.db.users.find_one({"username": username})
        if not user_doc:
            return None
            
        if not bcrypt.checkpw(password.encode(), user_doc["hashed_password"]):
            return None
            
        # Update last login
        await self.db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)

    def create_access_token(self, user: User, expires_delta: timedelta = timedelta(hours=24)) -> str:
        """Create JWT access token"""
        expires = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user.id,
            "exp": expires,
            "roles": user.roles,
            "permissions": user.permissions
        }
        
        return jwt.encode(to_encode, self.jwt_secret, algorithm="HS256")

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload["sub"]
            user_doc = await self.db.users.find_one({"_id": user_id})
            if not user_doc:
                raise HTTPException(status_code=401, detail="User not found")
            
            user_doc["id"] = str(user_doc.pop("_id"))
            return User(**user_doc)
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def check_permission(self, user: User, required_permission: Permission) -> bool:
        """Check if user has required permission"""
        return required_permission in user.permissions

    async def update_user_roles(self, user_id: str, roles: List[Role], admin_user: User) -> User:
        """Update user roles (requires admin permission)"""
        if not await self.check_permission(admin_user, Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        permissions = await self.calculate_permissions(roles)
        
        await self.db.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "roles": roles,
                    "permissions": permissions
                }
            }
        )
        
        user_doc = await self.db.users.find_one({"_id": user_id})
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        user_doc = await self.db.users.find_one({"_id": user_id})
        if not user_doc:
            return None
            
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[Role] = None
    ) -> List[User]:
        """List users with optional role filter"""
        query = {}
        if role:
            query["roles"] = role
            
        cursor = self.db.users.find(query).skip(skip).limit(limit)
        users = []
        
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc.pop("_id"))
            users.append(User(**user_doc))
            
        return users

    async def deactivate_user(self, user_id: str, admin_user: User) -> bool:
        """Deactivate user (requires admin permission)"""
        if not await self.check_permission(admin_user, Permission.MANAGE_USERS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        result = await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        return result.modified_count > 0

    async def update_user_metadata(self, user_id: str, metadata: Dict) -> User:
        """Update user metadata"""
        await self.db.users.update_one(
            {"_id": user_id},
            {"$set": {"metadata": metadata}}
        )
        
        user_doc = await self.db.users.find_one({"_id": user_id})
        user_doc["id"] = str(user_doc.pop("_id"))
        return User(**user_doc)

# Dependency for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_active_user(
    rbac: RBACManager,
    token: str = Security(oauth2_scheme)
) -> User:
    """Dependency to get current active user"""
    user = await rbac.get_current_user(token)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    async def permission_dependency(
        current_user: User = Security(get_current_active_user)
    ) -> User:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission {permission} required"
            )
        return current_user
    return permission_dependency
