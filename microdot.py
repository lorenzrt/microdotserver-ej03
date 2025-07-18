from microdot import Microdot, Response
from machine import Pin, ADC
import time
import uasyncio as asyncio

app = Microdot()
Response.default_content_type = 'application/json'

sensor_temp = ADC(Pin(34))
sensor_temp.atten(ADC.ATTN_11DB)

buzzer = Pin(26, Pin.OUT)

setpoint = 25.0
buzzer_status = False
last_temp = 0.0

def leer_temperatura():
    valor_adc = sensor_temp.read()
    voltaje = valor_adc * (3.3 / 4095)
    temperatura = voltaje * 100
    return round(temperatura, 2)

def controlar_buzzer(temp, ref):
    global buzzer_status
    buzzer_status = temp > ref
    buzzer.value(buzzer_status)

@app.route('/')
def index(req):
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Control de Temperatura</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin: 20px; }
            header, footer { background-color: #333; color: white; padding: 10px; }
            main { margin: 20px auto; max-width: 400px; }
            input[type=range] { width: 100%; }
            label, p { font-size: 1.2em; }
        </style>
    </head>
    <body>
        <header>
            <h1>Panel de control térmico</h1>
        </header>
        <main>
            <label for="setpoint">Setpoint: <span id="setpoint-value">25</span> °C</label><br>
            <input type="range" id="setpoint" min="0" max="30" value="25">
            <p>Temperatura actual: <span id="temp-actual">--</span> °C</p>
            <p>Estado del buzzer: <span id="buzzer-status">--</span></p>
        </main>
        <footer>
            <p>Joaquin Granata 7° 2° Avionica Comisión A - 2025</p>
        </footer>
        <script>
            const setpointSlider = document.getElementById("setpoint");
            const setpointValue = document.getElementById("setpoint-value");
            const tempActual = document.getElementById("temp-actual");
            const buzzerStatus = document.getElementById("buzzer-status");

            setpointSlider.addEventListener("input", () => {
                setpointValue.textContent = setpointSlider.value;
            });

            setpointSlider.addEventListener("change", () => {
                fetch("/setpoint", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ setpoint: parseFloat(setpointSlider.value) })
                });
            });

            async function actualizarDatos() {
                try {
                    const res = await fetch("/estado");
                    const data = await res.json();
                    tempActual.textContent = data.temp;
                    buzzerStatus.textContent = data.buzzer ? "Activo" : "Inactivo";
                } catch (err) {
                    tempActual.textContent = "Error";
                    buzzerStatus.textContent = "Error";
                }
            }

            setInterval(actualizarDatos, 2000);
            actualizarDatos();
        </script>
    </body>
    </html>
    """
    return Response(body=html, content_type='text/html')

@app.route('/setpoint', methods=['POST'])
def actualizar_setpoint(req):
    global setpoint
    setpoint = req.json.get('setpoint', setpoint)
    return {'ok': True, 'nuevo_setpoint': setpoint}

@app.route('/estado')
def estado(req):
    global last_temp
    last_temp = leer_temperatura()
    controlar_buzzer(last_temp, setpoint)
    return {'temp': last_temp, 'buzzer': buzzer_status}

async def loop_sensor():
    while True:
        global last_temp
        last_temp = leer_temperatura()
        controlar_buzzer(last_temp, setpoint)
        await asyncio.sleep(2)

async def main():
    asyncio.create_task(loop_sensor())
    app.run(debug=True)

asyncio.run(main())
