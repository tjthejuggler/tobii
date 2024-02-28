import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

import threading
import subprocess
import os
import pty

win_x = 0
win_y = 0

def get_window_position(root):
    global win_x, win_y
    """
    Print the current position of the Tkinter window.
    :param root: The Tkinter root window object.
    """
    win_x = root.winfo_x()
    win_y = root.winfo_y()
    print(f"Window position - X: {win_x}, Y: {win_y}")

def update_canvas_image(canvas, original_image_path, x, y, dot_radius=5):
    """
    Draw a red dot on the image at the specified (x, y) coordinates and update the canvas background.
    If (x, y) is outside the image, the dot is placed on the nearest edge.
    
    :param canvas: The Tkinter canvas object.
    :param original_image_path: Path to the original background image.
    :param x: X coordinate for the red dot.
    :param y: Y coordinate for the red dot.
    :param dot_radius: Radius of the red dot. Default is 5 pixels.
    """
    # Open the original image from the provided path
    original_img = Image.open(original_image_path)
    img_width, img_height = original_img.size  # Get the dimensions of the image
    
    # Adjust the coordinates to ensure the dot is within the image boundaries
    x = max(0, min(x, img_width))
    y = max(0, min(y, img_height))
    
    # Convert the image to an editable format
    img_drawable = ImageDraw.Draw(original_img)
    
    # Draw a red dot at the adjusted (x, y) coordinates
    img_drawable.ellipse([(x - dot_radius, y - dot_radius), (x + dot_radius, y + dot_radius)], fill="red")
    
    # Convert the edited image to a format that can be used by Tkinter
    img_tk = ImageTk.PhotoImage(original_img)
    
    # Keep a reference to the image to prevent it from being garbage collected
    canvas.background = img_tk
    
    # Update the canvas with the new image, anchoring it at the top-left corner
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)


def read_subprocess_output_and_update_gui(master_fd, canvas, screen_width, screen_height, original_image_path):
    global win_x, win_y
    """
    Read subprocess output in real-time, calculate focus point, and update GUI with a new cropped image.
    :param master_fd: File descriptor for the master end of the pseudo-terminal.
    :param canvas: Tkinter canvas object for background updates.
    :param screen_width: Width of the screen.
    :param screen_height: Height of the screen.
    :param original_image_path: Path to the original image to be zoomed and cropped.
    """
    with os.fdopen(master_fd, 'r') as stdout:
        for line in iter(stdout.readline, ''):
            parts = line.split(":")
            numbers = parts[1].split(",")

            # Convert string to float and scale according to screen size
            x = float(numbers[0]) * screen_width
            y = float(numbers[1]) * screen_height

            # Calculate the coordinates relative to the image
            image_x = x - win_x
            image_y = y - win_y

            # Adjust the zoom level if needed
            zoom_level = 2
            canvas.after(0, update_canvas_image, canvas, original_image_path, image_x, image_y)

def start_gui_and_subprocess():
    root = tk.Tk()
    root.geometry('512x512')

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    print(f"Screen width: {screen_width}, Screen height: {screen_height}")

    canvas = tk.Canvas(root, width=512, height=512)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Define the path to your original image here
    original_image_path = '/home/lunkwill/projects/ComfyUI/output/cat_00030_.png'

    # Setup subprocess
    master, slave = pty.openpty()
    cpp_script_path = '/home/lunkwill/projects/tobii_eye_tracker_linux_installer/example/main'
    process = subprocess.Popen(cpp_script_path, shell=True, stdout=slave, stderr=subprocess.PIPE, text=True, bufsize=1)
    os.close(slave)

    threading.Thread(target=read_subprocess_output_and_update_gui, args=(master, canvas, screen_width, screen_height, original_image_path), daemon=True).start()

    root.bind('<Configure>', lambda event: get_window_position(root))

    root.mainloop()
    process.wait()

if __name__ == "__main__":
    start_gui_and_subprocess()
