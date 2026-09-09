from datetime import datetime
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from geoalchemy2 import Geometry

class Base(DeclarativeBase):
    pass

class Vessel(Base):
    __tablename__ = "vessels"

    vessel_id = Column(String(64), primary_key=True)
    mmsi = Column(String(32), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    vessel_type = Column(String(64), nullable=True)
    flag = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    tracks = relationship("AISTrack", back_populates="vessel", cascade="all, delete-orphan")
    correlations = relationship("CorrelationResult", back_populates="vessel", cascade="all, delete-orphan")
    risk_scores = relationship("RiskAssessment", back_populates="vessel", cascade="all, delete-orphan")

class AISTrack(Base):
    __tablename__ = "ais_tracks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vessel_id = Column(String(64), ForeignKey("vessels.vessel_id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    latitude = Column(Double, nullable=False)
    longitude = Column(Double, nullable=False)
    sog = Column(Double, nullable=True)
    cog = Column(Double, nullable=True)
    heading = Column(Double, nullable=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    vessel = relationship("Vessel", back_populates="tracks")

    __table_args__ = (
        UniqueConstraint("vessel_id", "timestamp", name="uq_vessel_track_time"),
    )

class SpillIncident(Base):
    __tablename__ = "spill_incidents"

    spill_id = Column(String(64), primary_key=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    footprint = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    area_sq_km = Column(Double, nullable=True)
    confidence = Column(Double, nullable=True)
    status = Column(String(32), default="active")
    source_sensor = Column(String(64), nullable=True)
    source_image_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    detections = relationship("Detection", back_populates="spill", cascade="all, delete-orphan")
    correlations = relationship("CorrelationResult", back_populates="spill", cascade="all, delete-orphan")
    risk_scores = relationship("RiskAssessment", back_populates="spill", cascade="all, delete-orphan")

class Detection(Base):
    __tablename__ = "detections"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    spill_id = Column(String(64), ForeignKey("spill_incidents.spill_id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(64), nullable=False)
    model_version = Column(String(32), nullable=True)
    spill_detected = Column(Boolean, nullable=False)
    confidence = Column(Double, nullable=True)
    spill_area_pct = Column(Double, nullable=True)
    inference_time_ms = Column(Double, nullable=True)
    boundary_coords = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    spill = relationship("SpillIncident", back_populates="detections")

class CorrelationResult(Base):
    __tablename__ = "correlation_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    spill_id = Column(String(64), ForeignKey("spill_incidents.spill_id", ondelete="CASCADE"), nullable=False)
    vessel_id = Column(String(64), ForeignKey("vessels.vessel_id", ondelete="CASCADE"), nullable=False)
    spatial_score = Column(Double, nullable=False)
    temporal_score = Column(Double, nullable=False)
    min_distance_km = Column(Double, nullable=True)
    matched = Column(Boolean, default=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    spill = relationship("SpillIncident", back_populates="correlations")
    vessel = relationship("Vessel", back_populates="correlations")

    __table_args__ = (
        UniqueConstraint("spill_id", "vessel_id", name="uq_spill_vessel_correlation"),
    )

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    spill_id = Column(String(64), ForeignKey("spill_incidents.spill_id", ondelete="CASCADE"), nullable=False)
    vessel_id = Column(String(64), ForeignKey("vessels.vessel_id", ondelete="CASCADE"), nullable=False)
    risk_score = Column(Double, nullable=False)
    risk_level = Column(String(32), nullable=False)
    spatial_correlation = Column(Double, default=0.0)
    temporal_correlation = Column(Double, default=0.0)
    ais_anomaly_count = Column(Integer, default=0)
    sudden_speed_changes = Column(Integer, default=0)
    sharp_course_changes = Column(Integer, default=0)
    factors = Column(JSONB, nullable=True)
    rationale = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    spill = relationship("SpillIncident", back_populates="risk_scores")
    vessel = relationship("Vessel", back_populates="risk_scores")

    __table_args__ = (
        UniqueConstraint("spill_id", "vessel_id", name="uq_spill_vessel_risk"),
    )