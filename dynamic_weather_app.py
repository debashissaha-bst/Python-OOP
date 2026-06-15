import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass


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

    def __str__(self):
        return f"{self.city}, {self.country}"


@dataclass
class CurrentWeather:
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    weather_code: int
    time: str

    @property
    def condition(self):
        return WeatherCode.describe(self.weather_code)


@dataclass
class ForecastDay:
    date: str
    max_temp: float
    min_temp: float
    precipitation: float
    weather_code: int

    @property
    def condition(self):
        return WeatherCode.describe(self.weather_code)


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
            raise WeatherAppError("Request timeout. Try again.")

        except requests.exceptions.HTTPError:
            raise WeatherAppError("Server returned an error.")

        except requests.exceptions.RequestException:
            raise WeatherAppError("API request failed.")

        except ValueError:
            raise WeatherAppError("Invalid JSON response.")


class WeatherService:
    GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, api_client):
        self.api_client = api_client

    def get_location(self, city_name):
        params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json",
        }

        data = self.api_client.get_json(self.GEO_URL, params)

        if "results" not in data or len(data["results"]) == 0:
            raise WeatherAppError("Location not found.")

        result = data["results"][0]

        return Location(
            city=result.get("name", "Unknown"),
            country=result.get("country", "Unknown"),
            latitude=result.get("latitude"),
            longitude=result.get("longitude"),
            timezone=result.get("timezone", "auto"),
        )

    def get_current_weather(self, location):
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": [
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
            ],
            "timezone": "auto",
        }

        data = self.api_client.get_json(self.WEATHER_URL, params)

        if "current" not in data:
            raise WeatherAppError("Current weather data not available.")

        current = data["current"]

        return CurrentWeather(
            temperature=current.get("temperature_2m"),
            feels_like=current.get("apparent_temperature"),
            humidity=current.get("relative_humidity_2m"),
            wind_speed=current.get("wind_speed_10m"),
            weather_code=current.get("weather_code"),
            time=current.get("time"),
        )

    def get_forecast(self, location, days):
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "weather_code",
            ],
            "timezone": "auto",
            "forecast_days": days,
        }

        data = self.api_client.get_json(self.WEATHER_URL, params)

        if "daily" not in data:
            raise WeatherAppError("Forecast data not available.")

        daily = data["daily"]

        forecasts = []

        for i in range(len(daily["time"])):
            forecasts.append(
                ForecastDay(
                    date=daily["time"][i],
                    max_temp=daily["temperature_2m_max"][i],
                    min_temp=daily["temperature_2m_min"][i],
                    precipitation=daily["precipitation_sum"][i],
                    weather_code=daily["weather_code"][i],
                )
            )

        return forecasts


class WeatherReportPrinter:
    @staticmethod
    def show_current(location, weather):
        print("\nCURRENT WEATHER")
        print("-" * 45)
        print("Location       :", location)
        print("Temperature    :", weather.temperature, "°C")
        print("Feels Like     :", weather.feels_like, "°C")
        print("Humidity       :", weather.humidity, "%")
        print("Wind Speed     :", weather.wind_speed, "km/h")
        print("Condition      :", weather.condition)
        print("Time           :", weather.time)

    @staticmethod
    def show_forecast(location, forecasts):
        print("\nWEATHER FORECAST")
        print("-" * 45)
        print("Location:", location)
        print("-" * 45)

        for day in forecasts:
            print("Date          :", day.date)
            print("Max Temp      :", day.max_temp, "°C")
            print("Min Temp      :", day.min_temp, "°C")
            print("Precipitation :", day.precipitation, "mm")
            print("Condition     :", day.condition)
            print("-" * 45)

    @staticmethod
    def compare_weather(location1, weather1, location2, weather2):
        print("\nCITY WEATHER COMPARISON")
        print("-" * 60)
        print(f"{'Metric':<18}{str(location1):<22}{str(location2):<22}")
        print("-" * 60)
        print(f"{'Temperature':<18}{weather1.temperature} °C{'':<14}{weather2.temperature} °C")
        print(f"{'Feels Like':<18}{weather1.feels_like} °C{'':<14}{weather2.feels_like} °C")
        print(f"{'Humidity':<18}{weather1.humidity} %{'':<15}{weather2.humidity} %")
        print(f"{'Wind Speed':<18}{weather1.wind_speed} km/h{'':<11}{weather2.wind_speed} km/h")
        print(f"{'Condition':<18}{weather1.condition:<22}{weather2.condition:<22}")
        print("-" * 60)


class SearchHistory:
    def __init__(self):
        self.history = []

    def add(self, city):
        self.history.append(city)

    def show(self):
        print("\nSEARCH HISTORY")
        print("-" * 30)

        if not self.history:
            print("No search history found.")
            return

        for index, city in enumerate(self.history, start=1):
            print(f"{index}. {city}")

    def clear(self):
        self.history.clear()
        print("Search history cleared.")


class WeatherApp:
    def __init__(self):
        api_client = RequestsAPIClient()
        self.weather_service = WeatherService(api_client)
        self.history = SearchHistory()

    def get_city_input(self):
        city = input("Enter city name: ").strip()

        if not city:
            raise WeatherAppError("City name cannot be empty.")

        self.history.add(city)
        return city

    def current_weather_flow(self):
        city = self.get_city_input()
        location = self.weather_service.get_location(city)
        weather = self.weather_service.get_current_weather(location)
        WeatherReportPrinter.show_current(location, weather)

    def forecast_flow(self):
        city = self.get_city_input()

        try:
            days = int(input("Enter forecast days 1-7: "))
        except ValueError:
            raise WeatherAppError("Forecast days must be a number.")

        if days < 1 or days > 7:
            raise WeatherAppError("Forecast days must be between 1 and 7.")

        location = self.weather_service.get_location(city)
        forecasts = self.weather_service.get_forecast(location, days)
        WeatherReportPrinter.show_forecast(location, forecasts)

    def compare_flow(self):
        print("\nFirst City")
        city1 = self.get_city_input()

        print("\nSecond City")
        city2 = self.get_city_input()

        location1 = self.weather_service.get_location(city1)
        location2 = self.weather_service.get_location(city2)

        weather1 = self.weather_service.get_current_weather(location1)
        weather2 = self.weather_service.get_current_weather(location2)

        WeatherReportPrinter.compare_weather(location1, weather1, location2, weather2)

    def show_menu(self):
        print("\nPYTHON OOP WEATHER APP")
        print("=" * 40)
        print("1. Check Current Weather")
        print("2. View Weather Forecast")
        print("3. Compare Two Cities")
        print("4. View Search History")
        print("5. Clear Search History")
        print("6. Exit")
        print("=" * 40)

    def run(self):
        while True:
            self.show_menu()
            choice = input("Enter your choice: ").strip()

            try:
                if choice == "1":
                    self.current_weather_flow()

                elif choice == "2":
                    self.forecast_flow()

                elif choice == "3":
                    self.compare_flow()

                elif choice == "4":
                    self.history.show()

                elif choice == "5":
                    self.history.clear()

                elif choice == "6":
                    print("Weather app closed successfully.")
                    break

                else:
                    print("Invalid choice. Please try again.")

            except WeatherAppError as error:
                print("\nError:", error)

            except Exception as error:
                print("\nUnexpected error:", error)


if __name__ == "__main__":
    app = WeatherApp()
    app.run()