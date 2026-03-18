[app]
title = JARVIS MARK XXX
package.name = jarvis
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = INTERNET,RECORD_AUDIO
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.api = 31
android.minapi = 21
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
