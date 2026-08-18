def deterministic_beam_search(candidate_numbers, score_function, max_size=6, beam_width=50):
    candidates = tuple(sorted(set(int(number) for number in candidate_numbers)))
    if len(candidates) < max_size:
        raise ValueError("Candidate pool hedef set boyutundan küçük olamaz.")
    beam = [(tuple(), 0.0)]
    best_by_size = {}
    for size in range(1, max_size + 1):
        expansions = {}
        for current, _ in beam:
            for candidate in candidates:
                if candidate in current:
                    continue
                new_set = tuple(sorted((*current, candidate)))
                if len(new_set) != size:
                    continue
                expansions[new_set] = score_function(new_set)
        ordered = sorted(expansions.items(), key=lambda item: (-item[1], item[0]))
        beam = ordered[:beam_width]
        if not beam:
            raise ValueError("Beam search aday üretemedi.")
        if size >= 4:
            best_by_size[size] = beam[0][0]
    return best_by_size
