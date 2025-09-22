from PIL import Image, ImageDraw, ImageFont, ImageOps
import matplotlib.pyplot as plt
import numpy as np
from pyfonts import load_google_font

# Script that contains functions for rendering EDX graphs in certain styles
# The purpose of doing this is to remove labels that were included accidentally

# All charts have the following axes:
# Vertical axis: Counts / kcounts
# Horizontal axis: keV

# These functions expect to be given an upper bound curve and a lower bound curve
# The space between these curves will be filled in
# The units of these curves should be keV and counts (the real-world units that the data describes)
# The graphs will generally linearly interpolate between the two nearest points, so format your data accordingly
# The bounds curves do not need to have the same number of elements


# Render simply as a Matplotlib plot (for debugging, usually)


# Render in the style of the Quattro ESEM's EDX program



def find_neighbors(point, curve):
    # Return the two nearest points in curve to point, measured by x (0-index) distance
    # This does NOT assume that the curve is sorted
    # Returns the indices of the two surrounding points in curve
    # Assume the point is
    # If the x value of point is less than the lowest value in curve, make the first index (the index of the lower point) -1
    # If the x value of point is greater than the greatest value in the curve, make the second index (the index of the higher point) -1

    # Find the nearest lower point
    nlpi = -1  # nearest lower point index
    for p in range(len(curve)):
        # if nlpi is unset, take the first point that's lower than point
        # if nlpi is set, do the full comparison
        if nlpi == -1:
            if curve[p][0] < point[0]:
                nlpi = p
        else:
            if curve[nlpi][0] < curve[p][0] < point[0]:
                nlpi = p

    # Find the nearest upper point
    nupi = -1  # nearest upper point index
    for p in range(len(curve)):
        # if nupi is unset, take the first point that's higher than point
        # if nupi is set, do the full comparison
        if nupi == -1:
            if curve[p][0] > point[0]:
                nupi = p
        else:
            if point[0] < curve[p][0] < curve[nupi][0]:
                nupi = p

    return nlpi, nupi


def fill_out_curve(curve1, curve2):
    # Interpolate ensure that all of the x positions in curve2 are in curve1,
    # and lerp curve1 to preserve the shape of the curve for these new points
    # Curves are lists of 2-tuples
    orig_curve1_x = [p[0] for p in curve1]
    new_curve1 = curve1.copy()
    for pt in curve2:
        if pt[0] not in orig_curve1_x:
            # Need to add a point to the lower curve at the upper curve's x position
            nlpi, nupi = find_neighbors(pt, curve1)
            if nlpi == -1:
                # No lower point
                new_curve1.append((pt[0], 0))
                continue
            if nupi == -1:
                # No upper point
                new_curve1.append((pt[0], 0))
                continue
            # Otherwise, the point is between other points
            interp_factor = (pt[0] - curve1[nlpi][0]) / (curve1[nupi][0] - curve1[nlpi][0])
            new_point = (pt[0], curve1[nlpi][1] + interp_factor * (curve1[nupi][1] - curve1[nlpi][1]))
            new_curve1.append(new_point)
    return new_curve1


