from PIL import Image, ImageDraw, ImageFont, ImageOps
import os
import matplotlib.pyplot as plt
import colorsys

# This script is meant to extract the data from the graphs outputted by the Quattro's point/map report feature
# As an additional feature, it will automatically remove any ugly labels from the graph and create a clean version
# Open the report document in Word, click on the report graph, copy it, and paste it in DirtyGraphImages
# The script will ask you to type a number in because I don't want to make my venv instance 3 times bigger by installing Keras or smth
# Just deal with it


def color_distance(col1, col2):
    # Distance between two colors
    return ((col1[0] - col2[0])**2 + (col1[1] - col2[1])**2 + (col1[2] - col2[2])**2)**0.5


def less_than_all(candidate, others):
    # Return True if candidate is less than all values in others
    # candidate must be a number
    # others must be a list of numbers
    return all([candidate < i for i in others])


# The following is from https://stackoverflow.com/questions/70631490/how-can-i-make-np-argmin-code-without-numpy
def argmin(a):
    return min(range(len(a)), key=lambda x: a[x])


def argmax(a):
    return max(range(len(a)), key=lambda x: a[x])


def is_between(value, bounds):
    # Return true if value is between bounds
    # value: number
    # bounds: 2-tuple of numbers in any order
    return min(bounds) <= value <= max(bounds)


# Load font
font = ImageFont.truetype(os.path.join("C:", "Windows", "Fonts", "segoeui.ttf"), 24)


input_dir = "DirtyGraphImages"
output_dir = "CleanGraphImages"

