import threading
import time
import queue
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, ResultReason  # Add these imports
import speech_recognition as sr
import pyttsx3
import webbrowser
import datetime
import platform
import psutil
import requests
from newsapi import NewsApiClient
import smtplib
from email.message import EmailMessage
import pyjokes


# Constants for API keys
INSTAGRAM_API_KEY = "your_instagram_api_key"
NEWS_API_KEY = "your_news_api_key"
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"
OPENWEATHERMAP_API_KEY = "your_openweathermap_api_key"
BING_SPEECH_API_KEY = "YOUR_BING_API_KEY"  # Replace with your Bing Speech API key


# Queue for communication between threads
task_queue = queue.Queue()

def worker_thread():
    while True:
        task = task_queue.get()
        if task is None:
            break  # Exit the thread
        task()

def start_worker_threads(num_threads=4):
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker_thread)
        thread.start()
        threads.append(thread)
    return threads

def stop_worker_threads(threads):
    # Send termination signal to each thread
    for _ in threads:
        task_queue.put(None)
    # Wait for all threads to finish
    for thread in threads:
        thread.join()

def speak(text):
    pyttsx3.speak(text)

def listen(timeout=5):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=timeout)
            print("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            log_interaction(query)
            return query.lower()
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            return ""

def post_to_instagram(update):
    def task():
        api_url = f"https://graph.instagram.com/v12.0/me/media?access_token={INSTAGRAM_API_KEY}"
        response = requests.post(api_url, data={"caption": update})
        handle_instagram_response(response, update)

    task_queue.put(task)

def handle_instagram_response(response, update):
    if response.status_code == 200:
        speak(f"Posted update to Instagram: {update}")
    else:
        speak(f"Failed to post update. Status code: {response.status_code}")

def check_instagram_notifications():
    def task():
        api_url = f"https://graph.instagram.com/v12.0/me/notifications?access_token={INSTAGRAM_API_KEY}"
        response = requests.get(api_url)
        notifications = response.json().get("data", [])
        if notifications:
            speak("You have new Instagram notifications.")
            for notification in notifications:
                speak(notification["title"])
        else:
            speak("No new notifications.")

    task_queue.put(task)

def listen_bing():
    speech_config = SpeechConfig(subscription=BING_SPEECH_API_KEY, region="your_region")
    speech_recognizer = SpeechRecognizer(speech_config=speech_config)

    result = speech_recognizer.recognize_once()
    if result.reason == ResultReason.RecognizedSpeech:
        log_interaction(result.text)
        return result.text.lower()
    else:
        return ""


def log_interaction(command):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("interaction_log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - User said: {command}\n")

def search_google(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")

def open_website(website):
    webbrowser.open(f"https://www.{website}.com")

def play_song(song):
    webbrowser.open(f"https://www.youtube.com/results?search_query={song}")

def get_weather(city):
    def task():
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': OPENWEATHERMAP_API_KEY,
            'units': 'metric'
        }

        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if response.status_code == 200:
                weather_description = data['weather'][0]['description']
                temperature = data['main']['temp']
                humidity = data['main']['humidity']
                wind_speed = data['wind']['speed']

                weather_info = f"Weather in {city}:\n" \
                               f"Description: {weather_description}\n" \
                               f"Temperature: {temperature}°C\n" \
                               f"Humidity: {humidity}%\n" \
                               f"Wind Speed: {wind_speed} m/s"
                speak(weather_info)
            else:
                speak("Unable to fetch weather information. Please try again later.")

        except Exception as e:
            speak(f"An error occurred while fetching weather information: {str(e)}")

    task_queue.put(task)

def get_current_time():
    current_time = datetime.datetime.now().strftime("%H:%M")
    return f"The current time is {current_time}."

def set_reminder(reminder, time_in_seconds):
    def task():
        time.sleep(time_in_seconds)
        speak(f"Reminder: {reminder}")

    task_queue.put(task)

def get_news(topic=""):
    def task():
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)

        try:
            headlines = newsapi.get_top_headlines(q=topic, language='en', country='us')
            if headlines['status'] == 'ok' and headlines['totalResults'] > 0:
                articles = headlines['articles']
                news_info = "Here are the latest news headlines:\n"
                for idx, article in enumerate(articles):
                    news_info += f"{idx + 1}. {article['title']}\n"
                    news_info += f"Source: {article['source']['name']}\n"
                    news_info += f"URL: {article['url']}\n\n"
                speak(news_info)
            else:
                speak("Sorry, I couldn't retrieve any news on that topic.")

        except Exception as e:
            speak(f"An error occurred while fetching news: {str(e)}")

    task_queue.put(task)

