
import json
import random
from pathlib import Path

with open(Path(__file__).parent / "wardrobe.json", "r") as file:
    wardrobe = json.load(file)

style_weights = {
    "casual": 1,
    "athletic": 3,
    "dressy": 3,
    "cozy": 2,
    "edgy": 3,
    "western": 3,
    "boho": 3
}

style_conflicts = {
    "athletic": ["dressy"],
    "dressy": ["athletic", "edgy"],
    "edgy": ["dressy", "boho"],
    "boho": ["edgy", "cozy"]
}

incompatible_subcategories = {
    "leggings": ["mary_janes", "heels"],
    "mary_janes": ["leggings", "sweatpants"],
    "heels": ["leggings", "jeans", "shorts", "joggers", "sweatpants", "overalls"],
    "jeans": ["heels"],
    "athletic_shorts": ["heels", "sweater"],
    "jean_shorts": ["heels"],
    "joggers": ["heels"],
    "sweatpants": ["heels", "sweater", "mary_janes"],
    "overalls": ["heels", "sweatshirt", "sweater"],
    "sweater": ["sweatpants", "overalls", "athletic_shorts"],
    "sweatshirt": ["overalls"],
}

neutral_colors = {
    "black", "white", "cream", "gray", "grey",
    "denim", "brown", "beige" , "gold"
}

monochrome_penalty_colors = {
    "brown",
    "gray",
    "grey",
    "beige",
    "cream",
    "white"
}

color_conflicts = {
    "red": ["dark_green", "light_green", "pink", "blue", "burgundy", "brown"],
    "dark_green": ["red", "burgundy", "blue", "brown", "pink", "yellow"],
    "light_green": ["dark_green", "red", "burgundy", "blue", "brown"],
    "blue": ["brown", "green", "red"],
    "brown": ["blue", "pink", "gray", "light_green", "dark_green", "red", "burgundy"],
    "burgundy": ["dark_green", "pink", "red", "brown", "light_green"],
    "pink": ["brown", "red", "burgundy", "dark_green"],
    "gray": ["brown"],
    "cream": ["white"],
    "white": ["cream"],
    "yellow": ["dark green"]
}


# HELPER FUNCTIONS

def filter_by_category(wardrobe, category):
    matches = []
    for item in wardrobe:
        if item["category"] == category:
            matches.append(item)
    return matches


def calculate_style_score(shared_styles):
    total_score = 0
    for item in shared_styles:
        total_score += style_weights[item]
    return total_score


def calculate_conflict_penalty(styles_a, styles_b):
    penalty = 0
    for item in styles_a:
        if item in style_conflicts:
            for conflict in style_conflicts[item]:
                if conflict in styles_b:
                    penalty += 2
    return penalty


def is_outfit_compatible(item_a, item_b):
    subcategory_a = item_a.get("subcategory")
    subcategory_b = item_b.get("subcategory")

    if subcategory_a in incompatible_subcategories:
        if subcategory_b in incompatible_subcategories[subcategory_a]:
            return False

    if subcategory_b in incompatible_subcategories:
        if subcategory_a in incompatible_subcategories[subcategory_b]:
            return False

    return True


def calculate_color_score(colors_a, colors_b):
    color_score = 0

    if colors_a & colors_b:
        color_score += 3

    if (colors_a & neutral_colors) or (colors_b & neutral_colors):
        color_score += 2

    return color_score


def calculate_color_penalty(colors_a, colors_b):
    color_penalty = 0

    for item in colors_a:
        if item in color_conflicts:
            for conflict in color_conflicts[item]:
                if conflict in colors_b:
                    color_penalty += 4

    return color_penalty

def clamp_score(score, maximum):
    return max(0, min(score, maximum))

def calculate_outfit_style_score(top, bottoms, shoes):
    items = [top, bottoms, shoes]

    style_score = 16

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            styles_a = set(items[i]["styles"])
            styles_b = set(items[j]["styles"])

            shared_styles = styles_a & styles_b

            match_score = calculate_style_score(shared_styles)

            style_score += min(match_score, 8)

            conflict_penalty = calculate_conflict_penalty(
                styles_a, styles_b
            )

            style_score -= conflict_penalty

    return clamp_score(style_score, 40)


def is_season_compatible(top, bottoms, shoes, accessories):
    top_seasons = set(top.get("seasons", []))
    bottoms_seasons = set(bottoms.get("seasons", []))
    shoes_seasons = set(shoes.get("seasons", []))

    common_seasons = top_seasons & bottoms_seasons & shoes_seasons

    if accessories:
        accessories_seasons = set(accessories.get("seasons", []))
        common_seasons = common_seasons & accessories_seasons

    return bool(common_seasons)

def calculate_monochrome_penalty(top_colors, bottoms_colors):
    matching_colors = top_colors & bottoms_colors

    penalty_colors = matching_colors & monochrome_penalty_colors

    if penalty_colors:
        return 8

    return 0

def calculate_color_pair_score(colors_a, colors_b, maximum):
    if not colors_a or not colors_b:
        return 0

    shared_colors = colors_a & colors_b

    if shared_colors:
        return maximum * 0.5

    if (colors_a & neutral_colors) or (colors_b & neutral_colors):
        return maximum

    return maximum * 0.5

