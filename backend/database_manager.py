from typing import Dict, List, Any, Optional, Union
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import firebase_admin
from firebase_admin import credentials, firestore, db
import asyncpg
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.setup_logging()
        self.initialize_mongodb()
        self.initialize_postgresql()
        self.initialize_firebase()

    def setup_logging(self):
        """Set up logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('database_manager')

    def initialize_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            self.mongodb_client = AsyncIOMotorClient(mongodb_url)
            self.mongodb_db = self.mongodb_client.krish_ai
            self.logger.info("MongoDB initialized successfully")
            self.mongodb_available = True
        except Exception as e:
            self.logger.error(f"MongoDB initialization error: {str(e)}")
            self.mongodb_available = False

    def initialize_postgresql(self):
        """Initialize PostgreSQL connection"""
        try:
            postgres_url = os.getenv(
                "POSTGRES_URL",
                "postgresql+asyncpg://user:password@localhost/krishai"
            )
            self.postgres_engine = create_async_engine(postgres_url)
            self.postgres_session = sessionmaker(
                self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            self.Base = declarative_base()
            self.logger.info("PostgreSQL initialized successfully")
            self.postgresql_available = True
        except Exception as e:
            self.logger.error(f"PostgreSQL initialization error: {str(e)}")
            self.postgresql_available = False

    def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            cred_path = os.getenv("FIREBASE_CREDENTIALS")
            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': os.getenv("FIREBASE_DATABASE_URL")
                })
                self.firestore_db = firestore.client()
                self.realtime_db = db.reference()
                self.logger.info("Firebase initialized successfully")
                self.firebase_available = True
            else:
                self.logger.warning("Firebase credentials not found")
                self.firebase_available = False
        except Exception as e:
            self.logger.error(f"Firebase initialization error: {str(e)}")
            self.firebase_available = False

    # MongoDB Operations
    async def mongodb_insert(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> str:
        """Insert document into MongoDB"""
        try:
            result = await self.mongodb_db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"MongoDB insert error: {str(e)}")
            raise

    async def mongodb_find(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find documents in MongoDB"""
        try:
            cursor = self.mongodb_db[collection].find(query, projection)
            return await cursor.to_list(length=None)
        except Exception as e:
            self.logger.error(f"MongoDB find error: {str(e)}")
            raise

    async def mongodb_update(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """Update documents in MongoDB"""
        try:
            result = await self.mongodb_db[collection].update_many(
                query,
                {'$set': update}
            )
            return result.modified_count
        except Exception as e:
            self.logger.error(f"MongoDB update error: {str(e)}")
            raise

    # PostgreSQL Operations
    async def postgresql_execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute PostgreSQL query"""
        async with self.postgres_session() as session:
            try:
                result = await session.execute(query, params)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                self.logger.error(f"PostgreSQL query error: {str(e)}")
                raise

    async def postgresql_fetch(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data from PostgreSQL"""
        async with self.postgres_session() as session:
            try:
                result = await session.execute(query, params)
                return [dict(row) for row in result]
            except Exception as e:
                self.logger.error(f"PostgreSQL fetch error: {str(e)}")
                raise

    # Firebase Operations
    async def firestore_add(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> str:
        """Add document to Firestore"""
        try:
            doc_ref = self.firestore_db.collection(collection).document()
            doc_ref.set(document)
            return doc_ref.id
        except Exception as e:
            self.logger.error(f"Firestore add error: {str(e)}")
            raise

    async def firestore_get(
        self,
        collection: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get document from Firestore"""
        try:
            doc_ref = self.firestore_db.collection(collection).document(document_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            self.logger.error(f"Firestore get error: {str(e)}")
            raise

    async def firestore_query(
        self,
        collection: str,
        query_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Query Firestore collection"""
        try:
            query = self.firestore_db.collection(collection)
            for field, value in query_params.items():
                query = query.where(field, '==', value)
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            self.logger.error(f"Firestore query error: {str(e)}")
            raise

    async def realtime_db_set(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> None:
        """Set data in Firebase Realtime Database"""
        try:
            self.realtime_db.child(path).set(data)
        except Exception as e:
            self.logger.error(f"Realtime Database set error: {str(e)}")
            raise

    async def realtime_db_get(
        self,
        path: str
    ) -> Optional[Dict[str, Any]]:
        """Get data from Firebase Realtime Database"""
        try:
            return self.realtime_db.child(path).get()
        except Exception as e:
            self.logger.error(f"Realtime Database get error: {str(e)}")
            raise

    # Database Status
    def get_database_status(self) -> Dict[str, bool]:
        """Get status of available databases"""
        return {
            "mongodb": self.mongodb_available,
            "postgresql": self.postgresql_available,
            "firebase": self.firebase_available
        }

    # Database Selection
    def get_preferred_database(self) -> str:
        """Get preferred database based on availability and configuration"""
        if self.firebase_available and os.getenv("PREFERRED_DB") == "firebase":
            return "firebase"
        elif self.postgresql_available and os.getenv("PREFERRED_DB") == "postgresql":
            return "postgresql"
        elif self.mongodb_available:
            return "mongodb"
        else:
            raise Exception("No database available")

    async def execute_query(
        self,
        query: Union[str, Dict[str, Any]],
        database: Optional[str] = None
    ) -> Any:
        """Execute query on preferred or specified database"""
        db = database or self.get_preferred_database()
        
        if db == "mongodb":
            return await self.mongodb_find(
                query.get("collection"),
                query.get("query", {})
            )
        elif db == "postgresql":
            return await self.postgresql_fetch(
                query,
                query.get("params")
            )
        elif db == "firebase":
            return await self.firestore_query(
                query.get("collection"),
                query.get("query", {})
            )
        else:
            raise ValueError(f"Unsupported database: {db}")
