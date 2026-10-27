

import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
REFRESH_MS = 60_000

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm",
}


def get_coordinates(city):

    r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=10)
    r.raise_for_status()
    results = r.json().get("results")
    if not results:
        raise ValueError(f"City '{city}' not found")
    p = results[0]
    return p["name"], p.get("country", ""), p["latitude"], p["longitude"]


def get_weather(lat, lon):

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "auto",
        "forecast_days": 5,
    }
    r = requests.get(WEATHER_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Live Weather Dashboard")
        self.root.geometry("420x520")
        self.root.configure(bg="#1e293b")
        self.coords = None
        self.refresh_job = None
        self.build_ui()

    def build_ui(self):
        bg, fg = "#1e293b", "#f1f5f9"

        top = tk.Frame(self.root, bg=bg)
        top.pack(pady=15)
        self.city_entry = tk.Entry(top, font=("Arial", 14), width=20)
        self.city_entry.pack(side="left", padx=5)
        self.city_entry.bind("<Return>", lambda e: self.search())
        tk.Button(top, text="Search", command=self.search).pack(side="left")

        self.city_label = tk.Label(self.root, text="Enter a city", font=("Arial", 20, "bold"), bg=bg, fg=fg)
        self.city_label.pack(pady=(10, 0))

        self.temp_label = tk.Label(self.root, text="--°C", font=("Arial", 48, "bold"), bg=bg, fg="#38bdf8")
        self.temp_label.pack()

        self.cond_label = tk.Label(self.root, text="", font=("Arial", 14), bg=bg, fg=fg)
        self.cond_label.pack()

        self.details_label = tk.Label(self.root, text="", font=("Arial", 11), bg=bg, fg="#94a3b8", justify="center")
        self.details_label.pack(pady=10)

        tk.Label(self.root, text="5-Day Forecast", font=("Arial", 13, "bold"), bg=bg, fg=fg).pack(pady=(10, 5))
        self.forecast_frame = tk.Frame(self.root, bg=bg)
        self.forecast_frame.pack()

        self.updated_label = tk.Label(self.root, text="", font=("Arial", 9), bg=bg, fg="#64748b")
        self.updated_label.pack(side="bottom", pady=10)

    def search(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("Input needed", "Please type a city name.")
            return
        try:
            name, country, lat, lon = get_coordinates(city)
        except ValueError as e:
            messagebox.showerror("Not found", str(e))
            return
        except requests.RequestException:
            messagebox.showerror("Network error", "Could not reach the server. Check your internet.")
            return
        self.coords = (name, country, lat, lon)
        self.update_weather()

    def update_weather(self):
        if not self.coords:
            return
        name, country, lat, lon = self.coords
        try:
            data = get_weather(lat, lon)
        except requests.RequestException:
            self.updated_label.config(text="Update failed. Will retry.")
        else:
            self.show(name, country, data)


        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
        self.refresh_job = self.root.after(REFRESH_MS, self.update_weather)

    def show(self, name, country, data):
        cur = data["current"]
        self.city_label.config(text=f"{name}, {country}")
        self.temp_label.config(text=f"{cur['temperature_2m']:.0f}°C")
        self.cond_label.config(text=WEATHER_CODES.get(cur["weather_code"], "Unknown"))
        self.details_label.config(
            text=f"Feels like {cur['apparent_temperature']:.0f}°C   |   "
                 f"Humidity {cur['relative_humidity_2m']}%   |   "
                 f"Wind {cur['wind_speed_10m']} km/h"
        )

        for w in self.forecast_frame.winfo_children():
            w.destroy()
        daily = data["daily"]
        for i, date in enumerate(daily["time"]):
            day = datetime.strptime(date, "%Y-%m-%d").strftime("%a %d %b")
            desc = WEATHER_CODES.get(daily["weather_code"][i], "")
            hi, lo = daily["temperature_2m_max"][i], daily["temperature_2m_min"][i]
            tk.Label(
                self.forecast_frame,
                text=f"{day:<10} {lo:.0f}° / {hi:.0f}°   {desc}",
                font=("Courier", 11), bg="#1e293b", fg="#f1f5f9", anchor="w",
            ).pack(anchor="w", pady=2)

        self.updated_label.config(text=f"Last updated: {datetime.now():%H:%M:%S}")


if __name__ == "__main__":
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()