import tkinter as tk
from PIL import Image, ImageTk
import threading
import subprocess
import os
import pty
from collections import deque
import time
from pathlib import Path
import random

import image_gen_new
import _directory_watchdog

from concurrent.futures import ThreadPoolExecutor



win_x = 0
win_y = 0

dimensions = 600
1
clip_square_size = 200

give_to_comfy_half = True

class ZoomApp:
    def __init__(self, master, original_image_path, shared_state, crop_helper, use_eye_tracking=False):

        self.executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of workers as needed

        self.master = master
        self.use_eye_tracking = use_eye_tracking
        self.zoom_level = 1.01  # Adjust zoom level as needed
        self.original_image_path = original_image_path
        self.current_img = Image.open(self.original_image_path)
        self.canvas = tk.Canvas(master, width=dimensions, height=dimensions)
        self.canvas.pack()
        self.master.geometry(f"{dimensions}x{dimensions}")
        self.eyetrack_x = 512
        self.eyetrack_y = 512
        self.position_smoothing = deque(maxlen=9)
        self.just_got_new_image = False
        self.xy_backlog = []
        self.image_generating = False
        self.shared_state = shared_state
        self.old_image = ""
        self.crop_helper = crop_helper

        self.tk_img = ImageTk.PhotoImage(self.current_img)
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        self.denoise_set_point = 0.35
        self.current_denoise = 0.35

        if self.use_eye_tracking:
            self.start_eye_tracking()
        else:
            self.update_image()

    def shutdown(self):
        print("Shutting down the executor and cleaning up...")
        self.executor.shutdown(wait=True)
        #ps aux | grep '/home/lunkwill/projects/tobii_eye_tracker_linux_installer/example/main' | awk '{print $2}' | xargs kill
        os.system("ps aux | grep '/home/lunkwill/projects/tobii_eye_tracker_linux_installer/example/main' | awk '{print $2}' | xargs kill")
        # Any other cleanup code here

    def handle_eyemovement(self, coords):
        avg_x, avg_y = coords

        # Zoom on point similar to `zoom_on_point` in ImageZoomer
        image_width, image_height = self.current_img.size
        crop_box_width = self.canvas.winfo_width() / self.zoom_level
        crop_box_height = self.canvas.winfo_height() / self.zoom_level

        left = max(min(avg_x - crop_box_width / 2, image_width - crop_box_width), 0)
        top = max(min(avg_y - crop_box_height / 2, image_height - crop_box_height), 0)
        right = min(left + crop_box_width, image_width)
        bottom = min(top + crop_box_height, image_height)

        return left, top, right, bottom

    def handle_eyemovement_catchup(self, coords, length_backlog):
        avg_x, avg_y = coords

        # Zoom on point similar to `zoom_on_point` in ImageZoomer
        image_width, image_height = self.current_img.size
        crop_box_width = self.canvas.winfo_width() / self.zoom_level
        crop_box_height = self.canvas.winfo_height() / self.zoom_level

        left = max(min(avg_x - crop_box_width / 2, image_width - crop_box_width), 0)
        top = max(min(avg_y - crop_box_height / 2, image_height - crop_box_height), 0)
        right = min(left + crop_box_width, image_width)
        bottom = min(top + crop_box_height, image_height)

        return left, top, right, bottom

    def save_image(self, img, filename):
        img.save(filename)
        print(f"Image saved to {filename}")

    def zoom_current_image(self, img, left, top, right, bottom):
        success = False
        while not success:
            try:
                cropped_img = img.crop((left, top, right, bottom))
                success = True
            except Exception as e:
                print(f"Error cropping image: {e}. Retrying...")
                time.sleep(.01)
        cropped_img = img.crop((left, top, right, bottom))
        self.current_img = cropped_img.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.Resampling.LANCZOS)

    def super_zoom_current_image(self, img, left, top, right, bottom, zoom_list_length):
        (self.zoom_level - 1)*zoom_list_length
        success = False
        while not success:
            try:
                cropped_img = img.crop((left, top, right, bottom))
                success = True
            except Exception as e:
                print(f"Error cropping image: {e}. Retrying...")
                time.sleep(.01)
        cropped_img = img.crop((left, top, right, bottom))
        self.current_img = cropped_img.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.Resampling.LANCZOS)

    from PIL import Image

    def crop_image_for_clip(self, avg_x, avg_y):
        # Calculate the coordinates of the box
        half = clip_square_size / 2
        left = avg_x - half
        top = avg_y - half
        right = avg_x + half
        bottom = avg_y + half

        # Crop the image
        cropped_img = self.current_img.crop((left, top, right, bottom))

        return cropped_img

    def blend_images(self):
        # Ensure both images are the same size
        img1 = self.current_img.resize(self.old_image.size)

        # Blend the images
        blended_img = Image.blend(img1, self.old_image, alpha=0.5)

        return blended_img

    def generate_image(self, avg_x, avg_y):
        #use PIL.Image.blend to combine the two images self.current_img and self.old_image

        #self.current_img = self.blend_images()

        success = False
        self.image_generating = True
        #resize the image to 512x512
        if give_to_comfy_half:
            self.current_img = self.current_img.resize((512, 512), Image.ANTIALIAS)

        clip_crop_img = self.crop_image_for_clip(avg_x, avg_y)
        clip_crop_img.save("/home/lunkwill/projects/tobii/pre_comfy_clip_image.png")

        self.current_img.save("/home/lunkwill/projects/tobii/pre_comfy_image.png")
        while not success:
            try:
                img = Image.open("/home/lunkwill/projects/tobii/pre_comfy_image.png")
                img.load()  # Attempt to load the image
                # Image processing code here
                success = True  # If the image is loaded successfully, set success to True
            except OSError as e:
                print(f"Error loading image: {e}. Retrying...")
                # retry_count += 1
                # time.sleep(1)  # Wait for 1 second before retrying    
                time.sleep(.01)    
        #time.sleep(.3)           
        image_gen_new.create_img("high definition, high resolution, matrix, amazing", "/home/lunkwill/projects/tobii/pre_comfy_image.png", "/home/lunkwill/projects/tobii/pre_comfy_clip_image.png", self.current_denoise) #prompt currently turned off in image_gen_new.py

    def fade_between_images(self, old_image, new_image, steps=1, transition_time=0.01):
        """Fade from the current image to a new image."""
        if hasattr(self, 'current_img'):
            old_image = old_image.convert('RGBA')
        else:
            old_image = new_image.convert('RGBA')  # Use new_image as old_image if no current_img exists

        if old_image.size != new_image.size:
            new_image = new_image.resize(old_image.size)

        # Ensure the images have the same mode
        if old_image.mode != new_image.mode:
            new_image = new_image.convert(old_image.mode)

        new_image = new_image.convert('RGBA')
        self.current_img = new_image  # Update current image to new image

        for step in range(steps + 1):
            # Calculate alpha blend
            alpha = step / steps
            blended_image = Image.blend(old_image, new_image, alpha)
            self.tk_img = ImageTk.PhotoImage(blended_image)
            self.canvas.itemconfig(self.image_on_canvas, image=self.tk_img)
            self.canvas.update_idletasks()  # Update canvas
            time.sleep(transition_time / steps)

    def check_if_image_file(self):
        dir = '/home/lunkwill/projects/ComfyUI/output/my_output/'
        if os.path.exists(dir):
            files = os.listdir(dir)
            if len(files)>0:
                return True

    def update_image(self):
        left, top, right, bottom = 0, 0, 0, 0
        if self.old_image == "":
            self.old_image = self.current_img
        #doit = True
        #print("directory_state", self.shared_state.directory_state)
        just_got_new_image = False
        can_crop = False
        if self.shared_state.directory_state == "image":
            try:
                test_load = Image.open('/home/lunkwill/projects/ComfyUI/output/my_output/ComfyUI_0001.png')
                can_crop = True
            except Exception as e:
                print(f"Error cropping image precycle: {e}.")
        if self.shared_state.directory_state == "image" and can_crop:
            self.image_generating = False
            just_got_new_image = True
            self.current_img = Image.open('/home/lunkwill/projects/ComfyUI/output/my_output/ComfyUI_0001.png')
            #resize the image to dimensions
            if give_to_comfy_half:
                self.current_img = self.current_img.resize((dimensions, dimensions), Image.ANTIALIAS)
            length_backlog = len(self.xy_backlog)
            for i in range(length_backlog):
                left, top, right, bottom = self.handle_eyemovement_catchup(self.xy_backlog[i],length_backlog)
                print("i", i)
                self.super_zoom_current_image(self.current_img, left, top, right, bottom, length_backlog)
                #crop_helper.add_values(left, top, right, bottom)

            #left, top, right, bottom = crop_helper.calculate_averages()
            
            # files = os.listdir('/home/lunkwill/projects/ComfyUI/output/my_output')
            # #print("files", files)
            # for file in files:
            #     os.remove('/home/lunkwill/projects/ComfyUI/output/my_output/' + file)


            

            # Define the directory
            output_dir = Path('/home/lunkwill/projects/ComfyUI/output/my_output')

            # Iterate over each item in the directory
            for item in output_dir.iterdir():
                # Check if it is a file
                if item.is_file():
                    item.unlink()  # Delete the file
                    


            self.xy_backlog = []
        avg_x, avg_y = self.calculate_average_position()
        left, top, right, bottom = self.handle_eyemovement([avg_x, avg_y])
        print('normal zoom')
        self.zoom_current_image(self.current_img, left, top, right, bottom)
        if not just_got_new_image:
            self.xy_backlog.append([avg_x, avg_y])
        self.tk_img = ImageTk.PhotoImage(self.current_img)
        
        #self.fade_between_images(self.old_image, self.current_img, steps=5, transition_time=1)
        self.canvas.itemconfig(self.image_on_canvas, image=self.tk_img)
        

        if not self.image_generating and self.shared_state.directory_state == "empty":
            future = self.executor.submit(self.generate_image, avg_x, avg_y)
            self.current_denoise = (self.current_denoise + self.denoise_set_point) / 2

        self.old_image = self.current_img
        
        if not self.use_eye_tracking:
            self.master.after(100, self.update_image)

    def calculate_average_position(self):
        if self.position_smoothing:
            avg_x = sum(x for x, _ in self.position_smoothing) / len(self.position_smoothing)
            avg_y = sum(y for _, y in self.position_smoothing) / len(self.position_smoothing)
        else:
            avg_x, avg_y = self.eyetrack_x, self.eyetrack_y
        return avg_x, avg_y


    def start_eye_tracking(self):
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        master, slave = pty.openpty()
        subprocess_path = '/home/lunkwill/projects/tobii_eye_tracker_linux_installer/example/main'  # Update this path
        process = subprocess.Popen(subprocess_path, shell=True, stdout=slave, stderr=subprocess.PIPE, text=True, bufsize=1)
        os.close(slave)

        last_eye_data_time = SharedState()        


        #threading.Thread(target=self.watch_last_eye_data_time, args=(master, last_eye_data_time), daemon=True).start()

        threading.Thread(target=self.read_subprocess_output_and_update_gui, args=(master, screen_width, screen_height, last_eye_data_time), daemon=True).start()
        self.master.bind('<Configure>', lambda event: self.get_window_position())

        

    # def read_subprocess_output_and_update_gui(self, master_fd, screen_width, screen_height):
    #     global win_x, win_y
    #     with os.fdopen(master_fd, 'r') as stdout:
    #         for line in iter(stdout.readline, ''):
    #             parts = line.split(":")
    #             numbers = parts[1].split(",")

    #             x = float(numbers[0]) * screen_width
    #             y = float(numbers[1]) * screen_height

    #             image_x = x - win_x
    #             image_y = y - win_y

    #             # Update smoothed position
    #             self.position_smoothing.append((image_x, image_y))
    #             self.master.after(0, self.update_image)

    def watch_last_eye_data_time(self, master_fd, last_eye_data_time):
        while True:
            if time.time() - last_eye_data_time.last_eye_data_time > 2:
                print("No eye data for more than 1 second")
                self.current_denoise = (1+self.denoise_set_point)/2
                #make a beep sound
                sound = 'paplay /usr/share/sounds/freedesktop/stereo/complete.oga'
                os.system(sound)
                # Reset the position smoothing
                # self.position_smoothing = deque(maxlen=9)
                # self.master.after(0, self.update_image)
                time.sleep(1)

    def read_subprocess_output_and_update_gui(self, master_fd, screen_width, screen_height, last_eye_data_time):
        global win_x, win_y
        last_time = time.time()  # Initialize the time of the last data point
        timeout = 2.0  # Set the timeout to 1 second (or whatever value you want)

        with os.fdopen(master_fd, 'r') as stdout:
            for line in iter(stdout.readline, ''):
                last_eye_data_time.last_eye_data_time = time.time()
                current_time = time.time()  # Get the current time
                if current_time - last_time > timeout:
                    self.current_denoise = (1+self.denoise_set_point)/2
                    #make a beep sound
                    # sound = 'paplay /usr/share/sounds/freedesktop/stereo/complete.oga'
                    # os.system(sound)
                    print("Original Timeout: More than {} seconds since the last data point".format(timeout))

                last_time = current_time  # Update the time of the last data point

                parts = line.split(":")
                numbers = parts[1].split(",")

                x = float(numbers[0]) * screen_width
                y = float(numbers[1]) * screen_height

                image_x = x - win_x
                image_y = y - win_y

                # Update smoothed position
                self.position_smoothing.append((image_x, image_y))
                self.master.after(0, self.update_image)

    def get_window_position(self):
        global win_x, win_y
        win_x = self.master.winfo_x()
        win_y = self.master.winfo_y()

