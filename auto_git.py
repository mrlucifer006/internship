import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    """Logs all the events captured."""

    def on_any_event(self, event):
        if event.is_directory:
            return
        if '.git' in event.src_path:
            return
        
        print(f"Detected change in: {event.src_path}")
        self.execute_git_commands()

    def execute_git_commands(self):
        try:
            print("Adding changes...")
            subprocess.run(["git", "add", "."], check=True)
            
            print("Committing changes...")
            commit_message = "Auto-commit: File changes detected"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            print("Pulling changes from remote...")
            try:
                subprocess.run(["git", "pull"], check=True)
            except subprocess.CalledProcessError:
                print("Warning: git pull failed (possibly conflicts). Continuing to push...")

            print("Pushing changes...")
            subprocess.run(["git", "push"], check=True)
            
            print("Git operations completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during Git operations: {e}")
        except FileNotFoundError:
            print("Error: 'git' command not found. Please ensure Git is installed and in your PATH.")

if __name__ == "__main__":
    path = '.'
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    print("Starting file watcher...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()
    print("File watcher stopped.")