# Render in the style of EDAX GENESIS / the style desired by users of EDAX GENESIS
def render_modified_GENESIS(lower_curve, upper_curve, smooth_wide_edges=False, show=True, save_to=None):
    # Render the data in the style of EDAX GENESIS, but modified to meet Dr. Merchan's instructions
    # lower_curve: list of 2-tuples representing the lower bound curve [(keV, counts), (keV, counts), ...]
    # upper_curve: list of 2-tuples representing the upper bound curve [(keV, counts), (keV, counts), ...]
    # smooth_wide_edges: If the data has a lot of adjacent bars of the same height, smooth the edges so the actual data bars flow into one another more smoothly
    # Returns a PIL Image object that is the rendered graph

    # This is defined as a graph with the space between bounds filled in with the color red (255,0,0)
    # The curves appear to be smoothed or downsampled
    # The axes are labeled "Counts" and "KeV"
    # The axes labels is 26pt Arial while the tick labels are 22pt Arial
    # All text on the specific "We would like profiles like this one" graph appears to be 10pt Arial
    # Horizontal axis should be whole numbers with zero to two digits after the decimal point
    # Vertical axis should be whole numbers with no decimal points (or maybe kcounts with one digit after the point)

    # I'm less concerned with exactly matching a reference graph (like for the Quattro EDX), so I will use Matplotlib

    image_size = (982, 551)
    # Set size of figure
    dpi = 100
    size_in = (image_size[0] / dpi, image_size[1] / dpi)
    plt.figure(figsize=size_in)

    if len(lower_curve) != len(upper_curve):
        # Interpolate one or both curves so that they have the same number of data points
        new_upper_curve = fill_out_curve(upper_curve, lower_curve)
        lower_curve = fill_out_curve(lower_curve, new_upper_curve)
        upper_curve = new_upper_curve

    # lower_curve and upper_curve should have the same number of points now

    lower_curve = sorted(lower_curve, key=lambda p: p[0])
    upper_curve = sorted(upper_curve, key=lambda p: p[0])

    # Smooth sharp edges on wide bars if smooth_wide_edges is true
    if smooth_wide_edges:
        for i in range(1, len(lower_curve)-3):
            print(lower_curve[i-2:i+2], lower_curve[i-1])
            if lower_curve[i-1][1] == lower_curve[i][1] and lower_curve[i+1][1] == lower_curve[i+2][1]:
                # This is the edge of a wide bar
                slope = (lower_curve[i+2][1] - lower_curve[i-1][1]) / (lower_curve[i+2][0] - lower_curve[i-1][0])
                lower_curve[i] = (lower_curve[i][0], slope * (lower_curve[i][0] - lower_curve[i-1][0]) + lower_curve[i-1][1])
                lower_curve[i+1] = (lower_curve[i+1][0], slope * (lower_curve[i+1][0] - lower_curve[i-1][0]) + lower_curve[i-1][1])
            if upper_curve[i-1][1] == upper_curve[i][1] and upper_curve[i+1][1] == upper_curve[i+2][1]:
                # This is the edge of a wide bar
                slope = (upper_curve[i+2][1] - upper_curve[i-1][1]) / (upper_curve[i+2][0] - upper_curve[i-1][0])
                upper_curve[i] = (upper_curve[i][0], slope * (upper_curve[i][0] - upper_curve[i-1][0]) + upper_curve[i-1][1])
                upper_curve[i+1] = (upper_curve[i+1][0], slope * (upper_curve[i+1][0] - upper_curve[i-1][0]) + upper_curve[i-1][1])

    x_values = [p[0] for p in lower_curve]
    lower_bounds = [p[1] for p in lower_curve]
    upper_bounds = [p[1] for p in upper_curve]
    plt.fill_between(x_values, lower_bounds, upper_bounds, color=(1.0,0.0,0.0))

    axis_label_font = load_google_font("Arimo", weight="bold")
    plt.xlabel("KeV", font=axis_label_font, fontsize=26)
    plt.ylabel("Counts", font=axis_label_font, fontsize=26)
    ax = plt.gca()
    # Remove the top and right plot frame lines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Set the axis ticks
    ax.set_xticks(np.array([list(range(1,11))]).flatten(), labels=[f"{i:.01f}" for i in range(1,11)])
    # ax.get_yaxis().set_ticks([])
    for tick in ax.get_xticklabels():
        tick.set_font(axis_label_font)
        tick.set_fontsize(20)
    for tick in ax.get_yticklabels():
        tick.set_font(axis_label_font)
        tick.set_fontsize(20)
    ax.set_xmargin(0.005)
    ax.set_ymargin(0.005)

    plt.tight_layout()
    if save_to is not None:
        plt.savefig(save_to, dpi=dpi)
    if show:
        plt.show()
    plt.close()


if __name__ == "__main__":
    lower_curve = [(0,2), (9,3), (11,4), (15,5)]
    upper_curve = [(1,3), (5,6), (12,8), (14,6), (17,9)]
    neighbors_idx = find_neighbors((0,4), upper_curve)
    if neighbors_idx[0] == -1:
        print("No lower point")
    else:
        print(upper_curve[neighbors_idx[0]])
    if neighbors_idx[1] == -1:
        print("No upper point")
    else:
        print(upper_curve[neighbors_idx[1]])

    render_modified_GENESIS(upper_curve, lower_curve, show=True)