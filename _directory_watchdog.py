from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time

class WatchDirectoryHandler(FileSystemEventHandler):
    def __init__(self, shared_state):
        super().__init__()
        self.shared_state = shared_state

    def on_created(self, event):
        print(f'New file created: {event.src_path}')
        # Update the shared variable
        time.sleep(1)
        self.shared_state.directory_state = "image"

    def on_deleted(self, event):
        print(f'File deleted: {event.src_path}')
        # Update the shared variable for deletion
        self.shared_state.directory_state = "empty"

def start_monitoring(path, shared_state):
    event_handler = WatchDirectoryHandler(shared_state)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()

# if __name__ == '__main__':
#     path_to_watch = '/home/lunkwill/projects/ComfyUI/output/my_output'  # Update this to the path you want to monitor

#     # Create a shared state object
#     shared_state = SharedState()

#     # Create a thread to monitor the directory
#     thread = threading.Thread(target=start_monitoring, args=(path_to_watch, shared_state))
#     thread.daemon = True
#     thread.start()

#     print("Monitoring has started. Main program continues here.")

#     # Example: Main program using the shared variable
#     try:
#         while True:
#             if shared_state.directory_state == "image":
#                 print("Main program detected new file.")
#                 # Reset or remove the entry to avoid repetitive processing
#                 shared_state.directory_state = "empty"

#             # Simulate main program work with a sleep or other operations
#     except KeyboardInterrupt:
#         print("Program terminated by user.")