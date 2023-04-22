import math
def calculate_cost(characters: int) -> int:
    cost_per_character = 0.01  # You can adjust this value according to your pricing strategy
    return math.ceil(characters * cost_per_character)