class SharedState:
    def __init__(self):
        self.directory_state = "empty"
        self.last_eye_data_time = 0

class CropHelper:
    def __init__(self):
        self.left_values = []
        self.top_values = []
        self.right_values = []
        self.bottom_values = []

    def add_values(self, left, top, right, bottom):
        self.left_values.append(left)
        self.top_values.append(top)
        self.right_values.append(right)
        self.bottom_values.append(bottom)

    def calculate_averages(self):
        avg_left = sum(self.left_values) / len(self.left_values)
        avg_top = sum(self.top_values) / len(self.top_values)
        avg_right = sum(self.right_values) / len(self.right_values)
        avg_bottom = sum(self.bottom_values) / len(self.bottom_values)

        return avg_left, avg_top, avg_right, avg_bottom
    
    def reset_values(self):
        self.left_values = []
        self.top_values = []
        self.right_values = []
        self.bottom_values = []

def on_closing():
    app.shutdown()
    root.destroy()

def get_random_image(dir_path):
    # Get a list of all files in the directory
    files = os.listdir(dir_path)

    # Filter out any non-image files
    images = [file for file in files if file.endswith(('.png', '.jpg', '.jpeg'))]

    # Select a random image
    random_image = random.choice(images)

    # Return the full path of the random image
    return os.path.join(dir_path, random_image)

