import yaml
import os

def translate_recursive(data, translation_map):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Translate key if possible
            new_k = translation_map.get(k, k)
            new_dict[new_k] = translate_recursive(v, translation_map)
        return new_dict
    elif isinstance(data, list):
        return [translate_recursive(item, translation_map) for item in data]
    elif isinstance(data, str):
        return translation_map.get(data, data)
    else:
        return data

translation_map = {
    "股票": "Equity",
    "国内股票": "CN Equity",
    "美国股票": "US Equity",
    "公司美股": "Employer Stock",
    "港股": "HK Equity",
    "新兴市场股票": "Emerging Markets",
    "固定收益": "Fixed Income",
    "国内政府债券": "CN Govt Bonds",
    "美国政府债券": "US Govt Bonds",
    "企业债券": "Corporate Bonds",
    "货币市场": "Money Market",
    "银行理财": "Bank Products",
    "商品": "Commodities",
    "黄金": "Gold",
    "另类投资": "Alternative",
    "加密货币": "Crypto",
    "创业投资": "Venture Capital",
    "房地产": "Real Estate",
    "住宅地产": "Residential RE",
    "商业地产": "Commercial RE",
    "保险": "Insurance",
    "人寿保险": "Life Insurance",
    "健康保险": "Health Insurance",
    "现金": "Cash",
    "成长型": "Growth",
    "保守型": "Conservative",
    "均衡型": "Balanced",
    "进取型": "Aggressive",
    "高收益债券": "High Yield Bonds",
    "其他贵金属": "Other Precious Metals",
    "能源": "Energy",
    "农产品": "Agriculture",
    "活期存款": "Current Deposit",
    "定期存款": "Time Deposit",
    "房地产信托": "REITs",
    "风险投资": "Venture Capital",
    
    # Tier descriptions
    "第一梯队 (底仓/价值型)": "Tier 1 (Core/Value)",
    "第二梯队 (辅助/分散)": "Tier 2 (Diversification)",
    "第三梯队 (交易/择时)": "Tier 3 (Trading)",
    
    # Asset Identifiers (Strings that might be in lists)
    "投资资产": "Investable Assets",
    "固定资产": "Fixed Assets",
    "存款": "Deposit",
    "房产": "Real Estate",
    "基金": "Funds",
    "理财": "Wealth Management",
}

# Add reverse mapping for specific existing English keys that shouldn't change?
# No, if data is already English, get(data, data) returns data.

source_file = 'config/asset_taxonomy.yaml'
target_file = 'config/locales/asset_taxonomy.en.yaml'

with open(source_file, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

translated_data = translate_recursive(data, translation_map)

# Special handling for default_expectations keys which might not be covered if they are composed strings?
# The map covers "CN Equity", "US Equity" etc.
# But keys in default_expectations: "CN Equity", "HK ETF", etc. are already English or covered.

with open(target_file, 'w', encoding='utf-8') as f:
    yaml.dump(translated_data, f, allow_unicode=True, sort_keys=False)

print(f"Generated {target_file}")
