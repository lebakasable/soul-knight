import json
import math

def tuple_to_str(tp):
    return ';'.join([str(v) for v in tp])

def str_to_tuple(s):
    return tuple([int(v) for v in s.split(';')])

class TileMap:
    def __init__(self, tile_size, view_size):
        self.tile_size = tuple(tile_size)
        self.view_size = tuple(view_size)
        self.tile_map = {}
        self.all_layers = []

    # used after converting from json
    def tuplify(self):
        new_tile_map = {}
        for pos in self.tile_map:
            new_tile_data = {}
            for layer in self.tile_map[pos]:
                new_tile_data[int(layer)] = self.tile_map[pos][layer]
            new_tile_map[str_to_tuple(pos)] = new_tile_data
        self.tile_map = new_tile_map

    # used when converting to json
    def stringify(self):
        new_tile_map = {}
        for pos in self.tile_map:
            new_tile_map[tuple_to_str(pos)] = self.tile_map[pos]
        self.tile_map = new_tile_map

    def load_map(self, path):
        if path[0] != 'C':
            f = open('data/maps/' + path, 'r')
        else:
            f = open(path, 'r')
        dat = f.read()
        f.close()
        json_dat = json.loads(dat)
        self.tile_map = json_dat['map']
        self.all_layers = json_dat['all_layers']
        self.tuplify()

        tile_x_list = [tile[0] for tile in self.tile_map]
        tile_y_list = [tile[1] for tile in self.tile_map]
        self.left = min(tile_x_list)
        self.right = max(tile_x_list)
        self.top = min(tile_y_list)
        self.bottom = max(tile_y_list)

    def write_map(self, path):
        self.stringify()
        json_dat = {
            'map': self.tile_map,
            'all_layers': self.all_layers,
        }
        self.tuplify()
        f = open(path, 'w')
        f.write(json.dumps(json_dat))
        f.close()

    def tile_collide(self, pos):
        tile_pos = (int(pos[0] // self.tile_size[0]), int(pos[1] // self.tile_size[1]))
        if tile_pos in self.tile_map:
            return self.tile_map[tile_pos]
        else:
            return False

    def get_tile(self, pos, target_layer=None):
        pos = tuple(pos)
        if pos in self.tile_map:
            if target_layer:
                if target_layer in self.tile_map[pos]:
                    return self.tile_map[pos][target_layer]
                else:
                    return None
            else:
                return self.tile_map[pos]
        else:
            return None

    def add_tile(self, tile_type, pos, layer):
        pos = tuple(pos)
        if pos in self.tile_map:
            self.tile_map[pos][layer] = tile_type
        else:
            self.tile_map[pos] = {layer: tile_type}
        if layer not in self.all_layers:
            self.all_layers.append(layer)
            self.all_layers.sort()

    def remove_tile(self, pos, layer=None):
        pos = tuple(pos)
        if pos in self.tile_map:
            if layer:
                if layer in self.tile_map[pos]:
                    del self.tile_map[pos][layer]
            else:
                del self.tile_map[pos]

    def get_visible(self, pos):
        layers = {l : [] for l in self.all_layers}
        for y in range(math.ceil(self.view_size[1] / self.tile_size[1]) + 3):
            for x in range(math.ceil(self.view_size[0] / self.tile_size[0]) + 4):
                tile_pos = (x - 1 + int(round(pos[0] / self.tile_size[0] - 0.5, 0)), y - 2 + int(round(pos[1] / self.tile_size[1] - 0.5, 0)))
                if tile_pos in self.tile_map:
                    for tile in self.tile_map[tile_pos]:
                        layers[tile].append([(tile_pos[0] * self.tile_size[0], tile_pos[1] * self.tile_size[1]), self.tile_map[tile_pos][tile]])
        output = [layers[l] for l in self.all_layers]
        return output
