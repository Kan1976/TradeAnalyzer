from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import json, os
from datetime import datetime, timedelta

class TradeAnalyzerApp(App):
    LICENSE_FILE = "license.dat"
    SECRET_KEY = 948273

    def build(self):
        if not self.check_license():
            return Label(text="Лицензия не активирована", font_size=22)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        label = Label(text="Анализатор графика\nВерсия 1.0", font_size=32)
        layout.add_widget(label)
        return layout

    def check_license(self):
        if not os.path.exists(self.LICENSE_FILE):
            with open(self.LICENSE_FILE, "w") as f:
                json.dump({"start": datetime.now().strftime("%Y-%m-%d")}, f)
            return True

        with open(self.LICENSE_FILE, "r") as f:
            data = json.load(f)

        start = datetime.strptime(data["start"], "%Y-%m-%d")
        if (datetime.now() - start).days <= 30:
            return True

        self.show_license_popup()
        return False

    def show_license_popup(self):
        box = BoxLayout(orientation='vertical', spacing=10, padding=10)
        info = Label(text="Срок лицензии истёк!\nВведите код продления", font_size=20)
        code_input = TextInput(hint_text="Введите код", multiline=False, font_size=24, input_filter="int")
        btn = Button(text="Активировать", size_hint=(1, 0.3))

        def activate(instance):
            if self.check_code(code_input.text):
                with open(self.LICENSE_FILE, "w") as f:
                    json.dump({"start": datetime.now().strftime("%Y-%m-%d")}, f)
                popup.dismiss()
            else:
                code_input.text = ""
                code_input.hint_text = "Неверный код!"

        btn.bind(on_press=activate)
        box.add_widget(info)
        box.add_widget(code_input)
        box.add_widget(btn)

        popup = Popup(title="Лицензия", content=box, size_hint=(0.8, 0.6), auto_dismiss=False)
        popup.open()

    def check_code(self, code):
        today = datetime.now()
        correct = (self.SECRET_KEY * today.month * today.day) % 999999
        return str(correct) == str(code)

if __name__ == "__main__":
    TradeAnalyzerApp().run()
