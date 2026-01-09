"""
Product Recommender Module

Maps capital allocation recommendations to specific investment products
with detailed execution guidance.

Author: Personal Investment System
Created: 2025-10-14
"""

import yaml
import logging
from typing import Dict, List, Optional
from pathlib import Path


class ProductRecommender:
    """
    Recommends specific investment products for capital allocation.
    
    Features:
    - Maps asset classes to specific products (ETFs, funds, bank wealth products)
    - Provides execution steps and rationale
    - Adapts recommendations based on allocation size
    - Prioritizes existing products vs new suggestions
    """
    
    def __init__(self, config_path: str = 'config/product_recommendations.yaml'):
        """
        Initialize ProductRecommender.
        
        Args:
            config_path: Path to product recommendations YAML config
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load product recommendations configuration."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.error(f"Product config not found: {self.config_path}")
                return {}
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            self.logger.info(f"Loaded product recommendations config from {self.config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading product config: {e}", exc_info=True)
            return {}
    
    def recommend_products(
        self,
        asset_class: str,
        allocation_amount: float,
        sub_class: Optional[str] = None,
        current_holdings: Optional[List[str]] = None
    ) -> Dict:
        """
        Recommend specific products for an allocation amount.
        
        Args:
            asset_class: Asset class name (e.g., 'Fixed Income', 'Equity', 'Commodities')
            allocation_amount: Amount to allocate (CNY)
            sub_class: Optional sub-class (e.g., 'US Equity', 'China Equity')
            current_holdings: List of current holdings to avoid duplication
            
        Returns:
            Dictionary with product recommendations and execution details
        """
        try:
            # Normalize asset class name
            asset_class_key = self._normalize_asset_class(asset_class)
            
            if asset_class_key not in self.config:
                self.logger.warning(f"No product config for asset class: {asset_class}")
                return {
                    'products': [],
                    'allocation_strategy': 'No specific products configured',
                    'total_products': 0
                }
            
            # Get allocation strategy based on amount
            strategy = self._get_allocation_strategy(allocation_amount)
            
            # Get products for this asset class
            products = self._get_products_for_class(
                asset_class_key,
                allocation_amount,
                sub_class,
                current_holdings,
                strategy
            )
            
            return {
                'products': products,
                'allocation_strategy': strategy['principle'],
                'total_products': len(products),
                'allocation_amount': allocation_amount,
                'asset_class': asset_class
            }
            
        except Exception as e:
            self.logger.error(f"Error recommending products: {e}", exc_info=True)
            return {'products': [], 'allocation_strategy': 'Error', 'total_products': 0}
    
    def _normalize_asset_class(self, asset_class: str) -> str:
        """Normalize asset class name to config key."""
        mappings = {
            '固定收益': 'fixed_income',
            'fixed income': 'fixed_income',
            'fixed_income': 'fixed_income',
            '商品': 'commodities',
            'commodities': 'commodities',
            'commodity': 'commodities',
            '股票': 'equities',
            'equity': 'equities',
            'equities': 'equities',
            '另类投资': 'alternative',
            'alternative': 'alternative',
            'alternatives': 'alternative'
        }
        
        normalized = mappings.get(asset_class.lower())
        if not normalized:
            self.logger.warning(f"Unknown asset class: {asset_class}, defaulting to key")
            return asset_class.lower().replace(' ', '_')
        return normalized
    
    def _get_allocation_strategy(self, amount: float) -> Dict:
        """Get allocation strategy based on allocation amount."""
        strategy_config = self.config.get('allocation_strategy', {})
        
        if amount < 50000:
            return strategy_config.get('small_allocation', {
                'principle': '集中配置，优先高流动性',
                'product_count': 1
            })
        elif amount < 200000:
            return strategy_config.get('medium_allocation', {
                'principle': '适度分散，2-3个产品',
                'product_count': 2
            })
        else:
            return strategy_config.get('large_allocation', {
                'principle': '充分分散，3-5个产品',
                'product_count': 3
            })
    
    def _get_products_for_class(
        self,
        asset_class_key: str,
        allocation_amount: float,
        sub_class: Optional[str],
        current_holdings: Optional[List[str]],
        strategy: Dict
    ) -> List[Dict]:
        """Get product recommendations for asset class."""
        class_config = self.config.get(asset_class_key, {})
        
        # For equities, check sub-class
        if asset_class_key == 'equities' and sub_class:
            sub_class_key = 'us_equity' if 'us' in sub_class.lower() else 'china_equity'
            class_config = class_config.get(sub_class_key, class_config)
        
        # Get existing and new products
        existing_products = class_config.get('existing_products', [])
        new_suggestions = class_config.get('new_suggestions', [])
        
        # Filter out products already held
        current_holdings = current_holdings or []
        new_suggestions_filtered = [
            p for p in new_suggestions
            if not any(holding in p.get('name', '') or holding in p.get('ticker', '') or holding in p.get('code', '')
                      for holding in current_holdings)
        ]
        
        # Determine how many products to recommend
        target_count = strategy.get('product_count', 2)
        
        # Prioritize high-priority new suggestions
        high_priority = [p for p in new_suggestions_filtered if p.get('priority') == 'high']
        medium_priority = [p for p in new_suggestions_filtered if p.get('priority') == 'medium']
        
        # Build recommendation list
        products = []
        
        # Add high priority suggestions first
        for product in high_priority[:target_count]:
            products.append(self._format_product(product, allocation_amount, len(products) + 1))
        
        # Fill remaining slots with medium priority
        remaining_slots = target_count - len(products)
        for product in medium_priority[:remaining_slots]:
            products.append(self._format_product(product, allocation_amount, len(products) + 1))
        
        # If still need more, add existing products as context
        if len(products) < target_count and existing_products:
            for product in existing_products[:1]:  # Just one existing as reference
                products.append(self._format_product(product, allocation_amount, len(products) + 1, is_existing=True))
        
        return products
    
    def _format_product(self, product: Dict, total_allocation: float, sequence: int, is_existing: bool = False) -> Dict:
        """Format product into recommendation structure."""
        # Calculate suggested allocation for this product
        # For simplicity, divide equally among products
        suggested_amount = total_allocation  # Will be divided in UI if multiple products
        
        return {
            'sequence': sequence,
            'name': product.get('name', 'Unknown'),
            'code': product.get('code', product.get('ticker', '')),
            'type': product.get('type', ''),
            'yield_estimate': product.get('yield_estimate', 'N/A'),
            'risk_level': product.get('risk_level', '中风险'),
            'liquidity': product.get('liquidity', 'N/A'),
            'min_investment': product.get('min_investment', 'N/A'),
            'rationale': product.get('rationale', ''),
            'suggested_amount': suggested_amount,
            'execution_steps': product.get('execution_steps', []),
            'is_existing': is_existing,
            'priority': product.get('priority', 'medium')
        }
    
    def get_execution_priority_guide(self) -> Dict:
        """Get execution priority guidelines."""
        return self.config.get('execution_priority', {})
    
    def get_risk_warnings(self) -> Dict:
        """Get risk warnings for products."""
        return self.config.get('risk_warnings', {})


if __name__ == '__main__':
    # Test the ProductRecommender
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    
    logging.basicConfig(level=logging.INFO)
    
    recommender = ProductRecommender()
    
    # Test Case 1: Small Fixed Income allocation
    print("\n" + "="*80)
    print("TEST 1: Small Fixed Income Allocation (¥30,000)")
    print("="*80)
    result = recommender.recommend_products(
        asset_class='固定收益',
        allocation_amount=30000,
        current_holdings=['BND', '招商双债增强债券']
    )
    print(f"Strategy: {result['allocation_strategy']}")
    print(f"Total Products: {result['total_products']}")
    for product in result['products']:
        print(f"\n{product['sequence']}. {product['name']} ({product['code']})")
        print(f"   Type: {product['type']}")
        print(f"   Yield: {product['yield_estimate']}")
        print(f"   Risk: {product['risk_level']}")
        print(f"   Rationale: {product['rationale']}")
    
    # Test Case 2: Large Equity allocation
    print("\n" + "="*80)
    print("TEST 2: Large US Equity Allocation (¥250,000)")
    print("="*80)
    result = recommender.recommend_products(
        asset_class='股票',
        allocation_amount=250000,
        sub_class='US Equity',
        current_holdings=['QQQ', 'VOO']
    )
    print(f"Strategy: {result['allocation_strategy']}")
    print(f"Total Products: {result['total_products']}")
    for product in result['products']:
        print(f"\n{product['sequence']}. {product['name']} ({product['code']})")
        print(f"   Type: {product['type']}")
        print(f"   Rationale: {product['rationale']}")
        if product['execution_steps']:
            print(f"   Execution Steps:")
            for step in product['execution_steps']:
                print(f"     - {step}")
    
    # Test Case 3: Commodities allocation
    print("\n" + "="*80)
    print("TEST 3: Commodities Allocation (¥50,000)")
    print("="*80)
    result = recommender.recommend_products(
        asset_class='商品',
        allocation_amount=50000,
        current_holdings=['Paper_Gold']
    )
    print(f"Strategy: {result['allocation_strategy']}")
    print(f"Total Products: {result['total_products']}")
    for product in result['products']:
        print(f"\n{product['sequence']}. {product['name']} ({product['code']})")
        print(f"   Liquidity: {product['liquidity']}")
        print(f"   Rationale: {product['rationale']}")
