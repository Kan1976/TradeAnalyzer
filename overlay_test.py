# overlay_test.py
# Тестовый плавающий виджет (Kivy) — показывает сигнал, уверенность и экспирацию.
# Обновляется 1 раз в секунду.
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.behaviors import DragBehavior
import os, glob, json

# Подключаем твой анализатор: используем функцию predict_from_image
# (если файл candle_analyzer.py есть — будет использоваться)
try:
    from candle_analyzer import predict_from_image
except Exception as e:
    predict_from_image = None

class DraggableBox(DragBehavior, BoxLayout):
    pass

class Overlay(BoxLayout):
    signal = StringProperty("NEUTRAL")
    confidence = NumericProperty(50.0)
    expiry = NumericProperty(1)

    def update_from_latest(self, *args):
        # Берём последний скрин из screenshots/
        try:
            files = sorted(glob.glob("screenshots/*.png"))
            if not files:
                self.signal = "NO SHOTS"
                self.confidence = 0.0
                self.expiry = 1
                return
            last = files[-1]
            if predict_from_image:
                try:
                    res = predict_from_image(last)
                    self.signal = res.get("signal", "NEUTRAL")
                    self.confidence = res.get("confidence", 50.0)
                    self.expiry = res.get("expiry_min", 1)
                except Exception as e:
                    self.signal = "ERR"
                    self.confidence = 0.0
                    self.expiry = 1
            else:
                # Заглушка — если нет модуля анализа
                self.signal = "NEUTRAL"
                self.confidence = 50.0
                self.expiry = 1
        except Exception as e:
            self.signal = "ERR"
            self.confidence = 0.0
            self.expiry = 1

class OverlayApp(App):
    def build(self):
        # корень – прозрачный, создаём плавающий виджет справа по центру
        root = FloatLayout()
        # положение справа по центру:
        width = 200
        height = 110

        # Draggable box
        box = DraggableBox(size_hint=(None, None),
                           size=(width, height),
                           pos=(Window.width - width - 10, (Window.height - height) / 2))
        box.orientation = "vertical"
        box.padding = 6
        box.spacing = 4
        box.canvas.before.clear()

        overlay = Overlay()
        # визуальные элементы
        lbl_sig = Label(text="[b]Сигнал:[/b] " + overlay.signal, markup=True, halign="left", size_hint=(1, None), height=30)
        lbl_exp = Label(text="[b]Экспирация:[/b] " + str(overlay.expiry) + " мин", markup=True, halign="left", size_hint=(1, None), height=30)
        lbl_conf = Label(text="[b]Уверенность:[/b] " + str(overlay.confidence) + "%", markup=True, halign="left", size_hint=(1, None), height=30)

        # bind
        overlay.bind(signal=lambda i, v: setattr(lbl_sig, "text", "[b]Сигнал:[/b] " + str(v)))
        overlay.bind(expiry=lambda i, v: setattr(lbl_exp, "text", "[b]Экспирация:[/b] " + str(int(v)) + " мин"))
        overlay.bind(confidence=lambda i, v: setattr(lbl_conf, "text", "[b]Уверенность:[/b] " + str(round(float(v),2)) + "%"))

        # цвет фона через canvas
        from kivy.graphics import Color, RoundedRectangle
        with box.canvas.before:
            Color(0.06, 0.06, 0.06, 0.8)
            rr = RoundedRectangle(size=box.size, pos=box.pos, radius=[10])
        # обновлять геометрию прямоугольника при перетаскивании
        def upd_rect(*a):
            rr.pos = box.pos
            rr.size = box.size
        box.bind(pos=upd_rect, size=upd_rect)

        box.add_widget(lbl_sig)
        box.add_widget(lbl_exp)
        box.add_widget(lbl_conf)

        root.add_widget(box)

        # обновление каждую 1 секунду
        Clock.schedule_interval(overlay.update_from_latest, 1.0)
        # привязать overlay к box для отображения
        # (обновлять локальные лейблы через бинды)
        # сразу сделать первую итерацию
        overlay.update_from_latest()

        # также показываем стрелку/цвет по сигналу - менять цвет фона при обновлении
        def color_update(dt):
            s = overlay.signal.upper()
            if s == "UP":
                rr.rgba = (0.0, 0.6, 0.0, 0.9)
            elif s == "DOWN":
                rr.rgba = (0.6, 0.0, 0.0, 0.9)
            elif s == "NO SHOTS":
                rr.rgba = (0.2, 0.2, 0.2, 0.8)
            else:
                rr.rgba = (0.06, 0.06, 0.06, 0.8)
        Clock.schedule_interval(color_update, 1.0)

        return root

if __name__ == "__main__":
    OverlayApp().run()