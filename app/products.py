# app/products.py

products = {
    "P01": {"name": "Laptop", "category": "Electronics"},
    "P02": {"name": "Headphones", "category": "Electronics"},
    "P03": {"name": "Tablet", "category": "Electronics"},
    "P04": {"name": "Smartphone", "category": "Electronics"},
    "P05": {"name": "Camera", "category": "Electronics"},

    "P06": {"name": "Rice", "category": "Grocery"},
    "P07": {"name": "Milk", "category": "Grocery"},
    "P08": {"name": "Coffee", "category": "Grocery"},
    "P09": {"name": "Cereal", "category": "Grocery"},
    "P10": {"name": "Pasta", "category": "Grocery"},

    "P11": {"name": "Shoes", "category": "Fashion"},
    "P12": {"name": "Jacket", "category": "Fashion"},
    "P13": {"name": "T-Shirt", "category": "Fashion"},
    "P14": {"name": "Jeans", "category": "Fashion"},
    "P15": {"name": "Backpack", "category": "Fashion"},

    "P16": {"name": "Chair", "category": "Home"},
    "P17": {"name": "Lamp", "category": "Home"},
    "P18": {"name": "Vacuum", "category": "Home"},
    "P19": {"name": "Desk", "category": "Home"},
    "P20": {"name": "Blender", "category": "Home"}
}


def get_product_name(product_id):
    return products[product_id]["name"]


def get_product_category(product_id):
    return products[product_id]["category"]