from urllib.parse import urlparse

p1 = urlparse("irc://irc.gnome.org/#outreachy")
print("p1:", p1)
p2 = urlparse("irc://irc.gnome.org/outreachy")
print("p2:", p2)
p3 = urlparse("https://webchat.oftc.net/?channels=#channel")
print("p3:", p3)
