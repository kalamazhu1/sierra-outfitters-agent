from sierra_agent.data import load_products, load_products_by_sku


def test_load_products_by_sku_indexes_catalog_by_sku():
    products = load_products()
    products_by_sku = load_products_by_sku()

    assert len(products_by_sku) == len(products)
    assert products_by_sku["SOBP001"]["ProductName"] == "Bhavish's Backcountry Blaze Backpack"


def test_load_products_by_sku_is_cached():
    assert load_products_by_sku() is load_products_by_sku()