def send_email(subject, body, to_email):
    def task():
        try:
            message = EmailMessage()
            message.set_content(body)
            message['Subject'] = subject
            message['From'] = EMAIL_ADDRESS
            message['To'] = to_email

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(message)

            handle_email_response()
        except smtplib.SMTPAuthenticationError:
            speak("Failed to send email. Authentication error. Please check your credentials.")
        except smtplib.SMTPException as e:
            speak(f"Failed to send email. Error: {str(e)}")
        except Exception as e:
            speak(f"An unexpected error occurred while sending email: {str(e)}")

    task_queue.put(task)

def handle_email_response():
    speak("Email sent successfully!")

def tell_joke():
    joke = pyjokes.get_joke()
    speak(joke)

def get_system_information():
    def task():
        system_info = f"System Information:\n" \
                      f"OS: {platform.system()} {platform.release()}\n" \
                      f"Processor: {platform.processor()}\n" \
                      f"Memory (RAM): {psutil.virtual_memory().percent}% used\n" \
                      f"Disk Space: {psutil.disk_usage('/').percent}% used"
        speak(system_info)

    task_queue.put(task)

def perform_math_calculation(expression):
    def task():
        try:
            result = eval(expression)
            speak(f"The result of {expression} is {result}")
        except Exception as e:
            speak(f"Error performing calculation: {str(e)}")

    task_queue.put(task)

def main():
    speak("Hello! I'm your AI assistant. How can I help you today?")

    # Start worker threads
    threads = start_worker_threads()

    while True:
        command = listen()

        if "exit" in command:
            speak("Goodbye!")
            break
        elif "search" in command:
            query = command.replace("search", "")
            speak(f"Searching Google for {query}")
            search_google(query)
        elif "open website" in command:
            speak("Sure, which website would you like me to open?")
            website = listen(timeout=10)
            speak(f"Opening {website}")
            open_website(website)
        elif "play music" in command:
            speak("What song would you like to listen to?")
            song = listen(timeout=10)
            speak(f"Playing {song} on YouTube")
            play_song(song)
        elif "weather" in command:
            speak("Sure, which city's weather would you like to know?")
            city = listen(timeout=10)
            get_weather(city)
        elif "current time" in command:
            current_time_info = get_current_time()
            speak(current_time_info)
        elif "set reminder" in command:
            speak("What would you like to be reminded of?")
            reminder = listen(timeout=10)
            speak("After how many seconds should I remind you?")
            try:
                time_in_seconds = int(listen(timeout=10))
                set_reminder(reminder, time_in_seconds)
                speak("Reminder set successfully.")
            except ValueError:
                speak("Invalid input. Please provide a valid number of seconds.")
        elif "news" in command:
            speak("Sure, what topic would you like to know the news about?")
            topic = listen(timeout=10)
            get_news(topic)
        elif "send email" in command:
            speak("Sure, what is the subject of the email?")
            email_subject = listen(timeout=10)
            speak("What is the body of the email?")
            email_body = listen(timeout=20)
            speak("To whom should I send this email?")
            to_email = listen(timeout=10)
            send_email(email_subject, email_body, to_email)
        elif "tell a joke" in command or "fun fact" in command:
            tell_joke()

        elif "system information" in command:
            get_system_information()

        elif "post to Instagram" in command:
            speak("What update would you like to post?")
            update = listen(timeout=20)
            post_to_instagram(update)
        elif "check Instagram notifications" in command:
            check_instagram_notifications()

        elif "calculate" in command or "math" in command:
            speak("Sure, what mathematical calculation would you like me to perform?")
            math_expression = listen(timeout=20)
            perform_math_calculation(math_expression)

    # Stop worker threads
    stop_worker_threads(threads)

if __name__ == "__main__":
    main()
