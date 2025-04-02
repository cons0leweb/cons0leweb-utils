import os
import logging
import shutil
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinter.font import Font
import random
import string
import hashlib
import time
from datetime import datetime
import json
from typing import List, Tuple, Optional, Dict, Callable
import webbrowser

# Constants
CONFIG_FILE = "cons0leweb_utils_config.json"
DEFAULT_EXTENSIONS = ['.txt', '.html', '.css', '.js', '.py', '.json']
MAX_THREADS = 8
MAX_FILE_SIZE_MB = 10  # Default max file size in MB
BACKUP_EXTENSION = '.bak.cu'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cons0leweb_utils.log'),
        logging.StreamHandler()
    ]
)

class FileProcessor:
    """Core file processing functionality with thread safety and error handling"""
    
    def __init__(self):
        self.file_queue = queue.Queue()
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
        self.progress = {"total": 0, "processed": 0, "errors": 0}
        
    def start_workers(self, num_threads: int = MAX_THREADS):
        """Start worker threads for parallel processing"""
        self.running = True
        for _ in range(num_threads):
            worker = threading.Thread(target=self._worker)
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def stop_workers(self):
        """Stop all worker threads"""
        self.running = False
        for _ in range(len(self.workers)):
            self.file_queue.put(None)
        for worker in self.workers:
            worker.join()
        self.workers = []
    
    def _worker(self):
        """Worker thread that processes files from the queue"""
        while self.running:
            task = self.file_queue.get()
            if task is None:
                break
                
            try:
                func, args, kwargs = task
                func(*args, **kwargs)
                with self.lock:
                    self.progress["processed"] += 1
            except Exception as e:
                logging.error(f"Error processing task: {e}")
                with self.lock:
                    self.progress["errors"] += 1
            finally:
                self.file_queue.task_done()
    
    def add_task(self, func: Callable, *args, **kwargs):
        """Add a task to the processing queue"""
        self.file_queue.put((func, args, kwargs))
        with self.lock:
            self.progress["total"] += 1
    
    def get_progress(self) -> Dict[str, int]:
        """Get current processing progress"""
        with self.lock:
            return self.progress.copy()
    
    def reset_progress(self):
        """Reset progress counters"""
        with self.lock:
            self.progress = {"total": 0, "processed": 0, "errors": 0}

class FileOperations:
    """Static class for file operations with enhanced functionality"""
    
    @staticmethod
    def add_text_to_file(file_path: str, text: str, position: str = "start", 
                        create_backup: bool = True, encoding: str = "utf-8") -> bool:
        """Add text to file at specified position with backup option"""
        try:
            if create_backup:
                FileOperations.create_backup(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            with open(file_path, 'w', encoding=encoding) as f:
                if position == "start":
                    f.write(text + "\n" + content)
                elif position == "end":
                    f.write(content + "\n" + text)
                elif position == "random":
                    lines = content.splitlines()
                    insert_pos = random.randint(0, len(lines))
                    lines.insert(insert_pos, text)
                    f.write("\n".join(lines))
            
            logging.info(f"Text added to {position} of {file_path}")
            return True
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return False
    
    @staticmethod
    def create_backup(file_path: str) -> Optional[str]:
        """Create a backup of the file with timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{file_path}_{timestamp}{BACKUP_EXTENSION}"
            shutil.copy2(file_path, backup_path)
            logging.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup failed for {file_path}: {e}")
            return None
    
    @staticmethod
    def restore_backup(backup_path: str) -> bool:
        """Restore file from backup"""
        try:
            if not backup_path.endswith(BACKUP_EXTENSION):
                logging.error(f"Invalid backup file: {backup_path}")
                return False
                
            original_path = backup_path[:-len(BACKUP_EXTENSION)]
            shutil.copy2(backup_path, original_path)
            logging.info(f"Restored {original_path} from backup")
            return True
        except Exception as e:
            logging.error(f"Restore failed for {backup_path}: {e}")
            return False
    
    @staticmethod
    def create_dummy_file(folder_path: str, extension: str, 
                        name_type: str = "random", content: str = "") -> Optional[str]:
        """Create a dummy file with specified parameters"""
        try:
            os.makedirs(folder_path, exist_ok=True)
            
            if name_type == "random":
                filename = f"{''.join(random.choices(string.ascii_letters, k=8))}.{extension}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dummy_{timestamp}.{extension}"
            
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'w') as f:
                if content:
                    f.write(content)
                else:
                    # Generate some random content
                    f.write(f"This is a dummy {extension} file created on {datetime.now()}\n")
                    f.write("".join(random.choices(string.ascii_letters + string.digits + " \n", k=100)))
            
            logging.info(f"Created dummy file: {file_path}")
            return file_path
        except Exception as e:
            logging.error(f"Error creating dummy file: {e}")
            return None
    
    @staticmethod
    def calculate_checksum(file_path: str, algorithm: str = "md5") -> Optional[str]:
        """Calculate file checksum using specified algorithm"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating checksum for {file_path}: {e}")
            return None
    
    @staticmethod
    def batch_rename(folder_path: str, pattern: str, 
                    extensions: List[str], recursive: bool = False) -> int:
        """Batch rename files with specified pattern"""
        renamed = 0
        
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if any(filename.endswith(ext) for ext in extensions):
                    try:
                        name, ext = os.path.splitext(filename)
                        new_name = pattern.replace("{n}", name)
                        new_name = new_name.replace("{d}", datetime.now().strftime("%Y%m%d"))
                        new_name = new_name.replace("{t}", datetime.now().strftime("%H%M%S"))
                        new_name = new_name.replace("{r}", ''.join(random.choices(string.ascii_letters, k=4)))
                        
                        src = os.path.join(root, filename)
                        dst = os.path.join(root, f"{new_name}{ext}")
                        
                        if src != dst:
                            os.rename(src, dst)
                            renamed += 1
                    except Exception as e:
                        logging.error(f"Error renaming {filename}: {e}")
            
            if not recursive:
                break
                
        return renamed

