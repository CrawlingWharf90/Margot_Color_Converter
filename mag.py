import argparse
import sys
import os
import subprocess
import winreg
import ctypes

CYAN = '\033[96m'
RESET = '\033[0m'

def clear_terminal():
    command = "cls" if os.name == "nt" else "clear"
    os.system(command)

#* ==========================================
#* 1. MAIN APPLICATION LAUNCHER
#* ==========================================
def launch_app():
    print("Launching Margot Color Converter ᓚᘏᗢ<(meow)")
    try:
        from margot import Margot, ctk
        ctk.set_appearance_mode("dark")
        app = Margot()
        app.mainloop()
    except ImportError:
        print("Error: Required libraries not found.")
        print("Please run 'mag --setup' first to install dependencies.")
        sys.exit(1)

#* ==========================================
#* 2. SETUP & ENVIRONMENT PIPELINE
#* ==========================================
def setup_environment():
    print("Starting environment setup...\n")
    
    #? --- Install Requirements ---
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"[!] Error: Could not find '{req_file}' in the current directory.")
        sys.exit(1)
        
    print(f"[*] Installing dependencies from {req_file}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        print("[*] Dependencies installed successfully!\n")
    except subprocess.CalledProcessError:
        print("[!] Failed to install dependencies. Please check your requirements.txt.")
        sys.exit(1)
        
    #! --- Global PATH Configuration ---
    choice = input(f"{CYAN}Do you want to add this tool to your global PATH to run 'mag' from anywhere? (y/n): {RESET}").strip().lower()
    if choice in ['y', 'yes']:
        add_to_user_path()
    else:
        print("Skipped adding to PATH. You can still run the script locally.")

def add_to_user_path():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
        
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""
            
        if current_dir in current_path.split(os.pathsep):
            print(f"\n[Info] {current_dir} is already in your PATH.")
            winreg.CloseKey(key)
            return
            
        new_path = f"{current_path}{os.pathsep}{current_dir}" if current_path else current_dir
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)
        
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, None
        )
        
        print(f"\n[Success] Added {current_dir} to your User PATH.")
        print("[Action Required] You will need to open a NEW terminal window to use the 'mag' command globally.")
        
    except Exception as e:
        print(f"\n[!] Failed to update PATH automatically: {e}")
        print(f"You can add it manually. The path is: {current_dir}")

#* ==========================================
#* 3. CLI ARGUMENT PARSER
#* ==========================================
def main():
    clear_terminal()
    parser = argparse.ArgumentParser(
        description="CLI Utility wrapper for Ink Shifter Pro."
    )
    
    parser.add_argument(
        "-r", "--run", 
        action="store_true", 
        help="Launch the graphical interface for the color compensator."
    )
    
    parser.add_argument(
        "-s", "--setup", 
        action="store_true", 
        help="Install dependencies and setup global execution."
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.setup:
        setup_environment()
    elif args.run:
        launch_app()

if __name__ == "__main__":
    main()