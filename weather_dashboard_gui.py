import threading
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional

import requests


class WeatherAppError(Exception):
    pass


class WeatherCode:
    CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain shower",
        81: "Moderate rain shower",
        82: "Heavy rain shower",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Heavy thunderstorm with hail",
    }

    @classmethod
    def describe(cls, code):
        return cls.CODES.get(code, "Unknown condition")


@dataclass
class Location:
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str

    def display_name(self):
        return f"{self.city}, {self.country}"


@dataclass
class CurrentWeather:
    temperature: Optional[float]
    feels_like: Optional[float]
    humidity: Optional[int]
    wind_speed: Optional[float]
    weather_code: Optional[int]
    time: Optional[str]

    @property
    def condition(self):
        return WeatherCode.describe(self.weather_code)


@dataclass
class ForecastDay:
    date: str
    max_temp: Optional[float]
    min_temp: Optional[float]
    precipitation: Optional[float]
    weather_code: Optional[int]

    @property
    def condition(self):
        return WeatherCode.describe(self.weather_code)


@dataclass
class WeatherReport:
    location: Location
    current: CurrentWeather
    forecast: list[ForecastDay]


class APIClient(ABC):
    @abstractmethod
    def get_json(self, url, params):
        pass


class RequestsAPIClient(APIClient):
    def __init__(self, timeout=10):
        self.timeout = timeout

    def get_json(self, url, params):
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            raise WeatherAppError("No internet connection.")

        except requests.exceptions.Timeout:
            raise WeatherAppError("Request timed out. Please try again.")

        except requests.exceptions.HTTPError:
            raise WeatherAppError("Weather server returned an error.")

        except requests.exceptions.RequestException:
            raise WeatherAppError("API request failed.")

        except ValueError:
            raise WeatherAppError("Invalid JSON response received.")


class WeatherService:
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, api_client):
        self.api_client = api_client

    def search_location(self, city_name):
        params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json",
        }

        data = self.api_client.get_json(self.GEO_URL, params)

        if "results" not in data or not data["results"]:
            raise WeatherAppError("Location not found.")

        result = data["results"][0]

        return Location(
            city=result.get("name", "Unknown"),
            country=result.get("country", "Unknown"),
            latitude=result.get("latitude"),
            longitude=result.get("longitude"),
            timezone=result.get("timezone", "auto"),
        )

    def get_weather_report(self, city_name, forecast_days):
        location = self.search_location(city_name)

        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": (
                "temperature_2m,"
                "apparent_temperature,"
                "relative_humidity_2m,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_sum,"
                "weather_code"
            ),
            "timezone": location.timezone or "auto",
            "forecast_days": forecast_days,
        }

        data = self.api_client.get_json(self.WEATHER_URL, params)

        if not data or "daily" not in data or "current" not in data:
            raise WeatherAppError("Weather data is not available.")

        current = self._parse_current(data["current"])
        forecast = self._parse_forecast(data["daily"])

        return WeatherReport(location, current, forecast)

    def _parse_current(self, data):
        if data is None:
            raise WeatherAppError("Current weather data is missing.")

        return CurrentWeather(
            temperature=data.get("temperature_2m", data.get("temperature")),
            feels_like=(
                data.get("apparent_temperature")
                if data.get("apparent_temperature") is not None
                else data.get("temperature_2m", data.get("temperature"))
            ),
            humidity=data.get("relative_humidity_2m"),
            wind_speed=data.get("wind_speed_10m", data.get("windspeed")),
            weather_code=data.get("weather_code", data.get("weathercode")),
            time=data.get("time"),
        )

    def _parse_forecast(self, data):
        forecast_list = []

        dates = data.get("time", [])
        max_temps = data.get("temperature_2m_max", [])
        min_temps = data.get("temperature_2m_min", [])
        precipitation = data.get("precipitation_sum", data.get("precipitation", []))
        weather_codes = data.get("weather_code")
        if weather_codes is None:
            weather_codes = data.get("weathercode", [])

        for index, date in enumerate(dates):
            forecast_list.append(
                ForecastDay(
                    date=date,
                    max_temp=max_temps[index] if index < len(max_temps) else None,
                    min_temp=min_temps[index] if index < len(min_temps) else None,
                    precipitation=precipitation[index] if index < len(precipitation) else None,
                    weather_code=weather_codes[index] if index < len(weather_codes) else None,
                )
            )

        return forecast_list


class WeatherDashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("760x600")
        self.root.resizable(False, False)

        api_client = RequestsAPIClient()
        self.weather_service = WeatherService(api_client)

        self.city_history = []

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="Weather Dashboard",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=15)

        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="City:", font=("Arial", 11)).grid(row=0, column=0, padx=5)

        self.city_entry = tk.Entry(search_frame, width=28, font=("Arial", 11))
        self.city_entry.grid(row=0, column=1, padx=5)
        self.city_entry.insert(0, "Dhaka")

        tk.Label(search_frame, text="Forecast Days:", font=("Arial", 11)).grid(row=0, column=2, padx=5)

        self.days_box = ttk.Combobox(
            search_frame,
            values=["1", "2", "3", "4", "5", "6", "7"],
            width=5,
            state="readonly"
        )
        self.days_box.grid(row=0, column=3, padx=5)
        self.days_box.set("3")

        self.search_button = tk.Button(
            search_frame,
            text="Search Weather",
            width=16,
            command=self.fetch_weather
        )
        self.search_button.grid(row=0, column=4, padx=5)

        self.status_label = tk.Label(
            self.root,
            text="Enter a city name and click Search Weather.",
            font=("Arial", 10),
            fg="blue"
        )
        self.status_label.pack(pady=8)

        current_frame = tk.LabelFrame(
            self.root,
            text="Current Weather",
            font=("Arial", 12, "bold"),
            padx=15,
            pady=10
        )
        current_frame.pack(fill="x", padx=20, pady=10)

        self.location_label = tk.Label(current_frame, text="Location: -", font=("Arial", 12))
        self.location_label.grid(row=0, column=0, sticky="w", pady=3)

        self.temperature_label = tk.Label(current_frame, text="Temperature: -", font=("Arial", 12))
        self.temperature_label.grid(row=1, column=0, sticky="w", pady=3)

        self.feels_like_label = tk.Label(current_frame, text="Feels Like: -", font=("Arial", 12))
        self.feels_like_label.grid(row=2, column=0, sticky="w", pady=3)

        self.humidity_label = tk.Label(current_frame, text="Humidity: -", font=("Arial", 12))
        self.humidity_label.grid(row=0, column=1, sticky="w", padx=60, pady=3)

        self.wind_label = tk.Label(current_frame, text="Wind Speed: -", font=("Arial", 12))
        self.wind_label.grid(row=1, column=1, sticky="w", padx=60, pady=3)

        self.condition_label = tk.Label(current_frame, text="Condition: -", font=("Arial", 12))
        self.condition_label.grid(row=2, column=1, sticky="w", padx=60, pady=3)

        forecast_frame = tk.LabelFrame(
            self.root,
            text="Forecast",
            font=("Arial", 12, "bold"),
            padx=10,
            pady=10
        )
        forecast_frame.pack(fill="both", expand=True, padx=20, pady=10)

        columns = ("date", "max_temp", "min_temp", "precipitation", "condition")

        self.forecast_table = ttk.Treeview(
            forecast_frame,
            columns=columns,
            show="headings",
            height=8
        )

        self.forecast_table.heading("date", text="Date")
        self.forecast_table.heading("max_temp", text="Max Temp")
        self.forecast_table.heading("min_temp", text="Min Temp")
        self.forecast_table.heading("precipitation", text="Rain")
        self.forecast_table.heading("condition", text="Condition")

        self.forecast_table.column("date", width=120)
        self.forecast_table.column("max_temp", width=120)
        self.forecast_table.column("min_temp", width=120)
        self.forecast_table.column("precipitation", width=100)
        self.forecast_table.column("condition", width=220)

        self.forecast_table.pack(fill="both", expand=True)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=8)

        self.history_button = tk.Button(
            bottom_frame,
            text="Show Search History",
            width=18,
            command=self.show_history
        )
        self.history_button.grid(row=0, column=0, padx=5)

        self.clear_button = tk.Button(
            bottom_frame,
            text="Clear",
            width=18,
            command=self.clear_dashboard
        )
        self.clear_button.grid(row=0, column=1, padx=5)

        self.exit_button = tk.Button(
            bottom_frame,
            text="Exit",
            width=18,
            command=self.root.destroy
        )
        self.exit_button.grid(row=0, column=2, padx=5)

    def fetch_weather(self):
        city = self.city_entry.get().strip()

        if not city:
            messagebox.showerror("Input Error", "Please enter a city name.")
            return

        try:
            forecast_days = int(self.days_box.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please select forecast days.")
            return

        self.search_button.config(state="disabled")
        self.status_label.config(text="Fetching weather data...", fg="orange")

        thread = threading.Thread(
            target=self._fetch_weather_thread,
            args=(city, forecast_days),
            daemon=True
        )
        thread.start()

    def _fetch_weather_thread(self, city, forecast_days):
        try:
            report = self.weather_service.get_weather_report(city, forecast_days)
            self.root.after(0, lambda: self.render_report(report))

        except WeatherAppError as error:
            self.root.after(0, lambda: self.show_error(str(error)))

        except Exception as error:
            self.root.after(0, lambda: self.show_error(f"Unexpected error: {error}"))

    def render_report(self, report):
        self.city_history.append(report.location.display_name())

        self.location_label.config(text=f"Location: {report.location.display_name()}")
        self.temperature_label.config(text=f"Temperature: {report.current.temperature} °C")
        self.feels_like_label.config(text=f"Feels Like: {report.current.feels_like} °C")
        self.humidity_label.config(text=f"Humidity: {report.current.humidity}%")
        self.wind_label.config(text=f"Wind Speed: {report.current.wind_speed} km/h")
        self.condition_label.config(text=f"Condition: {report.current.condition}")

        self.forecast_table.delete(*self.forecast_table.get_children())

        for day in report.forecast:
            self.forecast_table.insert(
                "",
                "end",
                values=(
                    day.date,
                    f"{day.max_temp} °C",
                    f"{day.min_temp} °C",
                    f"{day.precipitation} mm",
                    day.condition,
                )
            )

        self.status_label.config(text="Weather data loaded successfully.", fg="green")
        self.search_button.config(state="normal")

    def show_error(self, message):
        self.status_label.config(text="Failed to load weather data.", fg="red")
        self.search_button.config(state="normal")
        messagebox.showerror("Weather Error", message)

    def show_history(self):
        if not self.city_history:
            messagebox.showinfo("Search History", "No search history found.")
            return

        history_text = "\n".join(
            f"{index}. {city}"
            for index, city in enumerate(self.city_history, start=1)
        )

        messagebox.showinfo("Search History", history_text)

    def clear_dashboard(self):
        self.city_entry.delete(0, tk.END)

        self.location_label.config(text="Location: -")
        self.temperature_label.config(text="Temperature: -")
        self.feels_like_label.config(text="Feels Like: -")
        self.humidity_label.config(text="Humidity: -")
        self.wind_label.config(text="Wind Speed: -")
        self.condition_label.config(text="Condition: -")

        self.forecast_table.delete(*self.forecast_table.get_children())
        self.status_label.config(text="Dashboard cleared.", fg="blue")


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDashboardApp(root)
    root.mainloop()