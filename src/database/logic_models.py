"""
Database models for the Logic Layer (Logic Studio).
Defines structures for classifying assets and configuring calculation strategies.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Taxonomy(Base):
    """
    Defines a classification category (e.g., 'Region', 'Asset Class', 'Sector').
    Acts as a container for Tags.
    """
    __tablename__ = 'taxonomies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="Name of the taxonomy (e.g. Region)")
    description = Column(String(200), comment="Description of what this taxonomy classifies")
    is_hierarchical = Column(Boolean, default=False, comment="Whether tags in this taxonomy can have parents")
    allow_multiple = Column(Boolean, default=False, comment="Whether an asset can have multiple tags from this taxonomy")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tags = relationship("Tag", back_populates="taxonomy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Taxonomy(name='{self.name}')>"

class Tag(Base):
    """
    Specific tags within a taxonomy (e.g., 'US', 'China' within 'Region').
    """
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    taxonomy_id = Column(Integer, ForeignKey('taxonomies.id'), nullable=False)
    name = Column(String(50), nullable=False, comment="Name of the tag (e.g. US)")
    description = Column(String(200))
    color = Column(String(20), default="blue", comment="UI color for the tag")
    parent_id = Column(Integer, ForeignKey('tags.id'), nullable=True, comment="Parent tag ID if hierarchical")
    is_top_level = Column(Boolean, default=False, comment="Whether this is a top-level category")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    taxonomy = relationship("Taxonomy", back_populates="tags")
    parent = relationship("Tag", remote_side=[id], backref="children")
    # asset_associations defined in AssetTag

    def __repr__(self):
        return f"<Tag(name='{self.name}', taxonomy='{self.taxonomy_id}')>"

class AssetTag(Base):
    """
    Link table associating Assets with Tags.
    """
    __tablename__ = 'asset_tags'

    asset_id = Column(String(50), ForeignKey('assets.asset_id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tag = relationship("Tag", backref="asset_associations")
    # asset relationship is usually defined on the Asset model side or backref here if needed

    def __repr__(self):
        return f"<AssetTag(asset='{self.asset_id}', tag='{self.tag_id}')>"

class CalculationStrategy(Base):
    """
    Defines how to calculate metrics for a specific asset.
    Overrides global defaults.
    """
    __tablename__ = 'calculation_strategies'

    asset_id = Column(String(50), ForeignKey('assets.asset_id'), primary_key=True)
    
    # Cost Basis
    cost_basis_method = Column(String(20), default='FIFO', comment="FIFO, LIFO, AvgCost, SpecificLot")
    
    # Currency
    currency_strategy = Column(String(20), default='Spot', comment="Spot (use daily rate), Fixed (use fixed rate), Hedged")
    fixed_currency_rate = Column(Integer, nullable=True, comment="Rate to use if strategy is Fixed")
    
    # Dividends
    dividend_strategy = Column(String(20), default='Cash', comment="Cash, Reinvest")
    
    # Notes
    notes = Column(Text, comment="User notes on why this strategy was chosen")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CalculationStrategy(asset='{self.asset_id}', method='{self.cost_basis_method}')>"

class ClassificationRule(Base):
    __tablename__ = 'classification_rules'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(200))
    
    # The target tag to apply
    taxonomy_id = Column(Integer, ForeignKey('taxonomies.id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=False)
    
    # Matching logic
    match_type = Column(String(20), nullable=False)  # 'exact', 'contains', 'regex'
    match_field = Column(String(50), nullable=False) # 'asset_name', 'asset_id', 'asset_type'
    pattern = Column(String(500), nullable=False)    # The string or regex to match
    
    priority = Column(Integer, default=0)            # Higher number = higher priority
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    taxonomy = relationship("Taxonomy")
    tag = relationship("Tag")

    def __repr__(self):
        return f"<ClassificationRule(name='{self.name}', pattern='{self.pattern}')>"

class RiskProfile(Base):
    """
    Defines a target asset allocation strategy (e.g. 'Growth', 'Balanced').
    """
    __tablename__ = 'risk_profiles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    is_active = Column(Boolean, default=False, comment="Whether this is the currently active profile for the user")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    allocations = relationship("TargetAllocation", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RiskProfile(name='{self.name}')>"

class TargetAllocation(Base):
    """
    Defines the target weight for a specific tag within a risk profile.
    """
    __tablename__ = 'target_allocations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey('risk_profiles.id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=False)
    target_weight = Column(Float, nullable=False, comment="Target weight as a decimal (e.g. 0.2 for 20%)") 
    # Note: Using Float in Python, but SQLite might store as Real. 
    # Wait, existing code uses Float? Let's check imports.
    # The imports in logic_models.py are: Column, Integer, String, Boolean, ForeignKey, DateTime, Text.
    # I need to import Float.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("RiskProfile", back_populates="allocations")
    tag = relationship("Tag")

    def __repr__(self):
        return f"<TargetAllocation(profile='{self.profile_id}', tag='{self.tag_id}', weight='{self.target_weight}')>"
