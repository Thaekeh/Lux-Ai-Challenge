import math
import random
import sys

from lux import annotate
from lux.constants import Constants
from lux.game import Game
from lux.game_constants import GAME_CONSTANTS
from lux.game_map import RESOURCE_TYPES, Cell

DIRECTIONS = Constants.DIRECTIONS
game_state = None


def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height
    game_map = game_state.map

    resource_tiles: list[Cell] = []
    empty_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
                continue
            if not cell.citytile:
                empty_tiles.append(cell)
                continue

    # we iterate over all our units and do something with them
    for unit in player.units:
        # unit_index = player.units.index(unit.id)
        if unit.is_worker() and unit.can_act():

            lowest_fuel_city = city_with_least_fuel(player)
            closest_dist = math.inf
            closest_resource_tile = None
            if unit_shares_position_with_other_units(player, unit):
                random_direction = get_random_direction()
                destination = unit.pos.translate(
                    random_direction, 1)
                actions.append(
                    unit.move(random_direction))

            if lowest_fuel_city.fuel < 200 and unit.get_cargo_space_left() < 20:
                # if we have resources and a city needs it
                actions.append(annotate.sidetext(
                    'going to city with lowest fuel - Step 1'))
                closest_city_tile = closest_city_tile_of_city(
                    lowest_fuel_city, unit)
                actions.append(annotate.x(closest_city_tile.pos.x,
                                          closest_city_tile.pos.y))
                actions.append(
                    unit.move(unit.pos.direction_to(
                        closest_city_tile.pos))
                )
                actions.append(annotate.x(closest_city_tile.pos.x,
                                          closest_city_tile.pos.y))

            elif unit.get_cargo_space_left() == 0:
                # unit is full so we want to build a city
                actions.append(annotate.sidetext(
                    'going to build a city - Step 2'))
                if unit.can_build(game_map):
                    actions.append(unit.build_city())
                else:
                    destination = closest_empty_tile(empty_tiles, unit)
                    actions.append(
                        unit.move(unit.pos.direction_to(destination.pos)))

            elif unit.get_cargo_space_left() > 0:
                # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                actions.append(annotate.sidetext(
                    'going to harvest resources - Step 3'))
                for resource_tile in resource_tiles:
                    if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal():
                        continue
                    if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium():
                        continue
                    dist = resource_tile.pos.distance_to(unit.pos)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_resource_tile = resource_tile
                if closest_resource_tile is not None:
                    actions.append(annotate.x(closest_resource_tile.pos.x,
                                              closest_resource_tile.pos.y))
                    actions.append(
                        unit.move(unit.pos.direction_to(closest_resource_tile.pos)))

    for k, city in player.cities.items():
        for cityTile in city.citytiles:
            if not cityTile.can_act():
                continue
            if city.fuel > 300 and can_produce_units(player):
                actions.append(cityTile.build_worker())
            else:
                actions.append(cityTile.research())

    return actions


def get_closest_city_tile(player, unit):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile


def get_empty_space_next_to_city_tile(game_state, city_tile):
    city_tile_x = city_tile.pos.x
    city_tile_y = city_tile.pos.y
    best_city_tile = None
    current_player_id = game_state.id
    current_player = game_state.players[current_player_id]
    for x in range(3):
        for y in range(3):
            current_x = city_tile_x - x - 2
            current_y = city_tile_y - y - 2

            cell = game_state.map.get_cell(
                current_x, current_y)
            if cell.pos.x < game_state.map.width - 1 and cell.pos.y < game_state.map.height - 1 and not cell.has_resource() and not cell.citytile:
                if not best_city_tile:
                    best_city_tile = cell
                else:
                    lowest_fuel_city = city_with_least_fuel(current_player)

    return best_city_tile


def city_with_least_fuel(player):
    lowest_fuel_city = None
    for k, city in player.cities.items():
        if not lowest_fuel_city or city.fuel < lowest_fuel_city.fuel:
            lowest_fuel_city = city
    return lowest_fuel_city


def closest_city_tile_of_city(city, unit):
    closest_tile = city.citytiles[0]

    for city_tile in city.citytiles:
        if city_tile.pos.distance_to(unit.pos) < closest_tile.pos.distance_to(unit.pos):
            closest_tile = city_tile
    return closest_tile


def can_produce_units(player):
    city_count = 0
    cities = player.cities.items()
    for k, city in cities:
        for city_tile in city.citytiles:
            city_count += 1
    unit_count = len(player.units)
    return unit_count < city_count


def closest_empty_tile(empty_cells, unit):
    closest_dist = math.inf
    closest_empty_cell = empty_cells[0]

    for cell in empty_cells:
        dist = cell.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_empty_cell = cell
    return closest_empty_cell


def unit_shares_position_with_other_units(player, unit):
    for temp_unit in player.units:
        if temp_unit == unit:
            continue
        if temp_unit.pos == unit.pos:
            return True
    return False


def get_random_direction():
    return random.choice(['s', 'n', 'w', 'e'])
