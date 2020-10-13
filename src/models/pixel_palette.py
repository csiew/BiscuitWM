import re


class PixelPalette(object):
    def __init__(self, colormap):
        self.colormap = colormap
        self.hex_map = {
            "red": "#ff0000",
            "sienna": "#a0522d",
            "tan": "#d2b48c",
            "green": "#00ff00",
            "blue": "#0000ff",
            "white": "#ffffff",
            "gainsboro": "#dcdcdc",
            "lightgray": "#d3d3d3",
            "darkgray": "#a9a9a9",
            "gray": "#808080",
            "dimgray": "#696969",
            "lightslategray": "#778899",
            "slategray": "#708090",
            "darkslategray": "#2F4F4F",
            "black": "#000000"
        }

    def is_color_hex(self, value):
        match = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value)
        if match is True:
            return True
        return False

    def get_named_pixel(self, color_name):
        if color_name in self.hex_map.keys():
            return self.colormap.alloc_named_color(self.hex_map[color_name]).pixel
        else:
            return self.colormap.alloc_named_color(self.hex_map["white"]).pixel

    def get_hex_pixel(self, hex_name):
        try:
            return self.colormap.alloc_named_color(hex_name).pixel
        except:
            return self.colormap.alloc_named_color(self.hex_map["white"]).pixel
