[app]

title = TradeAnalyzer
package.name = tradeanalyzer
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,dat,json

version = 1.0
fullscreen = 0
orientation = portrait

requirements = python3,kivy,pillow

presplash.filename = %(source.dir)s/icon.png
icon.filename = %(source.dir)s/icon.png

android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]

log_level = 2
warn_on_root = 0
