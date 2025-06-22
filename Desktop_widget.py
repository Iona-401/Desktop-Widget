import tkinter as tk
from tkinter import ttk, filedialog, Listbox, END
import time
import requests
import pygame
import vlc
import os
import json
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz
from mutagen import File as MutagenFile
import random

# Globals
API_KEY = "eecd724cd8269f42fa6a198e17045085"
current_timezone = None
cities = ["London", "New York", "Tokyo", "Dubai", "Kolkata"]

song = []
display_names = []

def update_time():
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    time_label.config(text = f"{time_str}")
    root.after(1000, update_time)

# Weather funcs
def save_cities():
    with open("cities.json", "w") as f:
        json.dump(cities, f)

def add_city():
    new_city = city_entry.get().strip()
    if new_city and new_city not in cities:
        cities.append(new_city)
        menu = city_dropdown["menu"]
        menu.delete(0, "end")
        for city in cities:
            menu.add_command(label = city, command = tk._setit(selected_city, city))
        selected_city.set(new_city)
        city_entry.delete(0, tk.END)
        save_cities()
        update_weather()
        
def update_clock():
    if current_timezone:
        now = datetime.now(current_timezone)
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        clock_label.config(text = f"Local Time: {time_str}")
    else:
        clock_label.config(text = "Local Time: --")
    
    root.after(1000, update_clock)

def update_weather(*args):
    global current_timezone
    city = selected_city.get()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()

        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]

        lattitude = data["coord"]["lat"]
        longitude = data["coord"]["lon"]
        
        #Timezone From Lat/Lon
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat = lattitude, lng = longitude)
        
        if timezone_str:
            current_timezone = pytz.timezone(timezone_str)  # convert string to pytz timezone
        else:
            current_timezone = None

        #Air Quality
        aq_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lattitude}&lon={longitude}&appid={API_KEY}"
        aq_response = requests.get(aq_url).json()
        aqi = aq_response["list"][0]["main"]["aqi"]  # 1 = good, 5 = very poor

        aqi_desc = ["", "Good", "Fair", "Moderate", "Poor", "Very Poor"]
        aqi_label = aqi_desc[aqi] if 0 < aqi < len(aqi_desc) else "Unknown"

        #Update Weather Label
        weather_text = (
            f"{city}\n"
            f"{temp}°C, {condition.capitalize()}\n"
            f"Humidity: {humidity}%\n"
            f"Air Quality: {aqi_label}"
        )
        weather_label.config(text=weather_text)
        
        #Update Clock
        update_clock()
    
    except Exception as e:
        weather_label.config(text = f"Weather error: {e}")

try:
    with open("cities.json", "r") as f:
        cities = json.load(f)
except FileNotFoundError:
    cities = ["London", "New York", "Tokyo"] 


#Music Player
pygame.mixer.init()

style = ttk.Style()
style.theme_use("clam")

vlc_instance = vlc.Instance()
player = vlc_instance.media_player_new()

music_folder = os.path.join(os.path.expanduser("~"), "Music")
valid_formats = (".mp3", ".m4a", ".wav", ".flac")
songs = [f for f in os.listdir(music_folder) if f.endswith(valid_formats)]

song_index = 0
shuffle_mode = tk.BooleanVar(value = False)
repeat_mode = tk.BooleanVar(value = False)

def play_song_by_index(index):
    global song_index
    song_index = index
    song = songs[song_index]
    song_path = os.path.join(music_folder, song)
    media = vlc_instance.media_new(song_path)
    player.set_media(media)
    player.play()

    song_listbox.select_clear(0, tk.END)
    song_listbox.select_set(song_index)
    song_listbox.activate(song_index)

def play_next_song():
    if not songs:
        return

    if shuffle_mode.get():
        song_index = random.randint(0, len(songs) - 1)
    elif repeat_mode.get():
        pass  # do not change index
    else:
        song_index = (song_index + 1) % len(songs)

    play_song_by_index(song_index)
    
def play_previous_song():
    global song_index
    if songs: 
        song_index = (song_index - 1) % len(songs)
        song_listbox.selection_clear(0, tk.END)
        song_listbox.selection_set(song_index)
        song_listbox.activate(song_index)
        play_selected_song()

