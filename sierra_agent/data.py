import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


@lru_cache(maxsize=1)
def load_orders() -> List[Dict[str, Any]]:
    return _load_json("CustomerOrders.json")


@lru_cache(maxsize=1)
def load_products() -> List[Dict[str, Any]]:
    return _load_json("ProductCatalog.json")


@lru_cache(maxsize=1)
def load_products_by_sku() -> Dict[str, Dict[str, Any]]:
    return {product["SKU"]: product for product in load_products()}


def _load_json(filename: str) -> List[Dict[str, Any]]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
