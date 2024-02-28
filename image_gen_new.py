import json
from urllib import request, parse
import random
import time
import os

def queue_prompt(prompt_workflow):
    print("queue_prompt")
    p = {"prompt": prompt_workflow}
    data = json.dumps(p).encode('utf-8')
    req = request.Request("http://127.0.0.1:8188/prompt", data=data)
    try:
        request.urlopen(req)
    except Exception as e:
        print(f"Failed to send request: {e}")

def create_img(prompt, img_path, img_path_clip):

    # read workflow api data from file and convert it into dictionary 
    # assign to var prompt_workflow
    prompt_workflow = json.load(open('/home/lunkwill/projects/tobii/turboTwoIMGCLIP.json'))

    # create a list of prompts
    prompt_list = []
    prompt_list.append(prompt)

    # chkpoint_loader_node = prompt_workflow["4"]
    prompt_pos_node = prompt_workflow["6"]
    # empty_latent_img_node = prompt_workflow["5"]
    ksampler_node = prompt_workflow["13"]
    #save_image_node = prompt_workflow["55"]

    input_image_file = prompt_workflow["54"]

    clip_input_image_file = prompt_workflow["69"]

    filepaths = []
    # for every prompt in prompt_list...
    for index, prompt in enumerate(prompt_list):

        # set the text prompt for positive CLIPTextEncode node
        #prompt_pos_node["inputs"]["text"] = prompt

        input_image_file["inputs"]["image"] = img_path

        clip_input_image_file["inputs"]["image"] = img_path_clip

        seed = random.randint(1, 18446744073709551614)
        print("prompt", prompt_pos_node["inputs"]["text"])

        # set a random seed in KSampler node 
        ksampler_node["inputs"]["noise_seed"] = seed

        fileprefix = prompt.replace(" ", "_")
        if len(fileprefix) > 80:
            fileprefix = fileprefix[:80]

        #save_image_node["inputs"]["filename_prefix"] = fileprefix
        #save_image_node["inputs"]["filename_prefix"] = "/home/lunkwill/projects/tobii/output/output.png"
        #make a random number
        #filepaths.append("/home/lunkwill/projects/ComfyUI/output/"+fileprefix+"_"+str(seed)+".png")

    # everything set, add entire workflow to queue.
    queue_prompt(prompt_workflow)

    #return filepaths

# create_new_banner("Bioacoustics Resources")
# create_new_banner("Bioacoustics Resources2")
# create_img("cat", "/home/lunkwill/Pictures/Wallpapers/ai_art/_There's_a_peculiar_pattern_of_latex_on_the_30-yea_1_0.png")

# Monitor for new files
def monitor_output_directory(output_dir, callback):
    files_before = set(os.listdir(output_dir))
    while True:
        time.sleep(1)  # Adjust the sleep time as needed
        files_after = set(os.listdir(output_dir))
        new_files = files_after - files_before
        if new_files:
            callback(new_files)
            files_before = files_after

def handle_new_files(new_files):
    print("New files detected:", new_files)
    # Process new files as needed

if __name__ == "__main__":
    output_dir = "/home/lunkwill/projects/ComfyUI/output"
    monitor_output_directory(output_dir, handle_new_files)