class ModernUI(tk.Tk):
    """Modern Tkinter UI with improved styling and functionality"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Cons0leweb Utils")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom fonts
        self.title_font = Font(family="Helvetica", size=12, weight="bold")
        self.label_font = Font(family="Helvetica", size=10)
        self.button_font = Font(family="Helvetica", size=10, weight="bold")
        
        # Configure colors
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=self.label_font)
        self.style.configure('TButton', font=self.button_font, padding=5)
        self.style.configure('TEntry', padding=5)
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', padding=[10, 5], font=self.button_font)
        
        # Initialize file processor
        self.processor = FileProcessor()
        
        # Load config
        self.config = self.load_config()
        
        # Build UI
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
        return {
            "recent_folders": [],
            "default_extensions": DEFAULT_EXTENSIONS,
            "max_file_size": MAX_FILE_SIZE_MB
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def on_close(self):
        """Handle window close event"""
        self.processor.stop_workers()
        self.save_config()
        self.destroy()
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_text_tab()
        self.create_files_tab()
        self.create_rename_tab()
        self.create_checksum_tab()
        self.create_log_tab()
        
        # Status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(self.status_frame, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Start progress updater
        self.update_progress()
    
    def create_text_tab(self):
        """Create the text processing tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Text Processing")
        
        # Text input section
        input_frame = ttk.LabelFrame(tab, text="Text Configuration", padding=10)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Text to add:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.text_entry = ttk.Entry(input_frame, width=60)
        self.text_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2)
        
        ttk.Label(input_frame, text="Position:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.position_var = tk.StringVar(value="start")
        ttk.Radiobutton(input_frame, text="Start", variable=self.position_var, value="start").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="End", variable=self.position_var, value="end").grid(row=1, column=2, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Random", variable=self.position_var, value="random").grid(row=1, column=3, sticky=tk.W)
        
        # File selection section
        file_frame = ttk.LabelFrame(tab, text="File Selection", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.folder_entry = ttk.Entry(file_frame)
        self.folder_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(file_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2, padx=5)
        
        ttk.Label(file_frame, text="Extensions (comma separated):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.extensions_entry = ttk.Entry(file_frame)
        self.extensions_entry.insert(0, ",".join(self.config["default_extensions"]))
        self.extensions_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(file_frame, text="Max file size (MB):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.max_size_entry = ttk.Entry(file_frame)
        self.max_size_entry.insert(0, str(self.config["max_file_size"]))
        self.max_size_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        self.subfolders_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_frame, text="Include subfolders", variable=self.subfolders_var).grid(row=2, column=2, sticky=tk.W)
        
        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_frame, text="Create backups", variable=self.backup_var).grid(row=2, column=3, sticky=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(tab)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Process Files", command=self.process_files, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Restore Backups", command=self.restore_backups).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        file_frame.columnconfigure(1, weight=1)
    
    def create_files_tab(self):
        """Create the file operations tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="File Operations")
        
        # Dummy files section
        dummy_frame = ttk.LabelFrame(tab, text="Create Dummy Files", padding=10)
        dummy_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dummy_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dummy_folder_entry = ttk.Entry(dummy_frame)
        self.dummy_folder_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(dummy_frame, text="Browse", command=lambda: self.browse_folder(self.dummy_folder_entry)).grid(row=0, column=2, padx=5)
        
        ttk.Label(dummy_frame, text="Number of files:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.dummy_num_entry = ttk.Entry(dummy_frame)
        self.dummy_num_entry.insert(0, "10")
        self.dummy_num_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(dummy_frame, text="Extension:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.dummy_ext_entry = ttk.Entry(dummy_frame)
        self.dummy_ext_entry.insert(0, "txt")
        self.dummy_ext_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(dummy_frame, text="Naming:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.dummy_name_var = tk.StringVar(value="random")
        ttk.Radiobutton(dummy_frame, text="Random", variable=self.dummy_name_var, value="random").grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(dummy_frame, text="Sequential", variable=self.dummy_name_var, value="sequential").grid(row=3, column=2, sticky=tk.W)
        
        ttk.Button(dummy_frame, text="Create Files", command=self.create_dummy_files).grid(row=4, column=1, pady=5)
        
        # File operations section
        ops_frame = ttk.LabelFrame(tab, text="File Operations", padding=10)
        ops_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(ops_frame, text="Delete Empty Files", command=self.delete_empty_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_frame, text="Find Duplicates", command=self.find_duplicates).pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        dummy_frame.columnconfigure(1, weight=1)
    
    def create_rename_tab(self):
        """Create the batch rename tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Batch Rename")
        
        # Rename configuration
        rename_frame = ttk.LabelFrame(tab, text="Rename Settings", padding=10)
        rename_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rename_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.rename_folder_entry = ttk.Entry(rename_frame)
        self.rename_folder_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(rename_frame, text="Browse", command=lambda: self.browse_folder(self.rename_folder_entry)).grid(row=0, column=2, padx=5)
        
        ttk.Label(rename_frame, text="Pattern:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.rename_pattern_entry = ttk.Entry(rename_frame)
        self.rename_pattern_entry.insert(0, "{n}_{d}_{r}")
        self.rename_pattern_entry.grid(row=1, column=1, sticky=tk.EW, pady=2)
        
        ttk.Label(rename_frame, text="Available placeholders:").grid(row=2, column=0, sticky=tk.W, pady=2)
        placeholders = ttk.Label(rename_frame, text="{n}=original name, {d}=date, {t}=time, {r}=random")
        placeholders.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(rename_frame, text="Extensions:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.rename_ext_entry = ttk.Entry(rename_frame)
        self.rename_ext_entry.insert(0, ",".join(DEFAULT_EXTENSIONS))
        self.rename_ext_entry.grid(row=3, column=1, sticky=tk.EW, pady=2)
        
        self.rename_recursive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rename_frame, text="Include subfolders", variable=self.rename_recursive_var).grid(row=4, column=1, sticky=tk.W)
        
        ttk.Button(rename_frame, text="Preview Rename", command=self.preview_rename).grid(row=5, column=1, pady=5, sticky=tk.W)
        ttk.Button(rename_frame, text="Execute Rename", command=self.execute_rename).grid(row=5, column=2, pady=5, sticky=tk.W)
        
        # Preview area
        preview_frame = ttk.LabelFrame(tab, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        rename_frame.columnconfigure(1, weight=1)
    
    def create_checksum_tab(self):
        """Create the checksum verification tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Checksum")
        
        # Checksum configuration
        checksum_frame = ttk.LabelFrame(tab, text="Checksum Settings", padding=10)
        checksum_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(checksum_frame, text="Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.checksum_folder_entry = ttk.Entry(checksum_frame)
        self.checksum_folder_entry.grid(row=0, column=1, sticky=tk.EW, pady=2)
        ttk.Button(checksum_frame, text="Browse", command=lambda: self.browse_folder(self.checksum_folder_entry)).grid(row=0, column=2, padx=5)
        
        ttk.Label(checksum_frame, text="Algorithm:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.checksum_algo_var = tk.StringVar(value="md5")
        ttk.Combobox(checksum_frame, textvariable=self.checksum_algo_var, 
                     values=["md5", "sha1", "sha256", "sha512"]).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Button(checksum_frame, text="Calculate Checksums", command=self.calculate_checksums).grid(row=2, column=1, pady=5, sticky=tk.W)
        
        # Results area
        results_frame = ttk.LabelFrame(tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.checksum_text = scrolledtext.ScrolledText(results_frame, height=10)
        self.checksum_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        checksum_frame.columnconfigure(1, weight=1)
    
    def create_log_tab(self):
        """Create the log viewer tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Log Viewer")
        
        # Log controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Refresh", command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Open Log File", command=self.open_log_file).pack(side=tk.LEFT, padx=5)
        
        # Log display
        log_frame = ttk.LabelFrame(tab, text="Application Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Load initial logs
        self.refresh_logs()
    
    def browse_folder(self, entry_widget=None):
        """Browse for folder and update the specified entry widget"""
        folder = filedialog.askdirectory()
        if folder:
            if entry_widget:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, folder)
            else:
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder)
            
            # Add to recent folders
            if folder not in self.config["recent_folders"]:
                self.config["recent_folders"].insert(0, folder)
                self.config["recent_folders"] = self.config["recent_folders"][:5]
    
    def process_files(self):
        """Process files with text addition"""
        folder = self.folder_entry.get()
        text = self.text_entry.get()
        position = self.position_var.get()
        extensions = [ext.strip() for ext in self.extensions_entry.get().split(",")]
        max_size = int(self.max_size_entry.get()) * 1024 * 1024  # Convert MB to bytes
        recursive = self.subfolders_var.get()
        create_backup = self.backup_var.get()
        
        if not folder or not text:
            messagebox.showwarning("Input Error", "Please specify folder and text")
            return
        
        # Start worker threads
        self.processor.start_workers()
        self.processor.reset_progress()
        
        # Walk through folder and add tasks
        for root, dirs, files in os.walk(folder):
            for filename in files:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in extensions:
                    file_path = os.path.join(root, filename)
                    if os.path.getsize(file_path) <= max_size:
                        self.processor.add_task(
                            FileOperations.add_text_to_file,
                            file_path, text, position, create_backup
                        )
            
            if not recursive:
                break
        
        messagebox.showinfo("Processing", f"Added {self.processor.progress['total']} files to queue")
    
    def restore_backups(self):
        """Restore files from backups"""
        folder = self.folder_entry.get()
        if not folder:
            messagebox.showwarning("Input Error", "Please specify folder")
            return
        
        # Start worker threads
        self.processor.start_workers()
        self.processor.reset_progress()
        
        # Walk through folder and restore backups
        for root, _, files in os.walk(folder):
            for filename in files:
                if filename.endswith(BACKUP_EXTENSION):
                    backup_path = os.path.join(root, filename)
                    self.processor.add_task(
                        FileOperations.restore_backup,
                        backup_path
                    )
        
        messagebox.showinfo("Processing", f"Found {self.processor.progress['total']} backups to restore")
    
    def create_dummy_files(self):
        """Create dummy files"""
        folder = self.dummy_folder_entry.get()
        num_files = int(self.dummy_num_entry.get())
        extension = self.dummy_ext_entry.get()
        name_type = self.dummy_name_var.get()
        
        if not folder:
            messagebox.showwarning("Input Error", "Please specify folder")
            return
        
        # Start worker threads
        self.processor.start_workers()
        self.processor.reset_progress()
        
        # Add tasks for dummy files
        for _ in range(num_files):
            self.processor.add_task(
                FileOperations.create_dummy_file,
                folder, extension, name_type
            )
        
        messagebox.showinfo("Processing", f"Creating {num_files} dummy files")
    
    def delete_empty_files(self):
        """Delete empty files in folder"""
        folder = self.dummy_folder_entry.get()
        if not folder:
            messagebox.showwarning("Input Error", "Please specify folder")
            return
        
        deleted = 0
        for root, _, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.getsize(file_path) == 0:
                    try:
                        os.remove(file_path)
                        deleted += 1
                    except Exception as e:
                        logging.error(f"Error deleting {file_path}: {e}")
        
        messagebox.showinfo("Complete", f"Deleted {deleted} empty files")
    
    def find_duplicates(self):
        """Find duplicate files in folder"""
        folder = self.dummy_folder_entry.get()
        if not folder:
            messagebox.showwarning("Input Error", "Please specify folder")
            return
        
        hashes = {}
        duplicates = []
        
        for root, _, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_hash = FileOperations.calculate_checksum(file_path)
                    if file_hash in hashes:
                        duplicates.append((file_path, hashes[file_hash]))
                    else:
                        hashes[file_hash] = file_path
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {e}")
        
        if duplicates:
            result = "Duplicate files found:\n\n"
            for dup, original in duplicates:
                result += f"{dup} is duplicate of {original}\n"
            
            # Show results in a scrollable dialog
            self.show_scrollable_message("Duplicate Files", result)
        else:
            messagebox.showinfo("No Duplicates", "No duplicate files found")
    
    def preview_rename(self):
        """Preview batch rename operation"""
        folder = self.rename_folder_entry.get()
        pattern = self.rename_pattern_entry.get()
        extensions = [ext.strip() for ext in self.rename_ext_entry.get().split(",")]
        recursive = self.rename_recursive_var.get()
        
        if not folder or not pattern:
            messagebox.showwarning("Input Error", "Please specify folder and pattern")
            return
        
        preview = []
        
        for root, _, files in os.walk(folder):
            for filename in files:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in extensions:
                    old_path = os.path.join(root, filename)
                    name, ext = os.path.splitext(filename)
                    
                    new_name = pattern
                    new_name = new_name.replace("{n}", name)
                    new_name = new_name.replace("{d}", datetime.now().strftime("%Y%m%d"))
                    new_name = new_name.replace("{t}", datetime.now().strftime("%H%M%S"))
                    new_name = new_name.replace("{r}", ''.join(random.choices(string.ascii_letters, k=4)))
                    
                    new_path = os.path.join(root, f"{new_name}{ext}")
                    
                    preview.append(f"{old_path} -> {new_path}")
            
            if not recursive:
                break
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, "\n".join(preview) if preview else "No files to rename")
    
    def execute_rename(self):
        """Execute batch rename operation"""
        folder = self.rename_folder_entry.get()
        pattern = self.rename_pattern_entry.get()
        extensions = [ext.strip() for ext in self.rename_ext_entry.get().split(",")]
        recursive = self.rename_recursive_var.get()
        
        if not folder or not pattern:
            messagebox.showwarning("Input Error", "Please specify folder and pattern")
            return
        
        renamed = FileOperations.batch_rename(folder, pattern, extensions, recursive)
        messagebox.showinfo("Complete", f"Renamed {renamed} files")
        self.preview_rename()  # Refresh preview
    
    def calculate_checksums(self):
        """Calculate checksums for files in folder"""
        folder = self.checksum_folder_entry.get()
        algorithm = self.checksum_algo_var.get()
        
        if not folder:
            messagebox.showwarning("Input Error", "Please specify folder")
            return
        
        results = []
        
        for root, _, files in os.walk(folder):
            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    checksum = FileOperations.calculate_checksum(file_path, algorithm)
                    results.append(f"{filename}: {checksum}")
                except Exception as e:
                    results.append(f"{filename}: ERROR - {str(e)}")
        
        self.checksum_text.delete(1.0, tk.END)
        self.checksum_text.insert(tk.END, "\n".join(results) if results else "No files processed")
    
    def refresh_logs(self):
        """Refresh log display"""
        try:
            with open('cons0leweb_utils.log', 'r') as f:
                logs = f.read()
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, logs)
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"Error loading logs: {str(e)}")
    
    def clear_logs(self):
        """Clear log file"""
        try:
            with open('cons0leweb_utils.log', 'w'):
                pass
            self.refresh_logs()
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear logs: {str(e)}")
    
    def open_log_file(self):
        """Open log file in default editor"""
        try:
            webbrowser.open('cons0leweb_utils.log')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {str(e)}")
    
    def show_scrollable_message(self, title, message):
        """Show a message in a scrollable dialog"""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        
        text = scrolledtext.ScrolledText(dialog, width=80, height=20)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, message)
        text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
    
    def update_progress(self):
        """Update progress bar and status"""
        progress = self.processor.get_progress()
        
        if progress["total"] > 0:
            percent = (progress["processed"] / progress["total"]) * 100
            self.progress_bar["value"] = percent
            self.status_label.config(
                text=f"Processed {progress['processed']} of {progress['total']} files ({progress['errors']} errors)"
            )
        else:
            self.progress_bar["value"] = 0
            self.status_label.config(text="Ready")
        
        self.after(500, self.update_progress)

if __name__ == "__main__":
    app = ModernUI()
    app.mainloop()
