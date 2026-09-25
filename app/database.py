import os
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db")

# SQLite connection args for multi-threaded FastAPI access
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(100), nullable=False)
    intensity = Column(String(50), nullable=False)
    schedule = Column(Integer, default=7)

    plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    original_plan = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True, default=None)

    user = relationship("User", back_populates="plans")


# Initialize tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency helper for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str) -> User:
    """Creates or updates a user in the database."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(id=user_id).first()
        if existing:
            existing.name = name
            existing.age = age
            existing.weight = weight
            existing.goal = goal
            existing.intensity = intensity
            db.commit()
            db.refresh(existing)
            return existing
        else:
            user = User(
                id=user_id,
                name=name,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity,
                schedule=7,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
    finally:
        db.close()


def save_plan(user_id: int, plan: str) -> WorkoutPlan:
    """Stores or updates the original plan in the database."""
    db = SessionLocal()
    try:
        workout = db.query(WorkoutPlan).filter_by(user_id=user_id).first()
        if workout:
            workout.original_plan = plan
            db.commit()
            db.refresh(workout)
            return workout
        else:
            workout = WorkoutPlan(user_id=user_id, original_plan=plan)
            db.add(workout)
            db.commit()
            db.refresh(workout)
            return workout
    finally:
        db.close()


def update_plan(user_id: int, updated_text: str) -> Optional[WorkoutPlan]:
    """Updates the workout plan based on feedback."""
    db = SessionLocal()
    try:
        workout = db.query(WorkoutPlan).filter_by(user_id=user_id).first()
        if workout:
            workout.updated_plan = updated_text
            db.commit()
            db.refresh(workout)
            return workout
        return None
    finally:
        db.close()


def get_original_plan(user_id: int) -> Optional[str]:
    """Fetches the original workout plan for a user."""
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        return plan.original_plan if plan else None
    finally:
        db.close()


def get_user(user_id: int) -> Optional[User]:
    """Fetches a user record by ID."""
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def get_all_users() -> List[User]:
    """Fetches all users from the database."""
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()


def get_all_plans() -> List[WorkoutPlan]:
    """Fetches all workout plans from the database."""
    db = SessionLocal()
    try:
        return db.query(WorkoutPlan).all()
    finally:
        db.close()


def delete_user(user_id: int) -> bool:
    """Deletes a user and associated plans."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    finally:
        db.close()
