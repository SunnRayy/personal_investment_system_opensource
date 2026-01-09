"""
Taxonomy Manager Module for Performance Attribution

This module provides centralized asset categorization logic that maps raw portfolio
holdings to standardized benchmark categories for performance attribution analysis.

It uses the unified asset_taxonomy.yaml configuration file for all classification needs.
"""

import pandas as pd
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from src.database import get_session
from src.database.logic_models import RiskProfile, TargetAllocation, Tag, ClassificationRule
from src.logic_layer.auto_tagger import AutoTagger

class TaxonomyManager:
    """
    Maps raw asset holdings to benchmark categories for performance attribution.
    
    This class provides centralized asset classification using the unified
    asset_taxonomy.yaml configuration file.
    """
    
    def __init__(self, config_path: Optional[str] = None, use_database: bool = True, locale: str = 'en'):
        """
        Initialize the TaxonomyManager.
        
        Args:
            config_path: Path to the asset_taxonomy.yaml file.
                        If None, uses default config directory and LocalizedConfigLoader.
            use_database: If True, attempts to load rules from the database.
            locale: Locale for loading configuration (default: 'en').
        """
        self.logger = logging.getLogger(__name__)
        self.locale = locale
        self.use_database = use_database
        self.db_rules = []
        
        # Set up paths and load config
        if config_path:
            self.config_path = Path(config_path)
            self.config = self._load_config()
        else:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
            
            # Use LocalizedConfigLoader
            try:
                from src.localization.config_loader import LocalizedConfigLoader
                loader = LocalizedConfigLoader(str(config_dir), locale)
                self.config = loader.load('asset_taxonomy')
                self.config_path = Path(loader.config_dir) # Just for reference
                self.logger.info(f"Loaded asset taxonomy config for locale: {locale}")
            except Exception as e:
                self.logger.warning(f"Failed to load localized config: {e}. Falling back to default.")
                self.config_path = config_dir / "asset_taxonomy.yaml"
                self.config = self._load_config()
        
        # Load Database Rules
        if self.use_database:
            self._load_db_rules()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the asset taxonomy configuration (legacy/fallback)."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"Loaded asset taxonomy config from {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load config from {self.config_path}: {e}")
            raise

    def _load_db_rules(self):
        """Load classification rules from the database."""
        try:
            from src.database import get_session, ClassificationRule
            from src.logic_layer.auto_tagger import AutoTagger
            
            session = get_session()
            # We only care about "Asset Class" taxonomy for now to match legacy behavior
            # But actually, the rules define the tag.
            # We will load all active rules.
            self.tagger = AutoTagger(session)
            self.db_rules = self.tagger.rules
            self.logger.info(f"Loaded {len(self.db_rules)} rules from database")
            
        except Exception as e:
            self.logger.warning(f"Failed to load rules from database: {e}. Falling back to YAML.")
            self.use_database = False

    def get_asset_classification(self, asset_name: str, asset_type: str = 'Unknown') -> Tuple[Optional[str], Optional[str]]:
        """
        Get the asset classification (sub-class, top-level).
        Tries DB rules first, then falls back to YAML asset_mapping.
        Only uses Asset Class taxonomy (ID 1), not Asset Tier (ID 2).

        Returns:
            Tuple of (sub_class, top_level_class)
        """
        ASSET_CLASS_TAXONOMY_ID = 1  # Only consider Asset Class rules

        # Try database rules first
        if self.use_database and self.db_rules:
            # Create dummy asset for matching
            class DummyAsset:
                def __init__(self, name, type_):
                    self.asset_name = name
                    self.asset_id = name
                    self.asset_type = type_

            dummy = DummyAsset(asset_name, asset_type)

            for rule in self.db_rules:
                # Only consider Asset Class taxonomy rules
                if rule.taxonomy_id != ASSET_CLASS_TAXONOMY_ID:
                    continue

                if self.tagger._matches(rule, dummy):
                    if rule.tag:
                        sub_class = rule.tag.name
                        top_level = None
                        if rule.tag.parent:
                            top_level = rule.tag.parent.name
                        elif rule.tag.is_top_level:
                            top_level = rule.tag.name
                        return sub_class, top_level

        # Fallback to YAML asset_mapping
        sub_class = self._get_asset_sub_class_yaml(asset_name)
        if sub_class and sub_class != 'Other':
            # Map sub-class to top-level class using sub_classes config
            top_level = self._get_top_level_for_subclass(sub_class)
            return sub_class, top_level

        return None, None

    def _get_top_level_for_subclass(self, sub_class: str) -> Optional[str]:
        """Map a sub-class to its top-level class using config."""
        sub_classes = self.config.get('sub_classes', {})
        for top_level, subs in sub_classes.items():
            if sub_class in subs:
                return top_level
        return None

    def get_asset_tag(self, asset_name: str, asset_type: str = 'Unknown') -> Optional[str]:
        """
        Get the raw asset tag (sub-class) for a given asset name and type.
        """
        sub_class, _ = self.get_asset_classification(asset_name, asset_type)
        if sub_class:
            return sub_class
        
        # Fallback to YAML logic
        return self._get_asset_sub_class_yaml(asset_name)

    def get_benchmark_category_for_asset(self, asset_name: str) -> Optional[str]:
        """
        Get the benchmark category (Top Level Class) for a given asset name.
        """
        # Try DB first
        sub_class, top_level = self.get_asset_classification(asset_name)
        
        if top_level:
            return top_level
            
        # If we have a sub-class from DB but no top-level (e.g. unmapped hierarchy in DB),
        # or if we didn't find anything in DB, fall back to YAML mapping.
        
        if not sub_class:
            sub_class = self._get_asset_sub_class_yaml(asset_name)
            
        if sub_class:
            # Use the benchmark_mapping to get the benchmark category
            benchmark_mapping = self.config.get('benchmark_mapping', {})
            return benchmark_mapping.get(sub_class, sub_class)
        
        return None

    def _get_category_from_db(self, asset_name: str, asset_type: str = 'Unknown') -> Optional[str]:
        """Deprecated: Use get_asset_classification instead."""
        sub, _ = self.get_asset_classification(asset_name, asset_type)
        return sub

    def get_risk_profile_allocations(self, profile_name: str) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Get target allocations and sub-category weights for a risk profile from DB.
        Falls back to YAML if DB lookup fails or is disabled.
        
        Note: This is for Asset Class allocations only. Tier tags (Taxonomy ID 2) are excluded.
        
        Returns:
            Tuple of (target_allocations, sub_category_weights)
        """
        TIER_TAXONOMY_ID = 2  # Asset Tier taxonomy - exclude from Asset Class reports
        
        if self.use_database:
            session = get_session()
            try:
                profile = session.query(RiskProfile).filter_by(name=profile_name).first()
                if profile:
                    top_level_targets = {}
                    sub_category_targets = {}  # Parent -> {Child: Weight}

                    # 1. First Pass: Organize allocations by hierarchy
                    for alloc in profile.allocations:
                        tag = alloc.tag
                        weight = alloc.target_weight
                        
                        # Skip Tier tags - they are managed separately
                        if tag.taxonomy_id == TIER_TAXONOMY_ID:
                            continue
                        
                        if tag.is_top_level or not tag.parent:
                            # Explicit Top Level Target
                            top_level_targets[tag.name] = weight
                        else:
                            # Sub-class Target
                            parent_name = tag.parent.name
                            if parent_name not in sub_category_targets:
                                sub_category_targets[parent_name] = {}
                            sub_category_targets[parent_name][tag.name] = weight

                    # 2. Second Pass: Determine Final Top Level Targets
                    sub_classes_config = self.config.get('sub_classes', {})
                    
                    final_target_allocations = top_level_targets.copy()
                    sub_category_weights = {} # For return (normalized)

                    for parent_name, children in sub_category_targets.items():
                        children_sum = sum(children.values())
                        
                        # Check if Parent is Self-Referential (e.g. Cash -> Cash)
                        # If so, the Top Level Allocation represents the "Self" portion, not the Total.
                        is_self_ref = parent_name in sub_classes_config.get(parent_name, [])
                        
                        if is_self_ref and parent_name in top_level_targets:
                            # Add the "Self" portion to the children sum
                            self_weight = top_level_targets[parent_name]
                            children_sum += self_weight
                            
                            # Add to children map for normalization
                            children[parent_name] = self_weight
                            
                        # For Pure Containers (e.g. Stock), the Top Level Allocation is redundant (Total).
                        # We overwrite it with the granular Sum of Children.
                        
                        final_target_allocations[parent_name] = children_sum
                        
                        # Verify normalization
                        if children_sum > 0:
                            sub_category_weights[parent_name] = {}
                            for child_name, abs_weight in children.items():
                                sub_category_weights[parent_name][child_name] = abs_weight / children_sum

                    return final_target_allocations, sub_category_weights
                else:
                    self.logger.warning(f"Profile '{profile_name}' not found in DB. Falling back to YAML.")
            except Exception as e:
                self.logger.error(f"Error loading allocations from DB: {e}")
            finally:
                session.close()
        
        # Fallback to YAML
        self.logger.info(f"Using YAML fallback for profile: {profile_name}")
        target_allocations = self.config.get('risk_profiles', {}).get(profile_name, {})
        sub_category_weights = self.config.get('sub_category_weights', {})
        return target_allocations, sub_category_weights

    def get_active_risk_profile_name(self) -> str:
        """
        Get the name of the currently active risk profile from DB.
        Returns '成长型' as default if no active profile found or DB disabled.
        """
        default_profile = '成长型'
        
        if self.use_database:
            session = get_session()
            try:
                profile = session.query(RiskProfile).filter_by(is_active=True).first()
                if profile:
                    return profile.name
            except Exception as e:
                self.logger.error(f"Error fetching active profile: {e}")
            finally:
                session.close()
                
        return default_profile

    def _get_asset_sub_class_yaml(self, asset_name: str) -> str:
        """
        Legacy YAML-based classification logic.
        """
        try:
            # Handle empty or whitespace-only input
            if not asset_name or not asset_name.strip():
                return 'Other'
            
            # Get the mapping from config
            mapping = self.config.get('asset_mapping', {})
            
            if not mapping:
                return 'Other'
            
            # Priority 1: Exact match (case-sensitive)
            if asset_name in mapping:
                return mapping[asset_name]
            
            # Priority 2: Case-insensitive exact match
            asset_name_lower = asset_name.lower()
            for key, value in mapping.items():
                if key.lower() == asset_name_lower:
                    return value
            
            # Priority 3: Regex-based pattern matching
            import re
            for pattern, asset_class in mapping.items():
                try:
                    regex_chars = r'[\.\*\+\?\[\]\(\)\{\}\|\\\^\$]'
                    if re.search(regex_chars, pattern):
                        if asset_name and re.search(pattern, asset_name, re.IGNORECASE):
                            return asset_class
                    else:
                        escaped_pattern = re.escape(pattern)
                        if re.search(escaped_pattern, asset_name, re.IGNORECASE):
                            return asset_class
                except Exception:
                    continue
            
            # Priority 4: Substring matching as final fallback
            for key, value in mapping.items():
                key_lower = key.lower()
                try:
                    if key_lower in asset_name_lower or asset_name_lower in key_lower:
                        return value
                except Exception:
                    continue
            
            return 'Other'
            
        except Exception as e:
            self.logger.error(f"Error in asset classification for '{asset_name}': {e}")
            return 'Other'
    
    def categorize_assets(self, portfolio_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict, List]:
        """
        Categorize assets in portfolio data to benchmark categories.
        
        Args:
            portfolio_data: DataFrame with asset columns and values
            
        Returns:
            Tuple of (result_df, categorization_results, unmapped_assets)
        """
        result_df = portfolio_data.copy()
        
        # Get asset columns (exclude non-asset columns)
        asset_columns = self._identify_asset_columns(result_df)
        
        # Initialize categorization results
        categorization_results = {}
        unmapped_assets = []
        
        self.logger.info(f"Categorizing {len(asset_columns)} asset columns")
        
        for col in asset_columns:
            try:
                # Get asset value (handle pandas Series issues)
                value = self._extract_asset_value(result_df, col)
                
                if value <= 0.01:  # minimum threshold
                    continue  # Skip assets below threshold
                
                # Apply categorization logic
                category = self.get_benchmark_category_for_asset(col)
                
                if category:
                    categorization_results[col] = {
                        'category': category,
                        'value': value
                    }
                    self.logger.debug(f"✅ {col}: {value:,.0f} → {category}")
                else:
                    unmapped_assets.append((col, value))
                    self.logger.warning(f"❓ {col}: {value:,.0f} → UNMAPPED")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing {col}: {e}")
                continue
        
        # Handle unmapped assets
        if unmapped_assets:
            self.logger.warning(f"⚠️ {len(unmapped_assets)} unmapped assets:")
            for name, value in unmapped_assets:
                self.logger.warning(f"   {name}: {value:,.0f} CNY")
        
        # Create asset class mapping for the dataframe
        asset_class_mapping = {col: info['category'] for col, info in categorization_results.items()}
        
        # Add Asset_Class column
        result_df['Asset_Class'] = result_df.index.map(
            lambda idx: [asset_class_mapping.get(col, 'Unknown') for col in result_df.columns if col in asset_class_mapping]
        )
        
        return result_df, categorization_results, unmapped_assets
    
    def get_portfolio_breakdown(self, portfolio_data: pd.DataFrame) -> Tuple[Dict[str, float], Dict[str, List[Tuple[str, float]]], float]:
        """
        Get portfolio breakdown by benchmark categories.
        
        Args:
            portfolio_data: DataFrame with asset holdings
            
        Returns:
            Tuple of (category_totals, category_details, total_assets)
        """
        asset_columns = self._identify_asset_columns(portfolio_data)
        
        # Initialize category totals
        benchmark_categories = self.config.get('benchmark_categories', [])
        category_totals = {category: 0.0 for category in benchmark_categories}
        category_details = {category: [] for category in benchmark_categories}
        
        total_assets = 0.0
        processed_assets = []
        
        self.logger.info(f"Processing {len(asset_columns)} asset columns for breakdown")
        
        for col in asset_columns:
            try:
                value = self._extract_asset_value(portfolio_data, col)
                if value <= 0.01:
                    continue
                
                # Only add valid values to total
                if not pd.isna(value) and value > 0:
                    total_assets += value
                    processed_assets.append((col, value))
                    
                    category = self.get_benchmark_category_for_asset(col)
                    
                    if category and category in category_totals:
                        category_totals[category] += value
                        category_details[category].append((col, value))
                        self.logger.debug(f"✅ {col}: {value:,.0f} → {category}")
                    else:
                        self.logger.warning(f"❓ {col}: {value:,.0f} → UNMAPPED")
                else:
                    self.logger.warning(f"⚠️ Skipping {col}: invalid value {value}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {col} for breakdown: {e}")
                continue
        
        self.logger.info(f"Processed {len(processed_assets)} valid assets, total value: {total_assets:,.0f}")
        
        return category_totals, category_details, total_assets
    
    def _identify_asset_columns(self, df: pd.DataFrame) -> List[str]:
        """Identify asset columns in the dataframe."""
        # Get excluded assets from special_categories (like insurance)
        special_categories = self.config.get('special_categories', [])
        excluded_assets = []
        
        # Also exclude known problematic assets
        asset_mapping = self.config.get('asset_mapping', {})
        for asset_name, sub_class in asset_mapping.items():
            if sub_class in special_categories:
                excluded_assets.append(asset_name)
        
        # Add hardcoded exclusions
        excluded_assets.extend(['Asset_Total_CNY', 'Asset_Invest_Private_Equity_Investment_A'])
        
        # Look for Asset_ prefix columns, excluding totals and problematic assets
        asset_columns = [
            col for col in df.columns 
            if col.startswith('Asset_') and col not in excluded_assets
        ]
        
        return asset_columns
    
    def _extract_asset_value(self, df: pd.DataFrame, column: str) -> float:
        """Extract numeric value from asset column, handling pandas Series issues."""
        try:
            if len(df) == 0:
                return 0.0
            
            value = df[column].iloc[0]
            
            # Handle pandas Series objects (nested Series issue)
            if hasattr(value, 'iloc'):
                value = value.iloc[0]
            elif hasattr(value, 'values') and len(value.values) > 0:
                value = value.values[0]
            elif pd.isna(value):
                return 0.0
            
            # Convert to float, handling any remaining string/object issues
            try:
                return float(value)
            except (ValueError, TypeError):
                self.logger.warning(f"Could not convert {column} value '{value}' to float, returning 0")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error extracting value from {column}: {e}")
            return 0.0
    
    def get_benchmark_categories(self) -> List[str]:
        """Get list of benchmark categories."""
        return self.config.get('benchmark_categories', [])
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """
        Validate the configuration for completeness and consistency.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check required sections
        required_sections = ['benchmark_categories', 'benchmark_mapping', 'asset_mapping']
        for section in required_sections:
            if section not in self.config:
                issues.append(f"Missing required section: {section}")
        
        # Check benchmark categories are consistent
        benchmark_categories = set(self.config.get('benchmark_categories', []))
        mapping_categories = set(self.config.get('benchmark_mapping', {}).values())
        
        unmapped_categories = mapping_categories - benchmark_categories
        
        if unmapped_categories:
            issues.append(f"Categories in benchmark_mapping but not in benchmark_categories: {unmapped_categories}")
        
        return len(issues) == 0, issues
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get a summary of the current mapping configuration."""
        return {
            'benchmark_categories': self.config.get('benchmark_categories', []),
            'asset_mappings_count': len(self.config.get('asset_mapping', {})),
            'benchmark_mappings_count': len(self.config.get('benchmark_mapping', {})),
            'pattern_rules_count': len(self.config.get('pattern_mapping', {})),
            'sub_classes_count': sum(len(sub_list) for sub_list in self.config.get('sub_classes', {}).values())
        }

    # ========================================
    # ASSET TIER CLASSIFICATION METHODS
    # ========================================

    def get_tier_config(self) -> Dict[str, Dict]:
        """
        Get tier definitions. Prioritizes DB if available.
        
        Returns:
            Dict with tier_key -> {name, description, color}
        """
        if self.use_database:
            session = get_session()
            try:
                # Find Asset Tier taxonomy (Fixed ID 2 or by name)
                from src.database import Taxonomy, Tag
                taxonomy = session.query(Taxonomy).filter_by(name="Asset Tier").first()
                if taxonomy:
                    tier_config = {}
                    for tag in taxonomy.tags:
                        # Map tag name to a key like 'tier_1_core' for backward compatibility if possible,
                        # or just use the name/slug. 
                        # For now, let's map by name to the known keys.
                        key = tag.name
                        if "第一" in tag.name or "Core" in tag.name: key = 'tier_1_core'
                        elif "第二" in tag.name or "Diversification" in tag.name: key = 'tier_2_diversification'
                        elif "第三" in tag.name or "Trading" in tag.name: key = 'tier_3_trading'
                        
                        tier_config[key] = {
                            'name': tag.name,
                            'description': tag.description,
                            'color': tag.color or 'blue'
                        }
                    if tier_config:
                        return tier_config
            except Exception as e:
                self.logger.warning(f"Error fetching tier config from DB: {e}")
            finally:
                session.close()

        return self.config.get('asset_tiers', {})

    def get_tier_targets(self) -> Dict[str, float]:
        """
        Get target allocations per tier. Prioritizes active Risk Profile in DB.
        """
        if self.use_database:
            profile_name = self.get_active_risk_profile_name()
            targets, _ = self.get_risk_profile_allocations(profile_name)
            
            # Filter targets for Tier tags
            tier_targets = {}
            for name, weight in targets.items():
                if "梯队" in name or "Tier" in name:
                    # Map to keys
                    if "第一" in name: tier_targets['tier_1_core'] = weight
                    elif "第二" in name: tier_targets['tier_2_diversification'] = weight
                    elif "第三" in name: tier_targets['tier_3_trading'] = weight
                    else: tier_targets[name] = weight # Fallback
            
            if tier_targets:
                return tier_targets

        return self.config.get('tier_target_allocations', {
            'tier_1_core': 0.50,
            'tier_2_diversification': 0.35,
            'tier_3_trading': 0.15
        })

    def get_tier_mapping(self) -> Dict[str, str]:
        """
        Get asset-to-tier mapping from config.
        
        Returns:
            Dict with asset_id/asset_name -> tier_key
        """
        return self.config.get('asset_tier_mapping', {})

    def get_asset_tier(self, asset_id: str, asset_name: str = None) -> str:
        """
        Get the tier for an asset. Prioritizes Database associations.
        """
        if self.use_database:
            session = get_session()
            try:
                from src.database import Asset, AssetTag, Tag, Taxonomy
                # 1. Check direct Asset-Tag associations for "Asset Tier" taxonomy
                query = session.query(Tag.name).join(AssetTag).join(Asset)\
                    .join(Taxonomy).filter(Taxonomy.name == "Asset Tier")\
                    .filter(Asset.asset_id == asset_id)
                
                res = query.first()
                if res:
                    name = res[0]
                    if "第一" in name: return 'tier_1_core'
                    if "第二" in name: return 'tier_2_diversification'
                    if "第三" in name: return 'tier_3_trading'
                    return name

                # 2. Check rules in DB
                for rule in self.db_rules:
                    # Only consider rules for Asset Tier taxonomy
                    if rule.taxonomy and rule.taxonomy.name == "Asset Tier":
                        # Create dummy asset for matching
                        class Dummy: pass
                        d = Dummy()
                        d.asset_id = asset_id
                        d.asset_name = asset_name
                        d.asset_type = 'Unknown'
                        
                        if self.tagger._matches(rule, d):
                            name = rule.tag.name
                            if "第一" in name: return 'tier_1_core'
                            if "第二" in name: return 'tier_2_diversification'
                            if "第三" in name: return 'tier_3_trading'
                            return name
            except Exception as e:
                self.logger.warning(f"Error classifying tier from DB: {e}")
            finally:
                session.close()

        # Fallback to YAML
        tier_mapping = self.get_tier_mapping()
        
        # 1. Exact Asset ID match
        # Handle 'N/A' or None asset_ids gracefully
        if asset_id and str(asset_id).upper() != 'N/A':
            # Normalize ID: strip, handle leading zeros for funds
            norm_id = str(asset_id).strip()
            if norm_id in tier_mapping:
                return tier_mapping[norm_id]
            
            # Try with leading zeros for fund codes (if numeric)
            if norm_id.isdigit() and len(norm_id) < 6:
                padded_id = norm_id.zfill(6)
                if padded_id in tier_mapping:
                    return tier_mapping[padded_id]
        
        # 2. Exact Asset Name match
        if asset_name:
            name_key = str(asset_name).strip()
            # Try exact match first
            if name_key in tier_mapping:
                return tier_mapping[name_key]
            
            # Case-insensitive match check 
            # (Note: keys in yaml are loaded as strings, we might want to pre-process them for speed,
            # but for <100 rules iteration is fine)
            lower_name = name_key.lower()
            for k, v in tier_mapping.items():
                if k.lower() == lower_name:
                    return v
                    
            # 3. Regex/Substring match
            regex_rules = self.config.get('asset_tier_mapping_rules', [])
            if regex_rules:
                import re
                for rule in regex_rules:
                    pattern = rule.get('pattern', '')
                    tier = rule.get('tier', '')
                    if pattern and tier:
                        # Case-insensitive regex search
                        if re.search(pattern, name_key, re.IGNORECASE):
                            return tier
        
        return 'unclassified'

    def get_tier_display_name(self, tier_key: str) -> str:
        """
        Get the display name for a tier.
        
        Args:
            tier_key: Internal tier key (e.g., 'tier_1_core')
            
        Returns:
            Display name in Chinese (e.g., '第一梯队 (底仓/价值型)')
        """
        tier_config = self.get_tier_config()
        if tier_key in tier_config:
            return tier_config[tier_key].get('name', tier_key)
        return tier_key

    def classify_holdings_by_tier(self, holdings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add tier classification columns to holdings DataFrame.
        
        Args:
            holdings_df: DataFrame with Asset_ID and/or Asset_Name columns
            
        Returns:
            DataFrame with added 'Asset_Tier' and 'Asset_Tier_Name' columns
        """
        result_df = holdings_df.copy()
        
        # Determine columns to use for matching
        id_col = 'Asset_ID' if 'Asset_ID' in result_df.columns else None
        name_col = 'Asset_Name' if 'Asset_Name' in result_df.columns else None
        
        if not id_col and not name_col:
            self.logger.warning("No Asset_ID or Asset_Name column found for tier classification")
            result_df['Asset_Tier'] = 'unclassified'
            result_df['Asset_Tier_Name'] = 'Unclassified'
            return result_df
        
        # Classify each holding
        tiers = []
        tier_names = []
        
        for _, row in result_df.iterrows():
            asset_id = str(row.get(id_col, '')) if id_col else ''
            asset_name = str(row.get(name_col, '')) if name_col else ''
            
            tier = self.get_asset_tier(asset_id, asset_name)
            tier_name = self.get_tier_display_name(tier)
            
            tiers.append(tier)
            tier_names.append(tier_name)
        
        result_df['Asset_Tier'] = tiers
        result_df['Asset_Tier_Name'] = tier_names
        
        return result_df



# Convenience function for easy import
def create_taxonomy_manager(config_path: Optional[str] = None, locale: str = 'en') -> TaxonomyManager:
    """Create and return a TaxonomyManager instance."""
    return TaxonomyManager(config_path, locale=locale)
