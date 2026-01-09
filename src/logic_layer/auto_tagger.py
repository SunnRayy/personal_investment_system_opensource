import re
import logging
from sqlalchemy.orm import Session
from src.database import get_session, ClassificationRule, Asset, AssetTag, Tag

logger = logging.getLogger(__name__)

class AutoTagger:
    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self.rules = []
        self._load_rules()

    def _load_rules(self):
        """Load all active rules from database, ordered by priority."""
        try:
            self.rules = self.session.query(ClassificationRule)\
                .filter_by(is_active=True)\
                .order_by(ClassificationRule.priority.desc())\
                .all()
            logger.info(f"Loaded {len(self.rules)} classification rules")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            self.rules = []

    def tag_asset(self, asset: Asset) -> list[str]:
        """
        Apply rules to a single asset.
        Returns a list of tag names that were applied.
        """
        applied_tags = []
        
        # Pre-fetch existing tags to avoid duplicates
        existing_tag_ids = {at.tag_id for at in self.session.query(AssetTag).filter_by(asset_id=asset.asset_id).all()}
        
        for rule in self.rules:
            if self._matches(rule, asset):
                if rule.tag_id not in existing_tag_ids:
                    self._apply_tag(asset, rule.tag_id)
                    existing_tag_ids.add(rule.tag_id)
                    applied_tags.append(rule.tag.name if rule.tag else str(rule.tag_id))
                    
        return applied_tags

    def _matches(self, rule: ClassificationRule, asset: Asset) -> bool:
        """Check if a rule matches an asset."""
        # Determine the field value to check
        if rule.match_field == 'asset_id':
            value = asset.asset_id
        elif rule.match_field == 'asset_name':
            value = asset.asset_name
        elif rule.match_field == 'asset_type':
            value = asset.asset_type
        else:
            return False

        if not value:
            return False
            
        value = str(value)

        # Check match based on type
        if rule.match_type == 'exact':
            return value == rule.pattern
        elif rule.match_type == 'contains':
            return rule.pattern.lower() in value.lower()
        elif rule.match_type == 'regex':
            try:
                return bool(re.search(rule.pattern, value, re.IGNORECASE))
            except re.error:
                logger.error(f"Invalid regex in rule {rule.id}: {rule.pattern}")
                return False
        
        return False

    def _apply_tag(self, asset: Asset, tag_id: int):
        """Link an asset to a tag and update Asset metadata."""
        try:
            # Create link
            asset_tag = AssetTag(asset_id=asset.asset_id, tag_id=tag_id)
            self.session.add(asset_tag)
            
            # Update Asset columns for backwards compatibility with HoldingsCalculator
            # ONLY if the tag belongs to the legacy "Asset Class" taxonomy (ID 1)
            tag = self.session.query(Tag).get(tag_id)
            if tag and tag.taxonomy_id == 1:
                # Update Sub-class / Type
                asset.asset_subclass = tag.name
                asset.asset_type = tag.name # Often used interchangeably in legacy code
                
                # Update Top-level Class
                if tag.parent:
                    asset.asset_class = tag.parent.name
                elif tag.is_top_level:
                    asset.asset_class = tag.name
                
                logger.info(f"Updated Asset Class metadata for {asset.asset_id}: Class={asset.asset_class}, Sub={asset.asset_subclass}")
            
            # Don't commit here to allow batch processing
        except Exception as e:
            logger.error(f"Error applying tag {tag_id} to {asset.asset_id}: {e}")

    def process_all_assets(self):
        """Run auto-tagging on all assets in the database."""
        try:
            assets = self.session.query(Asset).all()
            count = 0
            for asset in assets:
                tags = self.tag_asset(asset)
                if tags:
                    count += 1
            
            self.session.commit()
            logger.info(f"Auto-tagging complete. Updated {count} assets.")
            return count
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error during batch auto-tagging: {e}")
            return 0
        finally:
            self.session.close()
