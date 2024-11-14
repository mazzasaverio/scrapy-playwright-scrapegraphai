# 2. Update src/crawler/models/config_url_log_model.py

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ConfigState(str, Enum):
    """Enumeration of possible config processing states."""
    PENDING = 'pending'           
    RUNNING = 'running'           
    COMPLETED = 'completed'       
    FAILED = 'failed'            
    PARTIALLY_COMPLETED = 'partially_completed'

class ConfigUrlLog(BaseModel):
    """Model representing a log entry for a configuration URL."""
    
    id: Optional[int] = None
    url: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=255)
    config_state: ConfigState = ConfigState.PENDING
    
    # Metriche di elaborazione
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_duration: Optional[float] = None
    
    # Contatori
    total_urls_found: int = Field(default=0, ge=0)
    target_urls_found: int = Field(default=0, ge=0)
    seed_urls_found: int = Field(default=0, ge=0)
    failed_urls: int = Field(default=0, ge=0)
    
    # Configuration
    url_type: int = Field(..., ge=0, le=4)
    max_depth: int = Field(..., ge=0)
    reached_depth: int = Field(default=0, ge=0)
    target_patterns: Optional[List[str]] = None
    seed_pattern: Optional[str] = None
    
    # Error handling
    error_message: Optional[str] = None
    warning_messages: Optional[List[str]] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True