def calculate_outfit_color_score(top, bottoms, shoes):
    top_colors = set(top["colors"])
    bottoms_colors = set(bottoms["colors"])
    shoes_colors = set(shoes["colors"])

    score = 12

    score += calculate_color_pair_score(
        top_colors, bottoms_colors, 8
    )

    score += calculate_color_pair_score(
        top_colors, shoes_colors, 5
    )

    score += calculate_color_pair_score(
        bottoms_colors, shoes_colors, 5
    )

    score -= calculate_color_penalty(
        top_colors, bottoms_colors
    )

    score -= calculate_color_penalty(
        top_colors, shoes_colors
    )

    score -= calculate_color_penalty(
        bottoms_colors, shoes_colors
    )

    score -= calculate_monochrome_penalty(
        top_colors, bottoms_colors
    )

    return clamp_score(score, 30)

def calculate_clothing_compatibility_score(top, bottoms, shoes):
    pairs = [
        (top, bottoms),
        (top, shoes),
        (bottoms, shoes)
    ]

    for item_a, item_b in pairs:
        if not is_outfit_compatible(item_a, item_b):
            return 0

    return 20

def calculate_accessory_score(top, bottoms, shoes, accessory):
    if accessory is None:
        return 8

    clothing_items = [top, bottoms, shoes]

    accessory_styles = set(accessory["styles"])

    outfit_styles = set()

    for item in clothing_items:
        outfit_styles.update(item["styles"])

    conflict_penalty = calculate_conflict_penalty(
        accessory_styles, outfit_styles
    )

    conflict_penalty += calculate_conflict_penalty(
        outfit_styles, accessory_styles
    )

    if conflict_penalty > 0:
        return 0

    if accessory_styles & outfit_styles:
        return 10

    return 7

# OUTFIT GENERATOR

def generate_outfit(season="any"):

    # Filter wardrobe by season

    if season == "any":
        available_wardrobe = wardrobe
    else:
        available_wardrobe = [
            item for item in wardrobe
            if season in item.get("seasons", [])
        ]

    # Filter wardrobe by category

    tops = filter_by_category(available_wardrobe, "tops")
    bottoms = filter_by_category(available_wardrobe, "bottoms")
    shoes = filter_by_category(available_wardrobe, "shoes")
    accessories = filter_by_category(available_wardrobe, "accessories")

    if not all([tops, bottoms, shoes]):
        print("DEBUG - Missing required clothing category")
        return {}, None

    # Initialize generation variables

    attempts = 0
    max_attempts = 10000
    minimum_score = 70
    best_score = float("-inf")
    best_outfit = {}
    qualified_outfits = []
    seen_outfits = set()

    while attempts < max_attempts:
        attempts += 1

        # Randomly select clothing

        selected_top = random.choice(tops)
        selected_bottoms = random.choice(bottoms)
        selected_shoes = random.choice(shoes)
        selected_accessories = random.choice(accessories + [None])

        # Compatibility checks

        if not is_season_compatible(
            selected_top,
            selected_bottoms,
            selected_shoes,
            selected_accessories
        ):
            continue

        if not is_outfit_compatible(selected_bottoms, selected_shoes):
            continue

        if not is_outfit_compatible(selected_bottoms, selected_top):
            continue

        if not is_outfit_compatible(selected_top, selected_shoes):
            continue

          # Calculate the new 100-point score
        outfit_score = calculate_outfit_score(
            selected_top,
            selected_bottoms,
            selected_shoes,
            selected_accessories
        )

        # Reject incompatible outfits
        if outfit_score is None:
            continue

        # Keep the highest-scoring outfit
        if outfit_score > best_score:
            best_score = outfit_score

            best_outfit = {
                "top": selected_top,
                "bottoms": selected_bottoms,
                "shoes": selected_shoes,
                "accessories": selected_accessories
            }
        # if outfit score > minimum score
        if outfit_score >= minimum_score:

            outfit_key = (
                selected_top["name"],
                selected_bottoms["name"],
                selected_shoes["name"],
                selected_accessories["name"]
                if selected_accessories else None
            )

            if outfit_key not in seen_outfits:
                seen_outfits.add(outfit_key)

                qualified_outfits.append(
                    (outfit_score, {
                        "top": selected_top,
                        "bottoms": selected_bottoms,
                        "shoes": selected_shoes,
                        "accessories": selected_accessories
                    })
                )
            # Return results to Flask

    if not qualified_outfits:
        return {}, None

    # Find outfits within 3 points of the highest score
    top_outfits = [
        (score, outfit)
        for score, outfit in qualified_outfits
        if score >= best_score - 3
    ]

    # Choose randomly from the best outfits
    selected_score, selected_outfit = random.choice(top_outfits)

    return selected_outfit, selected_score

def calculate_outfit_score(top, bottoms, shoes, accessory):
    clothing_score = calculate_clothing_compatibility_score(
        top, bottoms, shoes
    )

    if clothing_score == 0:
        return None

    style_score = calculate_outfit_style_score(
        top, bottoms, shoes
    )

    color_score = calculate_outfit_color_score(
        top, bottoms, shoes
    )

    accessory_score = calculate_accessory_score(
        top, bottoms, shoes, accessory
    )

    total_score = (
        clothing_score
        + style_score
        + color_score
        + accessory_score
    )

    return round(clamp_score(total_score, 100), 2)

# OPTIONAL TERMINAL MODE

if __name__ == "__main__":
    best_outfit, best_score = generate_outfit()

    if not best_outfit:
        print("No outfit reached the 70% quality threshold.")

    else:
        print("Outfit generated successfully!")
        print("Outfit quality:", best_score, "%")
        print()

        print("myCloset Outfit:")
        print("Top:", best_outfit["top"]["name"])
        print("Bottoms:", best_outfit["bottoms"]["name"])
        print("Shoes:", best_outfit["shoes"]["name"])

        if best_outfit["accessories"]:
            print("Accessory:", best_outfit["accessories"]["name"])
        else:
            print("Accessory: None")

