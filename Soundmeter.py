from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import requests
import time
import threading
import numpy as np

class SoundLoggerApp(App):
    def build(self):
        self.is_logging = False
        self.log_file = None
        self.url = None
        self.calibration_factor = -90  # Default calibration factor
        self.sound_levels = []
        self.start_time = None

        layout = GridLayout(cols=2, padding=10)

        self.url_input = TextInput(text='http://192.168.137.53/data', multiline=False)
        layout.add_widget(Label(text='ESP32 URL:'))
        layout.add_widget(self.url_input)

        self.cal_input = TextInput(text=str(self.calibration_factor), multiline=False)
        layout.add_widget(Label(text='Calibration Factor:'))
        layout.add_widget(self.cal_input)

        self.start_btn = Button(text='Start Monitoring', on_press=self.start_monitoring)
        layout.add_widget(self.start_btn)

        self.stop_btn = Button(text='Stop Monitoring', on_press=self.stop_monitoring)
        layout.add_widget(self.stop_btn)

        self.output_label = Label(text='', size_hint_y=None, height=200)
        layout.add_widget(self.output_label)
        layout.add_widget(Label())  # Empty label for grid alignment

        self.save_btn = Button(text='Save Log', on_press=self.save_log)
        layout.add_widget(self.save_btn)

        self.clear_btn = Button(text='Clear Log', on_press=self.clear_log)
        layout.add_widget(self.clear_btn)

        return layout

    def start_monitoring(self, instance):
        self.url = self.url_input.text
        self.calibration_factor = float(self.cal_input.text)
        self.is_logging = True
        self.start_time = time.perf_counter()
        self.sound_levels = []
        self.log_file = open("sound_data_log.txt", "a")
        threading.Thread(target=self.fetch_data).start()

    def stop_monitoring(self, instance):
        self.is_logging = False
        if self.log_file:
            self.log_file.close()

    def save_log(self, instance):
        # Implement save log functionality here
        pass

    def clear_log(self, instance):
        self.output_label.text = ""

    def calculate_spl(self, samples):
        rms_value = np.sqrt(np.mean(np.array(samples) ** 2))
        spl = 20 * np.log10(rms_value / 0.00002) + self.calibration_factor if rms_value > 0 else None
        return spl

    def fetch_data(self):
        while self.is_logging:
            try:
                response = requests.get(self.url)
                if response.status_code == 200:
                    data = response.text
                    sound_samples = [int(x) for x in data.split(',') if x.strip()]
                    spl = self.calculate_spl(sound_samples)
                    if spl is not None:
                        self.sound_levels.append(spl)
                        current_time = time.perf_counter()
                        elapsed_time = current_time - self.start_time
                        leq = 10 * np.log10(np.mean(np.power(10, np.array(self.sound_levels) / 10))) if len(self.sound_levels) > 0 else None

                        display_data = f"Time: {elapsed_time:.2f}s, SPL: {spl:.2f} dB, Real-time LEq: {leq:.2f} dB" if leq is not None else f"Time: {elapsed_time:.2f}s, SPL: {spl:.2f} dB"
                        self.output_label.text += display_data + '\n'
            except requests.exceptions.RequestException:
                pass  # Ignore the error and proceed silently

            time.sleep(1/8)  # Maintain 8 Hz frequency

if __name__ == '__main__':
    SoundLoggerApp().run()
