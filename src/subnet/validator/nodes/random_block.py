import random


def select_block(first_block, last_block, chunks=16):
    total_blocks = last_block - first_block + 1
    num_parts = chunks
    part_size = total_blocks // num_parts

    # Assign probabilities linearly
    probabilities = [(i + 1) for i in range(num_parts)]
    total_probability = sum(probabilities)
    normalized_probabilities = [p / total_probability for p in probabilities]

    # Create the ranges
    ranges = [(first_block + i * part_size, first_block + (i + 1) * part_size - 1) for i in range(num_parts)]
    ranges[-1] = (ranges[-1][0], last_block)  # Adjust the last range to include the last block

    # Select a range based on the probabilities
    selected_range = random.choices(ranges, weights=normalized_probabilities, k=1)[0]

    # Select a single block within the selected range
    selected_block = random.randint(selected_range[0], selected_range[1])
    return selected_block
