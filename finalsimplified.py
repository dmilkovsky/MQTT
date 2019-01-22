import matplotlib.pyplot as pyplot
import matplotlib.animation as animation
from matplotlib import style
import paho.mqtt.client as mqtt
import time
import datetime
import pyowm
from pyowm import timeutils
import os


os.popen("sudo -S service mosquitto stop", 'w').write("*******")
os.system("mosquitto -v")


def get_rainforecast(date, place):

    owm = pyowm.OWM('98e24ff49ada4e3427680087d268f230')  # You MUST provide a valid API key
    forecast = owm.three_hours_forecast(place)
    tomorrow_forecast = forecast.get_weather_at(date)
    forecast_rain = tomorrow_forecast.get_rain()

    return forecast_rain


def watering_data(soil_moisture, client):

    tomorrow_date = timeutils.tomorrow()
    rain_data = get_rainforecast(tomorrow_date, 'Skopje,MK')
    rain_mm = float(rain_data['3h'])

    if (float(soil_moisture) < 50) and (rain_mm < 5):   # if soil moisture is less than 50%
        client.publish("Water Pump", "ON")     # and rainfall less than 5 litres per square meter
    else:
        client.publish("Water Pump", "OFF")


def plot_temperature(ax_temp, day):
    # Get Temperature from file
    try:
        temperature_data = open('Temperature' + day, 'r').read()
        rows = temperature_data.split('\n')
        xt = []
        yt = []

        for row in rows:
            if len(row) > 1:
                x, y = (row.split(','))
                xt.append(x)
                yt.append(float(y))

        ax_temp.plot(xt, yt)
    except FileNotFoundError:
        time.sleep(60)


def plot_humidity(ax_hum_moist, day):
    # Get Air Humidity from file
    try:
        humidity_data = open('Humidity' + day, 'r').read()
        hrows = humidity_data.split('\n')
        xh = []
        yh = []

        for row in hrows:
            if len(row) > 1:
                p, q = (row.split(','))
                xh.append(p)
                yh.append(float(q))

        ax_hum_moist.plot(xh, yh, label='Air Humidity')
    except FileNotFoundError:
        time.sleep(60)


def plot_moisture(ax_hum_moist, day):
    # Get Soil Moisture from file
    try:
        moisture_data = open('Soil Moisture' + day, 'r').read()
        mrows = moisture_data.split('\n')
        xm = []
        ym = []

        for row in mrows:
            if len(row) > 1:
                r, t = (row.split(','))
                xm.append(r)
                ym.append(float(t))

        ax_hum_moist.plot(xm, ym, label='Soil Moisture')
    except FileNotFoundError:
        time.sleep(60)


style.use('seaborn-darkgrid')
figure = pyplot.figure()


def plot_data(i):
    day = datetime.datetime.now().strftime("_%d-%m-%y")

    # Temperature graph
    ax_temp = figure.add_subplot(2, 1, 1)
    ax_temp.clear()
    pyplot.ylabel('Degrees Celsius')
    pyplot.title('Temperature')
    ax_temp.axes.xaxis.set_ticklabels([])  # No labels
    plot_temperature(ax_temp, day)
    # Humidity and Moisture graph

    ax_hum_moist = figure.add_subplot(2, 1, 2)
    ax_hum_moist.clear()
    pyplot.ylabel('Percents')
    pyplot.title('Soil Moisture & Air Humidity')
    plot_humidity(ax_hum_moist, day)
    plot_moisture(ax_hum_moist, day)
    pyplot.legend()

    # X-axis Labels 45 Degree Rotation
    for label in ax_hum_moist.xaxis.get_ticklabels():
        label.set_rotation(45)


def on_message(client, userdata, message):
    payload = str(message.payload.decode("utf-8")).strip()

    print(message.topic + ": " + payload)

    date_now = datetime.datetime.now().strftime("_%d-%m-%y")
    text_file = open(message.topic + date_now, 'a')
    text_file.write(datetime.datetime.now().strftime("%H:%M,") + payload + "\n")

    if message.topic == "Soil Moisture":
        watering_data(payload, client)


def new_client(client_name, broker_address, topics, callback_func):
    # Create New Client Instance
    print("Creating New Client")
    client = mqtt.Client(client_name)

    # Assign Callback Function
    print("Assigning Callback Function")
    client.on_message = on_message

    # Connect to Broker
    print("Connecting to Broker")
    client.connect(broker_address)

    # Put Client in Infinite Loop
    client.loop_start()

    # Subscribe to Topics
    for t in topics:
        print("Subscribing to Topic", t)
        client.subscribe(t)


def main():

    new_client("OrangePi", "127.0.0.1", ["Temperature", "Humidity", "Soil Moisture"], on_message)
    ani = animation.FuncAnimation(figure, plot_data, interval=500)
    pyplot.show()
    time.sleep(2)


main()
