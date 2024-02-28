import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import threading
import subprocess
import os
import pty

win_x = 0
win_y = 0
current_image_path = ''  # Add this to store the current image path

def get_window_position(root):
    global win_x, win_y
    win_x = root.winfo_x()
    win_y = root.winfo_y()
    print(f"Window position - X: {win_x}, Y: {win_y}")

def update_canvas_image(canvas, x, y, image_folder, dot_radius=5, zoom_factor=1.0001):
    global current_image_path  # Use the global variable to access the current image path
    
    # Use the current image for operations
    original_img = Image.open(current_image_path)
    img_width, img_height = original_img.size
    
    # Calculate the crop box dimensions centered around (x, y)
    crop_width = img_width / zoom_factor
    crop_height = img_height / zoom_factor
    left = max(0, x - crop_width / 2)
    upper = max(0, y - crop_height / 2)
    right = min(img_width, x + crop_width / 2)
    lower = min(img_height, y + crop_height / 2)
    crop_box = (left, upper, right, lower)
    
    # Crop and zoom the image
    cropped_img = original_img.crop(crop_box).resize(original_img.size, Image.LANCZOS)
    
    # Draw a red dot at the specified (x, y) coordinates on the zoomed image
    img_drawable = ImageDraw.Draw(cropped_img)
    img_drawable.ellipse([(x - dot_radius, y - dot_radius), (x + dot_radius, y + dot_radius)], fill="red")
    
    # Generate a unique filename for the new image
    new_image_path = '/home/lunkwill/projects/tobii/images/zoomed_5_1.png'
    
    # Save the new image and update the current image path
    cropped_img.save(new_image_path)
    current_image_path = new_image_path  # Update the path to the new image
    
    # Convert the edited image to a format that can be used by Tkinter
    img_tk = ImageTk.PhotoImage(cropped_img)
    canvas.background = img_tk
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

def read_subprocess_output_and_update_gui(master_fd, canvas, screen_width, screen_height):
    global win_x, win_y, current_image_path
    with os.fdopen(master_fd, 'r') as stdout:
        for line in iter(stdout.readline, ''):
            parts = line.split(":")
            numbers = parts[1].split(",")

            x = float(numbers[0]) * screen_width
            y = float(numbers[1]) * screen_height

            image_x = x - win_x
            image_y = y - win_y

            canvas.after(0, update_canvas_image, canvas, image_x, image_y, '/home/lunkwill/projects/tobii/images', 5, 1.0001)

def start_gui_and_subprocess():
    global current_image_path
    root = tk.Tk()
    root.geometry('512x512')

    canvas = tk.Canvas(root, width=512, height=512)
    canvas.pack(fill=tk.BOTH, expand=True)

    # Initialize the current image path with the path to your original image
    current_image_path = '/home/lunkwill/projects/ComfyUI/output/cat_00030_.png'

    master, slave = pty.openpty()
    cpp_script_path = '/home/lunkwill/projects/tobii_eye_tracker_linux_installer/example/main'
    process = subprocess.Popen(cpp_script_path, shell=True, stdout=slave, stderr=subprocess.PIPE, text=True, bufsize=1)
    os.close(slave)

    threading.Thread(target=read_subprocess_output_and_update_gui, args=(master, canvas, root.winfo_screenwidth(), root.winfo_screenheight()), daemon=True).start()

    root.bind('<Configure>', lambda event: get_window_position(root))

    root.mainloop()
    process.wait()

if __name__ == "__main__":
    start_gui_and_subprocess()
