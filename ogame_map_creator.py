import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import requests
from typing import Set, Dict, List

class XMLFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ogame map creator")
        self.root.geometry("600x950")
        
        self.players_url = tk.StringVar()
        self.planets_url = tk.StringVar()
        self.highscore_url = tk.StringVar()
        self.coords_only = tk.BooleanVar(value=False)
        self.use_highscore = tk.BooleanVar(value=False)
        self.min_score = tk.StringVar(value="0")
        
        self.help_text = """Instruction:

1. Enter the URLs to the XML files in the appropriate fields
2. Select player statuses to exclude
3. Optionally enable highscore filtering and set minimum points
4. Optionally check the option to show only unique coordinates
5. Set the name of the output file
6. Click 'Process Data' to process the data

The filtered data will be saved to a file with the indicated name."""

        self.status_labels = {
            'i': 'Inactive (7d)',
            'I': 'Inactive (28d)',
            'v': 'Vacation (<7d)',
            'vi': 'Vacation (7d)',
            'vI': 'Vacation (28d)',
            'a': 'Admin',
            'vib': 'Banned (Temp)',
            'vIb': 'Banned (Perm)'
        }
        
        self.status_vars = {
            'i': tk.BooleanVar(value=True),
            'I': tk.BooleanVar(value=True),
            'v': tk.BooleanVar(value=True),
            'vi': tk.BooleanVar(value=True),
            'vI': tk.BooleanVar(value=True),
            'a': tk.BooleanVar(value=True),
            'vib': tk.BooleanVar(value=True),
            'vIb': tk.BooleanVar(value=True)
        }
        
        self.create_gui()
        
    def create_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="URLs Configuration", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, pady=10, sticky=tk.W)
        
        ttk.Label(main_frame, text="Players XML URL:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.players_url, width=70).grid(row=2, column=0, pady=5)
        
        ttk.Label(main_frame, text="Universe XML URL:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.planets_url, width=70).grid(row=4, column=0, pady=5)
        
        ttk.Label(main_frame, text="Status Filter Configuration", font=('Helvetica', 12, 'bold')).grid(row=5, column=0, pady=10, sticky=tk.W)
        ttk.Label(main_frame, text="Select statuses to exclude:").grid(row=6, column=0, sticky=tk.W)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=7, column=0, pady=5, sticky=tk.W)
        
        for i, (status, label) in enumerate(self.status_labels.items()):
            ttk.Checkbutton(
                status_frame, 
                text=label,
                variable=self.status_vars[status]
            ).grid(row=i//2, column=i%2, padx=10, pady=5, sticky=tk.W)

        ttk.Label(main_frame, text="Highscore Filter Configuration", font=('Helvetica', 12, 'bold')).grid(row=8, column=0, pady=10, sticky=tk.W)
        
        highscore_frame = ttk.Frame(main_frame)
        highscore_frame.grid(row=9, column=0, pady=5, sticky=tk.W)
        
        ttk.Checkbutton(
            highscore_frame,
            text="Enable highscore filtering",
            variable=self.use_highscore,
            command=self.toggle_highscore_fields
        ).grid(row=0, column=0, sticky=tk.W)
        
        self.highscore_url_label = ttk.Label(highscore_frame, text="Highscore XML URL:")
        self.highscore_url_entry = ttk.Entry(highscore_frame, textvariable=self.highscore_url, width=70)
        
        self.min_score_label = ttk.Label(highscore_frame, text="Minimum points:")
        self.min_score_entry = ttk.Entry(highscore_frame, textvariable=self.min_score, width=20)
        self.min_score_entry.bind('<KeyRelease>', self.format_score)
        
        ttk.Label(main_frame, text="Output Format Configuration", font=('Helvetica', 12, 'bold')).grid(row=10, column=0, pady=10, sticky=tk.W)
        ttk.Checkbutton(
            main_frame,
            text="Show only solar systems",
            variable=self.coords_only
        ).grid(row=11, column=0, pady=5, sticky=tk.W)
        
        ttk.Label(main_frame, text="Output Configuration", font=('Helvetica', 12, 'bold')).grid(row=12, column=0, pady=10, sticky=tk.W)
        
        ttk.Label(main_frame, text="Output file name:").grid(row=13, column=0, sticky=tk.W)
        self.output_file = ttk.Entry(main_frame, width=70)
        self.output_file.insert(0, "ogame_map.txt")
        self.output_file.grid(row=14, column=0, pady=5)
        
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=15, column=0, pady=20)
        
        ttk.Button(buttons_frame, text="Process Data", command=self.process_data).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text="Help", command=self.show_help).grid(row=0, column=1, padx=5)
        
        ttk.Label(main_frame, text="Processing Log:", font=('Helvetica', 12, 'bold')).grid(row=16, column=0, pady=10, sticky=tk.W)
        self.log_area = tk.Text(main_frame, height=10, width=60)
        self.log_area.grid(row=17, column=0, pady=5)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_area.yview)
        scrollbar.grid(row=17, column=1, sticky=(tk.N, tk.S))
        self.log_area.configure(yscrollcommand=scrollbar.set)

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("500x700")
        
        help_frame = ttk.Frame(help_window, padding="10")
        help_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(help_frame, text="Instruction:", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, pady=10, sticky=tk.W)
        help_text = tk.Text(help_frame, height=10, width=50, wrap=tk.WORD)
        help_text.grid(row=1, column=0, pady=5)
        help_text.insert(tk.END, self.help_text)
        help_text.config(state='disabled')
        
        ttk.Label(help_frame, text="URLs examples:", font=('Helvetica', 12, 'bold')).grid(row=2, column=0, pady=10, sticky=tk.W)
        
        url1_frame = ttk.Frame(help_frame)
        url1_frame.grid(row=3, column=0, pady=5, sticky=tk.W)
        url1 = "https://s[number of universe]-[community letters].ogame.gameforge.com/api/players.xml"
        url1_entry = ttk.Entry(url1_frame, width=50)
        url1_entry.insert(0, url1)
        url1_entry.config(state='readonly')
        url1_entry.grid(row=0, column=0, padx=5)
        ttk.Button(url1_frame, text="Copy players URL", command=lambda: self.copy_to_clipboard(url1)).grid(row=0, column=1)
        
        url2_frame = ttk.Frame(help_frame)
        url2_frame.grid(row=4, column=0, pady=5, sticky=tk.W)
        url2 = "https://s[number of universe]-[community letters].ogame.gameforge.com/api/universe.xml"
        url2_entry = ttk.Entry(url2_frame, width=50)
        url2_entry.insert(0, url2)
        url2_entry.config(state='readonly')
        url2_entry.grid(row=0, column=0, padx=5)
        ttk.Button(url2_frame, text="Copy universe URL", command=lambda: self.copy_to_clipboard(url2)).grid(row=0, column=1)

        url3_frame = ttk.Frame(help_frame)
        url3_frame.grid(row=5, column=0, pady=5, sticky=tk.W)
        url3 = "https://s[number of universe]-[community letters].ogame.gameforge.com/api/highscore.xml?category=1&type=0"
        url3_entry = ttk.Entry(url3_frame, width=50)
        url3_entry.insert(0, url3)
        url3_entry.config(state='readonly')
        url3_entry.grid(row=0, column=0, padx=5)
        ttk.Button(url3_frame, text="Copy highscore URL", command=lambda: self.copy_to_clipboard(url3)).grid(row=0, column=1)

        ttk.Label(help_frame, text="\nHighscore URL types:\n0: Total Score\n1: Economy\n2: Research\n3: Military\n4: Military Lost\n5: Military Built\n6: Military Destroyed\n7: Honor").grid(row=6, column=0, pady=5, sticky=tk.W)
          
        ttk.Label(help_frame, text='In place of "number of universe" paste the server number, you will find it at the beginning\nof the URL when you log into your account. In the place of "community letters" enter\nthe two letters that follow the server number in the URL, e.g. for ORG servers\nit will be "en" and for PL servers "pl".\n\nExample: Czech Zenith will be 178-cz.').grid(row=7, column=0, pady=5, sticky=tk.W)
    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message("URL copied to clipboard")

    def toggle_highscore_fields(self):
        if self.use_highscore.get():
            self.highscore_url_label.grid(row=1, column=0, sticky=tk.W, pady=(10,0))
            self.highscore_url_entry.grid(row=2, column=0, pady=5)
            self.min_score_label.grid(row=3, column=0, sticky=tk.W)
            self.min_score_entry.grid(row=4, column=0, pady=5)
        else:
            self.highscore_url_label.grid_remove()
            self.highscore_url_entry.grid_remove()
            self.min_score_label.grid_remove()
            self.min_score_entry.grid_remove()

    def format_score(self, event):
        current = self.min_score.get().replace(" ", "")
        if current.isdigit():
            formatted = "{:,}".format(int(current)).replace(",", " ")
            self.min_score.set(formatted)
    
    def log_message(self, message: str):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.root.update()

    def download_xml_data(self, url: str) -> str:
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self.log_message(f"Error while downloading data from {url}: {str(e)}")
            return None

    def get_player_scores(self, xml_content: str) -> Dict[str, int]:
        try:
            root = ET.fromstring(xml_content)
            player_scores = {}
            
            for player in root.findall('.//player'):
                player_id = player.get('id', '')
                score = player.get('score', '0')
                if player_id and score:
                    player_scores[player_id] = int(score)
            
            return player_scores
        except ET.ParseError as e:
            self.log_message(f"Error while parsing highscore XML: {str(e)}")
            return {}

    def get_player_data(self, xml_content: str, min_score: int = 0, player_scores: Dict[str, int] = None) -> tuple[Set[str], Dict[str, str]]:
            try:
                root = ET.fromstring(xml_content)
                active_players = set()
                player_names = {}
                
                statuses_to_ignore = {
                    status for status, var in self.status_vars.items() 
                    if var.get()
                }
                
                for player in root.findall('.//player'):
                    player_id = player.get('id', '')
                    player_status = player.get('status', '').split(',')  # Split multiple statuses
                    name = player.get('name', '')
                    
                    # Skip if player has any status we want to ignore
                    if any(status in statuses_to_ignore for status in player_status):
                        continue
                        
                    if player_scores is not None:
                        score = player_scores.get(player_id, 0)
                        if score < min_score:
                            continue
                            
                    if player_id:
                        active_players.add(player_id)
                        if name:
                            player_names[player_id] = name
                
                return active_players, player_names
            except ET.ParseError as e:
                self.log_message(f"Error while parsing XML universe: {str(e)}")
                return set(), {}

    def process_planet_data(self, planets_xml: str, active_players: Set[str], 
                          player_names: Dict[str, str]) -> List[tuple[int, str]]:
        try:
            root = ET.fromstring(planets_xml)
            planet_data = []
            unique_coords = set()
            
            for planet in root.findall('.//planet'):
                player_id = planet.get('player', '')
                coords = planet.get('coords', '')
                
                # Only process planets belonging to non-filtered players
                if player_id and coords and player_id in active_players:
                    if self.coords_only.get():
                        galaxy, system, _ = coords.split(':')
                        short_coords = f"{galaxy}:{system}"
                        
                        if short_coords in unique_coords:
                            continue
                        
                        unique_coords.add(short_coords)
                        sort_value = int(galaxy) * 1000000 + int(system) * 1000
                        planet_data.append((sort_value, short_coords))
                    else:
                        player_name = player_names.get(player_id, player_id)
                        sort_value = self.convert_coords_to_sortable(coords)
                        planet_data.append((sort_value, f"{player_name} ; {coords}"))
            
            return planet_data
        except ET.ParseError as e:
            self.log_message(f"Error while parsing XML universe: {str(e)}")
            return []

    @staticmethod
    def convert_coords_to_sortable(coords: str) -> int:
        galaxy, system, position = map(int, coords.split(':'))
        return galaxy * 1000000 + system * 1000 + position

    def process_data(self):
        self.log_area.delete(1.0, tk.END)
        
        if not self.players_url.get() or not self.planets_url.get():
            messagebox.showerror("Error", "Please provide both URLs")
            return
            
        if self.use_highscore.get():
            if not self.highscore_url.get():
                messagebox.showerror("Error", "Please provide highscore URL")
                return
            try:
                min_score = int(self.min_score.get().replace(" ", ""))
            except ValueError:
                messagebox.showerror("Error", "Invalid minimum score value")
                return
        
        try:
            player_scores = None
            if self.use_highscore.get():
                self.log_message("Downloading highscore data...")
                highscore_xml = self.download_xml_data(self.highscore_url.get())
                if not highscore_xml:
                    return
                player_scores = self.get_player_scores(highscore_xml)
                
            self.log_message("Downloading player data...")
            players_xml = self.download_xml_data(self.players_url.get())
            if not players_xml:
                return
                
            self.log_message("Downloading planetary data...")
            planets_xml = self.download_xml_data(self.planets_url.get())
            if not planets_xml:
                return
            
            self.log_message("Processing of player data...")
            min_score = int(self.min_score.get().replace(" ", "")) if self.use_highscore.get() else 0
            active_players, player_names = self.get_player_data(players_xml, min_score, player_scores)
            
            self.log_message("Planetary data processing...")
            planet_data = self.process_planet_data(planets_xml, active_players, player_names)
            
            self.log_message("Sorting the data...")
            planet_data.sort()
            
            output_filename = self.output_file.get()
            with open(output_filename, 'w', encoding='utf-8') as f:
                for _, line in planet_data:
                    f.write(line + '\n')
            
            self.log_message(f"\nProcessing completed:")
            if not self.coords_only.get():
                self.log_message(f"- Found {len(active_players)} active players")
            self.log_message(f"- Recorded {len(planet_data)} unique rows to {output_filename}")
            
            messagebox.showinfo("Success", "Data processed successfully!")
            
        except Exception as e:
            self.log_message(f"An error occurred: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = XMLFilterApp(root)
    root.mainloop()