def play_selected_song():    
    selected_index = song_listbox.curselection()
    if selected_index:
        song_index = selected_index[0]
        song = songs[song_index]
        song_path = os.path.join(music_folder, song)
        media = vlc_instance.media_new(song_path)
        player.set_media(media)
        player.play()

def check_music_end():
    if player.get_state() == vlc.State.Ended:
        play_next_song()
    root.after(1000, check_music_end)

def pause_music():
    player.pause()

for filename in songs:
        try:
            filepath = os.path.join(music_folder, filename)
            audio = MutagenFile(filepath, easy = True)
            title = audio.get("title", [None])[0]
            artist = audio.get("artist", [None])[0]
            album =  audio.get("album", [None])[0]
            
            if title or artist:
                display = f"{title or filename} - {artist or 'Unknown Artist'}"
                if album:
                    display += f" ({album})"
        
            else:
                display = filename
        except Exception as e:
            display = filename
        
        display_names.append(display)

#GUI
root = tk.Tk()
root.title("Desktop Widget")
root.geometry("500x500")
root.configure(bg = "#f0f0f0")

time_label = tk.Label(root, text = "", font=("Segoe UI", 9), bg = "#f0f0f0", anchor = "e")
time_label.place(relx = 1.0, y = 2, anchor = "ne")

#Weather Frame
weather_frame = tk.Frame(root, bg = "white", bd = 2, relief = "groove", padx = 10, pady = 10)
weather_frame.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = "ew")

selected_city = tk.StringVar(value = cities[0])
selected_city.trace_add("write", update_weather)

city_dropdown = tk.OptionMenu(weather_frame, selected_city, *cities)
city_dropdown.grid(row = 0, column = 0, sticky = "w")

refresh_button = tk.Button(weather_frame, text="Refresh", command=update_weather)
refresh_button.grid(row = 0, column = 1, sticky = "e")

weather_label = tk.Label(weather_frame, text = "", font = ("Helvetica", 12), bg = "white")
weather_label.grid(row = 1, column = 0, columnspan = 2, pady = 5)

clock_label = tk.Label(weather_frame, text = "", font = ("Helvatica", 12))
clock_label.grid(row = 2, column = 0, pady = 10)

city_entry = tk.Entry(weather_frame)
city_entry.grid(row = 3, column = 0)

add_city_btn = tk.Button(weather_frame, text = "Add City", command = add_city)
add_city_btn.grid(row = 3, column = 1, pady = 5)

#Music Frame
music_frame = tk.Frame(root, bg = "white", bd = 2, relief = "groove", padx = 10, pady = 10)
music_frame.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = "ew")
music_frame.grid_rowconfigure(0, weight = 1)
music_frame.grid_columnconfigure(0, weight = 1)

song_listbox = tk.Listbox(music_frame, font = ("Segoe UI", 10), height = 10, bg = "#fafafa", yscrollcommand = lambda f, l: scrollbar.set(f, l))
song_listbox.grid(row = 0, column =  0, columnspan = 3, sticky = "nsew", pady = 5)

scrollbar = tk.Scrollbar(music_frame, orient = "vertical", command = song_listbox.yview)
scrollbar.grid(row = 0,  column = 3,  sticky = "ns", pady = 5)

for name in display_names:
    song_listbox.insert(tk.END, name)

prev_button = tk.Button(music_frame, text = "⏮ Prev", command = play_previous_song)
play_button = tk.Button(music_frame, text = "▶ Play", command = play_selected_song)
next_button = tk.Button(music_frame, text = "⏭ Next", command = play_next_song)

prev_button.grid(row = 1, column = 0, padx = 5, pady = 5)
play_button.grid(row = 1, column = 1, padx = 5, pady = 5)
next_button.grid(row = 1, column = 2, padx = 5, pady = 5)

shuffle_check = tk.Checkbutton(music_frame, text = "Shuffle", variable = shuffle_mode)
pause_button = tk.Button(music_frame, text = "⏸ Pause", command = pause_music)
repeat_check = tk.Checkbutton(music_frame, text = "Repeat", variable = repeat_mode)

shuffle_check.grid(row = 2, column = 0, padx = 5, pady = 5)
pause_button.grid(row = 2, column = 1, padx = 5, pady = 5)
repeat_check.grid(row = 2, column = 2, padx = 5, pady = 5)


update_time()
update_weather()
update_clock()
check_music_end()

root.mainloop()