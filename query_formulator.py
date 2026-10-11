"""
Query formulation module for the SurplusLink Hyperlocal Lead Generation Engine.
Generates targeted SerpApi Google Local search queries to find immediate commercial buyers.
"""

import re
from typing import Dict, List, Optional


class QueryFormulator:
    """
    Formulates targeted Google Local queries based on item name and category
    to discover immediate commercial B2B buyers within a hyperlocal radius.
    """

    # Keyword mapping rules to target specific commercial buyer types
    BUYER_RULES: List[Dict] = [
        # --- Food & Produce ---
        {
            "category_keywords": ["food", "produce", "agriculture", "grocery", "perishable", "farm"],
            "item_keywords": ["tomato", "onion", "potato", "vegetable", "fruit", "lettuce", "apple", "berry", "produce", "salad"],
            "buyer_query": "restaurants catering commercial kitchens food wholesalers",
        },
        {
            "category_keywords": ["food", "bakery"],
            "item_keywords": ["bread", "flour", "yeast", "pastry", "croissant", "cake", "dough", "bakery"],
            "buyer_query": "bakeries cafes catering restaurants commercial kitchen",
        },
        {
            "category_keywords": ["food", "dairy"],
            "item_keywords": ["milk", "cheese", "butter", "dairy", "yogurt", "cream"],
            "buyer_query": "restaurants cafes bakeries commercial kitchens",
        },
        {
            "category_keywords": ["food", "meat", "poultry", "seafood"],
            "item_keywords": ["meat", "chicken", "beef", "pork", "fish", "seafood", "salmon", "shrimp"],
            "buyer_query": "restaurants butcher shops catering commercial kitchens",
        },
        {
            "category_keywords": ["food", "beverage", "grocery"],
            "item_keywords": [],
            "buyer_query": "restaurants catering commercial kitchens wholesale food buyers",
        },

        # --- Construction & Building Materials ---
        {
            "category_keywords": ["construction", "building", "material", "hardware"],
            "item_keywords": ["brick", "cement", "concrete", "sand", "gravel", "aggregate", "mortar"],
            "buyer_query": "building contractors masonry construction suppliers",
        },
        {
            "category_keywords": ["construction", "building", "lumber", "wood"],
            "item_keywords": ["timber", "lumber", "wood", "plywood", "plank", "beam", "stud", "decking"],
            "buyer_query": "general contractors carpenters furniture workshops building supply",
        },
        {
            "category_keywords": ["construction", "building", "interior", "finish"],
            "item_keywords": ["tile", "marble", "granite", "flooring", "ceramic", "laminate", "drywall"],
            "buyer_query": "flooring contractors renovation contractors interior builders",
        },
        {
            "category_keywords": ["construction", "building", "metal", "steel"],
            "item_keywords": ["steel", "rebar", "iron", "beam", "pipe", "conduit", "sheet metal"],
            "buyer_query": "metal fabrication contractors steel suppliers construction companies",
        },
        {
            "category_keywords": ["construction", "building"],
            "item_keywords": [],
            "buyer_query": "general contractors building material suppliers construction companies",
        },

        # --- Scrap, Recycling & E-Waste ---
        {
            "category_keywords": ["scrap", "recycling", "waste", "electronics"],
            "item_keywords": ["copper", "brass", "aluminum", "cable", "wire", "scrap metal"],
            "buyer_query": "scrap metal dealers scrap yard metal recycling buyers",
        },
        {
            "category_keywords": ["electronics", "scrap", "e-waste", "hardware", "it"],
            "item_keywords": ["computer", "laptop", "pcb", "server", "e-waste", "monitor", "electronics", "circuit"],
            "buyer_query": "e-waste recycling computer repair electronics refurbished wholesale",
        },
        {
            "category_keywords": ["recycling", "scrap", "waste"],
            "item_keywords": ["plastic", "hdpe", "pet", "polymer"],
            "buyer_query": "plastic recycling scrap dealers manufacturing suppliers",
        },

        # --- Packaging & Logistics ---
        {
            "category_keywords": ["packaging", "shipping", "logistics", "warehouse"],
            "item_keywords": ["box", "carton", "corrugated", "pallet", "wooden pallet", "bubble wrap", "crate"],
            "buyer_query": "logistics packaging suppliers moving companies shipping warehouses",
        },

        # --- Textiles & Apparel ---
        {
            "category_keywords": ["textile", "fabric", "apparel", "clothing"],
            "item_keywords": ["fabric", "cloth", "cotton", "silk", "denim", "wool", "yarn", "roll"],
            "buyer_query": "garment manufacturers clothing tailors fashion studios textile wholesale",
        },

        # --- Furniture & Office Equipment ---
        {
            "category_keywords": ["furniture", "office"],
            "item_keywords": ["chair", "desk", "table", "cubicle", "cabinet", "sofa", "office furniture"],
            "buyer_query": "used office furniture liquidators secondhand commercial office furniture",
        },

        # --- Industrial & Machinery ---
        {
            "category_keywords": ["industrial", "machinery", "equipment", "tool"],
            "item_keywords": ["motor", "pump", "generator", "compressor", "valve", "bearing", "machinery"],
            "buyer_query": "industrial equipment repair machinery dealers maintenance contractors",
        },
    ]

    @classmethod
    def formulate_query(cls, item_name: str, category: str) -> str:
        """
        Formulate a commercial buyer search query based on item name and category.
        
        Args:
            item_name: Name or description of the surplus item (e.g. 'Fresh Organic Tomatoes')
            category: Category of the item (e.g. 'Food & Agriculture')
            
        Returns:
            A targeted search query string for Google Local search.
        """
        item_lower = (item_name or "").lower().strip()
        cat_lower = (category or "").lower().strip()
        combined_text = f"{cat_lower} {item_lower}"

        # 1. Match specific rules based on category and item keywords
        for rule in cls.BUYER_RULES:
            cat_match = any(ck in combined_text for ck in rule["category_keywords"])
            
            if rule["item_keywords"]:
                item_match = any(ik in combined_text for ik in rule["item_keywords"])
                if cat_match and item_match:
                    return rule["buyer_query"]
            elif cat_match:
                return rule["buyer_query"]

        # 2. Extract clean alphanumeric item name for dynamic query formulation
        clean_item = re.sub(r"[^\w\s-]", "", item_name).strip()
        clean_cat = re.sub(r"[^\w\s-]", "", category).strip()

        # 3. Dynamic fallback: combine cleaned item / category with commercial buyer terms
        if clean_item and clean_cat:
            return f"{clean_item} {clean_cat} commercial wholesale buyers"
        elif clean_item:
            return f"{clean_item} commercial wholesale buyers"
        elif clean_cat:
            return f"{clean_cat} commercial wholesale buyers"
        
        return "commercial wholesale buyers liquidators"
