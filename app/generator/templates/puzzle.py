"""Puzzle game template — grid-based match/swap mechanics."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class PuzzleTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_game_scene()
        self._write_grid_logic()

    def _write_game_scene(self) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        self._write("scenes/game.tscn", f'''[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Game" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color{bg}

[node name="GridContainer" type="GridContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -200.0
offset_top = -200.0
offset_right = 200.0
offset_bottom = 200.0
columns = 6
theme_override_constants/h_separation = 4
theme_override_constants/v_separation = 4

[node name="MovesLabel" type="Label" parent="."]
layout_mode = 1
anchors_preset = 1
anchor_left = 1.0
anchor_right = 1.0
offset_left = -200.0
offset_top = 60.0
offset_right = -20.0
offset_bottom = 90.0
theme_override_font_sizes/font_size = 22
text = "Moves: 0"
horizontal_alignment = 2

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')

    def _write_grid_logic(self) -> None:
        primary = self._hex_to_godot_color(self.spec.color_primary)
        self._write("scripts/game_level.gd", f'''extends Control
## Puzzle grid — click tiles to clear matching groups.

const COLS := 6
const ROWS := 6
const TILE_SIZE := 60
const COLORS: Array[Color] = [
\tColor{primary},
\tColor(0.85, 0.2, 0.3, 1),
\tColor(0.2, 0.8, 0.3, 1),
\tColor(0.95, 0.8, 0.15, 1),
\tColor(0.6, 0.3, 0.8, 1),
]

var grid: Array = []
var moves: int = 0
var _buttons: Array = []


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
\t_build_grid()


func _build_grid() -> void:
\tfor child in $GridContainer.get_children():
\t\tchild.queue_free()
\tgrid.clear()
\t_buttons.clear()
\tfor row in ROWS:
\t\tvar grid_row: Array[int] = []
\t\tvar btn_row: Array = []
\t\tfor col in COLS:
\t\t\tvar color_idx := randi() % COLORS.size()
\t\t\tgrid_row.append(color_idx)
\t\t\tvar btn := Button.new()
\t\t\tbtn.custom_minimum_size = Vector2(TILE_SIZE, TILE_SIZE)
\t\t\tbtn.add_theme_stylebox_override("normal", _make_style(COLORS[color_idx]))
\t\t\tbtn.add_theme_stylebox_override("hover", _make_style(COLORS[color_idx].lightened(0.2)))
\t\t\tbtn.add_theme_stylebox_override("pressed", _make_style(COLORS[color_idx].darkened(0.2)))
\t\t\tbtn.pressed.connect(_on_tile_pressed.bind(row, col))
\t\t\t$GridContainer.add_child(btn)
\t\t\tbtn_row.append(btn)
\t\tgrid.append(grid_row)
\t\t_buttons.append(btn_row)


func _make_style(color: Color) -> StyleBoxFlat:
\tvar sb := StyleBoxFlat.new()
\tsb.bg_color = color
\tsb.corner_radius_top_left = 6
\tsb.corner_radius_top_right = 6
\tsb.corner_radius_bottom_left = 6
\tsb.corner_radius_bottom_right = 6
\treturn sb


func _on_tile_pressed(row: int, col: int) -> void:
\tvar target_color: int = grid[row][col]
\tvar matched: Array = []
\t_flood_fill(row, col, target_color, matched)
\tif matched.size() < 2:
\t\treturn
\tmoves += 1
\t$MovesLabel.text = "Moves: " + str(moves)
\tGameManager.add_score(matched.size() * 5)
\tfor coord in matched:
\t\tgrid[coord.x][coord.y] = -1
\t_collapse_columns()
\t_refill()
\t_refresh_visuals()


func _flood_fill(row: int, col: int, target: int, result: Array) -> void:
\tif row < 0 or row >= ROWS or col < 0 or col >= COLS:
\t\treturn
\tif grid[row][col] != target:
\t\treturn
\tvar coord := Vector2i(row, col)
\tif coord in result:
\t\treturn
\tresult.append(coord)
\t_flood_fill(row - 1, col, target, result)
\t_flood_fill(row + 1, col, target, result)
\t_flood_fill(row, col - 1, target, result)
\t_flood_fill(row, col + 1, target, result)


func _collapse_columns() -> void:
\tfor col in COLS:
\t\tvar write_row := ROWS - 1
\t\tfor row in range(ROWS - 1, -1, -1):
\t\t\tif grid[row][col] != -1:
\t\t\t\tgrid[write_row][col] = grid[row][col]
\t\t\t\tif write_row != row:
\t\t\t\t\tgrid[row][col] = -1
\t\t\t\twrite_row -= 1


func _refill() -> void:
\tfor row in ROWS:
\t\tfor col in COLS:
\t\t\tif grid[row][col] == -1:
\t\t\t\tgrid[row][col] = randi() % COLORS.size()


func _refresh_visuals() -> void:
\tfor row in ROWS:
\t\tfor col in COLS:
\t\t\tvar color_idx: int = grid[row][col]
\t\t\tvar btn: Button = _buttons[row][col]
\t\t\tbtn.add_theme_stylebox_override("normal", _make_style(COLORS[color_idx]))
\t\t\tbtn.add_theme_stylebox_override("hover", _make_style(COLORS[color_idx].lightened(0.2)))


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
