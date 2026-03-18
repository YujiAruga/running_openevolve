def solve_packing(container_dims, items):
    placed_items = []
    # EVOLVE-BLOCK-START
    """
    Solves 2D/3D Knapsack Packing using a Maximal Rectangles / Best-Fit heuristic.
    Supports item rotation, inventory counts, and dynamic dimension detection.
    """
    is_3d = len(container_dims) == 3
    if is_3d:
        W, H, D = container_dims
    else:
        W, H = container_dims
        D = 0

    sorted_items = sorted(items, key=lambda x: x["p"], reverse=True)

    free_spaces = [[0, 0, 0, W, H, D if is_3d else 1]]

    for item in sorted_items:
        for _ in range(item["count"]):
            best_space_idx = -1
            best_fit_rotation = None

            if is_3d:
                w, h, d = item["w"], item["h"], item["d"]
                rotations = [
                    (w, h, d),
                    (w, d, h),
                    (h, w, d),
                    (h, d, w),
                    (d, w, h),
                    (d, h, w),
                ]
            else:
                w, h = item["w"], item["h"]
                rotations = [(w, h, 1), (h, w, 1)]

            found_placement = False
            for s_idx, space in enumerate(free_spaces):
                sx, sy, sz, sw, sh, sd = space

                for rw, rh, rd in rotations:
                    if rw <= sw and rh <= sh and rd <= sd:
                        if is_3d:
                            placed_items.append((item["id"], sx, sy, sz, rw, rh, rd))
                        else:
                            placed_items.append((item["id"], sx, sy, rw, rh))

                        new_spaces = []
                        if sw - rw > 0:
                            new_spaces.append([sx + rw, sy, sz, sw - rw, rh, rd])
                        if sh - rh > 0:
                            new_spaces.append([sx, sy + rh, sz, sw, sh - rh, rd])
                        if is_3d and sd - rd > 0:
                            new_spaces.append([sx, sy, sz + rd, sw, sh, sd - rd])

                        free_spaces.pop(s_idx)
                        free_spaces.extend(new_spaces)
                        free_spaces.sort(key=lambda s: s[3] * s[4] * s[5])

                        found_placement = True
                        break
                if found_placement:
                    break

            if not found_placement:
                break
    # EVOLVE-BLOCK-END

    return placed_items
