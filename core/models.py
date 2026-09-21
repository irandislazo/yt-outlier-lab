# core/models.py
"""
Modelos SQLAlchemy — Tablas de la base de datos.
"""
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float,
    DateTime, Boolean, Text, Index
)
from core.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id               = Column(String,  primary_key=True)
    title            = Column(String,  nullable=False, default="")
    handle           = Column(String,  nullable=True)
    description      = Column(Text,    nullable=True)
    thumbnail_url    = Column(String,  nullable=True)
    subscriber_count = Column(Integer, default=0)
    video_count      = Column(Integer, default=0)
    view_count       = Column(Integer, default=0)
    country          = Column(String,  nullable=True)
    category         = Column(String,  nullable=True)
    language         = Column(String,  nullable=True)
    is_own_channel   = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow)
    last_ingested_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "handle": self.handle or "",
            "thumbnail_url": self.thumbnail_url or "",
            "subscriber_count": self.subscriber_count or 0,
            "video_count": self.video_count or 0,
            "view_count": self.view_count or 0,
            "country": self.country or "",
            "category": self.category or "",
            "language": self.language or "",
            "is_own_channel": self.is_own_channel,
        }


class Video(Base):
    __tablename__ = "videos"

    id               = Column(String,  primary_key=True)
    channel_id       = Column(String,  nullable=False, index=True)
    channel_title    = Column(String,  nullable=True)
    title            = Column(String,  nullable=False, default="")
    description      = Column(Text,    nullable=True)
    published_at     = Column(DateTime, nullable=True)
    thumbnail_url    = Column(String,  nullable=True)
    duration_seconds = Column(Integer, default=0)
    tags             = Column(Text,    nullable=True)
    view_count       = Column(Integer, default=0)
    like_count       = Column(Integer, default=0)
    comment_count    = Column(Integer, default=0)
    outlier_score    = Column(Float,   default=0.0)
    views_per_hour   = Column(Float,   default=0.0)
    views_per_sub    = Column(Float,   default=0.0)
    topic_cluster    = Column(Integer, nullable=True)
    category         = Column(String,  nullable=True)
    language         = Column(String,  nullable=True)
    thumb_has_face   = Column(Boolean, nullable=True)
    thumb_dominant_color = Column(String, nullable=True)
    thumb_brightness = Column(Float,   nullable=True)
    thumb_text_detected  = Column(Boolean, nullable=True)
    # ── CAMPOS NUEVOS ────────────────────────────────────────
    category_label   = Column(String,  nullable=True)
    is_favorite      = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_video_channel",   "channel_id"),
        Index("idx_video_published", "published_at"),
        Index("idx_video_outlier",   "outlier_score"),
        Index("idx_video_cluster",   "topic_cluster"),
        Index("idx_video_category", "category_label"),
        Index("idx_video_favorite", "is_favorite"),
    )

    def to_dict(self):
        return {
            "id":               self.id,
            "channel_id":       self.channel_id,
            "channel_title":    self.channel_title or "",
            "title":            self.title,
            "published_at":     self.published_at.strftime("%Y-%m-%d") if self.published_at else "",
            "thumbnail_url":    self.thumbnail_url or "",
            "duration_seconds": self.duration_seconds or 0,
            "view_count":       self.view_count or 0,
            "like_count":       self.like_count or 0,
            "comment_count":    self.comment_count or 0,
            "outlier_score":    round(self.outlier_score or 0, 2),
            "views_per_hour":   round(self.views_per_hour or 0, 1),
            "views_per_sub":    round(self.views_per_sub or 0, 4),
            "category":         self.category or "",
            "category_label":   self.category_label or "",
            "is_favorite":      bool(self.is_favorite),
            "yt_url":           f"https://youtube.com/watch?v={self.id}",
        }
    
class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    video_id       = Column(String,  nullable=False, index=True)
    snapshot_at    = Column(DateTime, default=datetime.utcnow)
    view_count     = Column(Integer, default=0)
    like_count     = Column(Integer, default=0)
    comment_count  = Column(Integer, default=0)
    is_own_channel = Column(Boolean, default=False)


class TopicCluster(Base):
    __tablename__ = "topic_clusters"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    label             = Column(String,  nullable=False)
    keywords          = Column(Text,    nullable=True)
    video_count       = Column(Integer, default=0)
    avg_outlier_score = Column(Float,   default=0.0)
    outlier_count     = Column(Integer, default=0)
    demand_score      = Column(Float,   default=0.0)
    saturation_score  = Column(Float,   default=0.0)
    opportunity_score = Column(Float,   default=0.0)
    created_at        = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        kw = []
        try:
            kw = json.loads(self.keywords or "[]")
        except Exception:
            pass
        return {
            "id":                self.id,
            "label":             self.label,
            "keywords":          kw,
            "video_count":       self.video_count,
            "avg_outlier_score": round(self.avg_outlier_score or 0, 2),
            "outlier_count":     self.outlier_count,
            "demand_score":      round(self.demand_score or 0, 2),
            "saturation_score":  round(self.saturation_score or 0, 2),
            "opportunity_score": round(self.opportunity_score or 0, 4),
        }


class IdeaNote(Base):
    __tablename__ = "idea_notes"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    title                 = Column(String,  nullable=False)
    angle                 = Column(Text,    nullable=True)
    inspired_by_video_id  = Column(String,  nullable=True)
    cluster_id            = Column(Integer, nullable=True)
    status                = Column(String,  default="idea")
    priority              = Column(Integer, default=0)
    notes                 = Column(Text,    nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":        self.id,
            "title":     self.title,
            "angle":     self.angle or "",
            "status":    self.status,
            "priority":  self.priority,
            "notes":     self.notes or "",
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "inspired_by_video_id": self.inspired_by_video_id or "",
        }


class QuotaLog(Base):
    __tablename__ = "quota_log"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    endpoint   = Column(String,  nullable=False)
    units_used = Column(Integer, default=1)
    called_at  = Column(DateTime, default=datetime.utcnow)
    success    = Column(Boolean, default=True)

    @staticmethod
    def get_used_today(session) -> int:
        from datetime import date
        today = datetime.utcnow().date()
        rows = session.query(QuotaLog).filter(
            QuotaLog.called_at >= datetime(today.year, today.month, today.day)
        ).all()
        return sum(r.units_used for r in rows)