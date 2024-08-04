def generateId(brand=None, type="", color=""):
    brandToId = ""

    if brand is not None and brand != "unknown":
        brandToId = f"{brand}_"

    return f"filament_{brandToId}{type}_{color.lstrip('#')}"