# Usage example
if __name__ == "__main__":
    #delete any remainging files in the output directory
    files = os.listdir('/home/lunkwill/projects/ComfyUI/output/my_output')
    for file in files:
        os.remove('/home/lunkwill/projects/ComfyUI/output/my_output/' + file)

    path_to_watch = '/home/lunkwill/projects/ComfyUI/output/my_output'  # Update this to the path you want to monitor

    # Create a shared state object
    shared_state = SharedState()

    # Create a thread to monitor the directory
    thread = threading.Thread(target=_directory_watchdog.start_monitoring, args=(path_to_watch, shared_state))
    thread.daemon = True
    thread.start()
    
    root = tk.Tk()
    root.title("Eye Tracking Zoom")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    #use the random library to choose an image in here 
    
    dir_path = '/home/lunkwill/Pictures/Wallpapers/ai_art'
    image_path = get_random_image(dir_path)
    

    #create a new image with the dimensions variable and the image_path
    img = Image.open(image_path)
    img = img.resize((dimensions, dimensions), Image.ANTIALIAS)
    img.save(image_path.replace(".png", "_resized.png"))
    new_path = image_path.replace(".png", "_resized.png")

    crop_helper = CropHelper()

    # Ensure to update the path to your image and eye tracking executable as needed
    app = ZoomApp(root, new_path, shared_state, crop_helper, use_eye_tracking=True)

    root.mainloop()