for filename in os.listdir(input_dir):
    with Image.open(os.path.join("DirtyGraphImages", filename)) as graph_image:
        rgb_image = graph_image.convert('RGB')

        line_color = (70, 152, 226)  # the color of the line part of the graph that we're trying to read
        text_color = (0, 0, 0)  # the base color of text that's unfortunately overlaid on top of the graph
        background_line_color = (192, 192, 192)  # the color of tick marks and background lines that we can ignore
        background_color = (255, 255, 255)  # the color of the background
        # ^ Some of these colors aren't used
        # because I found it was much more reliable to look for changes in hue and saturation

        x_units = "eV"
        y_units = "counts"

        origin_point = (70, 469)
        # We might be able to find the origin point by looking for the intersection of the axes and the line
        # (which has to be on OR NEAR!! the x-axis for the first few eV due to machine limitations)
        # Maybe something to do if we need to use graphs from other software or functions of the machine
        # What follows are default values for the reference x- and y-points, but they are immediately overwritten
        x_point = (2111, 469)
        x_point_value = 20 * 1000
        y_point = (70, 32)
        y_point_value = 80 * 1000
        # Alternatively, automatically find a major gridline and recognize the text associated with it
        gridline_row = -1
        n_major_gridlines = 0
        for row in range(graph_image.size[1]):
            if color_distance(rgb_image.getpixel((graph_image.size[0]-2, row)), background_line_color) < 10:
                # This row is a major gridline
                if gridline_row == -1:
                    gridline_row = row
                    y_point = (graph_image.size[0]-2,gridline_row)
                n_major_gridlines += 1
        # Get a bounding box for the label, assuming that it's near the major gridline we found
        image_copy = rgb_image.crop((0, gridline_row - 20, origin_point[0] - 8, gridline_row + 20))  # left, top, right, bottom
        crop_bbox = ImageOps.invert(image_copy).getbbox()
        # We can convert the crop bbox back to image coordinates if we wanted to
        # label_bbox = (crop_bbox[0] + 0, crop_bbox[1] + gridline_row - 20, crop_bbox[2] + 0, crop_bbox[3] + gridline_row - 20)
        # Use our super ultra high tech optical character recognition software to identify the label
        # (AKA the user's eyeballs, brain, and fingers)
        image_copy.crop(crop_bbox).show()
        label_text = ""
        while "k" not in label_text:
            label_text = input("What does this say? (Please include the lowercase 'k') ")
        y_point_value = int(label_text[:-1]) * 1000

        # Figure out the scale of the graph as single values
        x_unit_value = x_point_value / (x_point[0] - origin_point[0])  # value of 1 pixel difference on X
        y_unit_value = y_point_value / -(y_point[1] - origin_point[1])  # value of 1 pixel difference on Y
        print(f"Uncertainties: x: {x_unit_value:.02f} {x_units}, y: {y_unit_value:.02f} {y_units}")

        num_columns = x_point[0] - origin_point[0]

        # x_values, lower_bounds, and upper_bounds are pretty much universally the pixel values instead of actual unit values
        # Maybe I should just use Numpy for this...
        x_values = [i + origin_point[0] for i in range(num_columns)]#[i * x_unit_value for i in range(num_columns)]
        lower_bounds = [0 for i in range(num_columns)]
        upper_bounds = [0 for i in range(num_columns)]
        undetermined = [False for i in range(num_columns)]

        for col in range(x_point[0] - origin_point[0]):
            col_pix_pos = origin_point[0] + col
            row_pix_pos = origin_point[1]

            # Assumptions for a single column:
            # There is one contiguous region that represents where the column intersects the line
            # Text could cover the line
            # There can be more than one contiguous regions of text in a column
            # If no line is visible but one text region is, the text must be covering the line
            # If no line is visible but multiple text regions are, one of them must be covering the line
            # The line region in one column is adjacent (strictly touching) the line region in neighboring columns
            # If the text happens to be similar to the line, it isn't similar for long

            line_rows = []
            text_rows = []

            while row_pix_pos > 0:
                current_color = rgb_image.getpixel((round(col_pix_pos), round(row_pix_pos)))
                pixel_hsv = colorsys.rgb_to_hsv(*current_color)

                if abs(pixel_hsv[0]*360 - 208) < 5 and pixel_hsv[1] > 0.5 and pixel_hsv[2] < 255 * 0.9:
                    # However the Quattro is generating these plots, they conserve hue fairly reliably
                    # So we can use that to determine whether a pixel is meant to be on the line or not
                    line_rows.append(row_pix_pos) #-(row_pix_pos - origin_point[1]) * y_unit_value)

                row_pix_pos -= 1

            if len(line_rows) > 0:
                lower_bounds[col] = min(line_rows)
                upper_bounds[col] = max(line_rows)

                # Check to make sure it connects to the previous column:
                if 0 < col < graph_image.size[0]:
                    # Assume that the break is either as the data is rising
                    # (upper left = lower right) or falling (lower left = upper right)
                    left_bounds = (upper_bounds[col-1], lower_bounds[col-1])
                    right_bounds = (upper_bounds[col], lower_bounds[col])
                    if not (is_between(upper_bounds[col], left_bounds) or is_between(lower_bounds[col], left_bounds) or is_between(upper_bounds[col-1], right_bounds) or is_between(lower_bounds[col-1], right_bounds)):
                        # Re-connect by re-drawing the shorter column
                        if abs(upper_bounds[col-1] - lower_bounds[col-1]) < abs(upper_bounds[col] - lower_bounds[col]):
                            undetermined[col-1] = True
                        else:
                            undetermined[col] = True
            else:
                undetermined[col] = True

        # We can fill in from neighboring columns, assuming that the undetermined region is only one column wide
        # Also notify the user of the number of undetermined columns
        # and whether there are any two undetermined columns next to one another
        notif = "Undetermined columns: "
        last_undetermined_val = -1
        for c in range(len(undetermined)):
            if undetermined[c]:
                if abs(c - last_undetermined_val) < 2:
                    print("Undetermined value error!")
                last_undetermined_val = c
                notif = notif + str(c + origin_point[0]) + ", "

                # Connect undetermined columns by tying them to the limits of the nearby columns
                dist_to_lower = (abs(lower_bounds[c-1] - lower_bounds[c+1]), abs(lower_bounds[c-1] - upper_bounds[c+1]))
                dist_to_upper = (abs(upper_bounds[c-1] - lower_bounds[c+1]), abs(upper_bounds[c-1] - upper_bounds[c+1]))
                lower_or_upper = argmin([min(l) for l in (dist_to_lower, dist_to_upper)])
                closest_1 = (lower_bounds[c-1], upper_bounds[c-1])[lower_or_upper]
                closest_2 = (lower_bounds[c+1], upper_bounds[c+1])[argmin((dist_to_lower, dist_to_upper)[lower_or_upper])]
                lower_bounds[c] = min((closest_1, closest_2))
                upper_bounds[c] = max((closest_1, closest_2))

        # Print a notification if there are any undetermined columns that needed to be filled
        if len(undetermined) > 0:
            print(notif[:-2])

        # Save the data in a CSV file for use with Sheets, Excel, other scripts, etc.
        with open(os.path.join(output_dir, filename[:-4] + "_data.csv"), 'w') as csv_file:
            csv_file.write("eV,Upper Bound,Lower Bound\n")
            for point in range(len(x_values)):
                csv_file.write(f"{(x_values[point] - origin_point[0]) * x_unit_value},{(origin_point[1] - upper_bounds[point]) * y_unit_value},{(origin_point[1] - lower_bounds[point]) * y_unit_value}\n")

        # Render the clean graph, either as an image or as an interactive Matplotlib graph
        render = "IMAGE"# "MATPLOTLIB"

        if render == "MATPLOTLIB":
            # Matplotlib-based plotting
            plt.fill_between(x_values, lower_bounds, upper_bounds)
            plt.plot(x_values, lower_bounds, 'k')
            plt.plot(x_values, upper_bounds, 'k')
            plt.show()

        elif render == "IMAGE":
            # Raw image-based plotting to replicate the Quattro's output as accurately as possible
            new_image = Image.new(mode='RGB', size=graph_image.size)
            canvas = ImageDraw.Draw(new_image)
            canvas.rectangle(((0,0), new_image.size), (255,255,255))
            # Draw axes
            canvas.line((origin_point, (graph_image.size[0], origin_point[1])), background_line_color)
            canvas.line((origin_point, (origin_point[0], 0)), background_line_color)

            # Draw ticks and gridlines
            # Draw vertical ticks and gridlines
            maximum_y = y_unit_value * origin_point[1]
            print(f"Maximum y: {maximum_y}")
            tick_value_candidates = [1, 2.5, 5, 10, 20, 50, 100, 500]
            tick_value_candidates = tick_value_candidates + [v * 1000 for v in tick_value_candidates]
            major_tick_value = tick_value_candidates[argmax([maximum_y / v if maximum_y / v <= 5 else 0 for v in tick_value_candidates])]
            n_major_ticks = int(maximum_y / major_tick_value) + 1
            print(f"Major tick value: {major_tick_value}")
            minor_tick_value = major_tick_value / 5  # always have 5 minor ticks in between major ticks
            # Draw major and minor ticks
            for ma in range(n_major_ticks):
                tick_real_value = ma * major_tick_value
                ma_pixel_y_value = origin_point[1] - tick_real_value / y_unit_value
                canvas.line(((origin_point[0]-1, ma_pixel_y_value), (origin_point[0]-6, ma_pixel_y_value)), text_color)
                # Draw gridlines
                canvas.line(((origin_point[0], ma_pixel_y_value), (graph_image.size[0], ma_pixel_y_value)), background_line_color)
                # Draw minor gridlines
                for mi in range(5):
                    mi_pixel_y_value = ma_pixel_y_value - minor_tick_value / y_unit_value * mi
                    if mi_pixel_y_value >= 0:
                        canvas.line(((origin_point[0] - 1, mi_pixel_y_value), (origin_point[0] - 4, mi_pixel_y_value)), text_color)
                # Draw labels
                tick_label = f"{tick_real_value}"
                if tick_real_value >= 1000 and tick_real_value < major_tick_value * n_major_ticks:
                    tick_label = f"{int(tick_real_value / 1000)}k"
                canvas.text(xy=(origin_point[0]-9, max(min(ma_pixel_y_value+1, origin_point[1] - 16), 16)), text=tick_label, font=font, fill=text_color, anchor="rm")

            # Draw horizontal ticks and gridlines
            maximum_x = x_unit_value * graph_image.size[0] - origin_point[0]
            nearest_good_value = int(maximum_x * 5000) / 5000
            major_tick_value = 5000
            n_major_ticks = int(maximum_x / major_tick_value) + 1
            minor_tick_value = major_tick_value / 5
            for ma in range(n_major_ticks):
                tick_real_value = ma * major_tick_value
                ma_pixel_x_value = origin_point[0] + tick_real_value / x_unit_value
                canvas.line(((ma_pixel_x_value, origin_point[1]+1), (ma_pixel_x_value, origin_point[1]+6)), text_color)
                # Draw gridlines
                canvas.line(((ma_pixel_x_value, origin_point[1]), (ma_pixel_x_value, 0)), background_line_color)
                # Draw minor gridlines
                for mi in range(5):
                    mi_pixel_x_value = ma_pixel_x_value - minor_tick_value / x_unit_value * mi
                    if mi_pixel_x_value < graph_image.size[0]:
                        canvas.line(((mi_pixel_x_value, origin_point[1]+1), (mi_pixel_x_value, origin_point[1]+5)), text_color)
                # Draw labels
                tick_label = f"{tick_real_value} eV"
                if tick_real_value >= 1000:
                    tick_label = f"{int(tick_real_value / 1000)} keV"
                canvas.text(xy=(min(max(ma_pixel_x_value + 1, origin_point[0] + 24), graph_image.size[0] - 37), origin_point[1] + 10), text=tick_label, font=font, fill=text_color, anchor="ma")

            # Draw line
            for col in range(num_columns):
                # x_pos = round(x_values[col] / x_unit_value + origin_point[0])
                # lower_y = round(-lower_bounds[col] / y_unit_value + origin_point[1])
                # upper_y = round(-upper_bounds[col] / y_unit_value + origin_point[1])

                x_pos = x_values[col]
                lower_y = lower_bounds[col]
                upper_y = upper_bounds[col]

                canvas.line(((x_pos, lower_y), (x_pos, upper_y)), line_color)

            # new_image.show()
            new_image.save(os.path.join(output_dir, filename), format="PNG")
