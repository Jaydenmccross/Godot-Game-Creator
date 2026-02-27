"""Puzzle Game — multi-level grid-based click-to-clear matching.

Each level has a different grid configuration with increasing difficulty:
- Level 1: Small grid, few colors, low score target
- Level 2: Medium grid, more colors, higher score target
- Level 3+: Large grid, many colors, demanding score target
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class PuzzleTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_grid_logic()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    # ── grid logic script ────────────────────────────────────────────────

    def _write_grid_logic(self) -> None:
        primary = self._hex_to_godot_color(self.spec.color_primary)
        secondary = self._hex_to_godot_color(self.spec.color_secondary)
        accent = self._hex_to_godot_color(self.spec.color_accent)
        self._write("scripts/puzzle_grid.gd", f'''extends Control
## Puzzle grid — click tiles to clear matching groups. Reach score target to advance.

var grid_cols: int = 6
var grid_rows: int = 6
var color_count: int = 4
var score_target: int = 200

const TILE_SIZE := 60
const BASE_COLORS: Array[Color] = [
\tColor{primary},
\tColor{secondary},
\tColor{accent},
\tColor(0.2, 0.8, 0.3, 1),
\tColor(0.6, 0.3, 0.8, 1),
\tColor(0.95, 0.5, 0.15, 1),
]

var grid: Array = []
var moves: int = 0
var _buttons: Array = []
var _level_score: int = 0


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
\t_build_grid()
\t_update_target_label()


func setup(cols: int, rows: int, colors: int, target: int) -> void:
\tgrid_cols = cols
\tgrid_rows = rows
\tcolor_count = mini(colors, BASE_COLORS.size())
\tscore_target = target


func _build_grid() -> void:
\tfor child in $GridContainer.get_children():
\t\tchild.queue_free()
\tgrid.clear()
\t_buttons.clear()
\t$GridContainer.columns = grid_cols
\tfor row in grid_rows:
\t\tvar grid_row: Array[int] = []
\t\tvar btn_row: Array = []
\t\tfor col in grid_cols:
\t\t\tvar color_idx := randi() % color_count
\t\t\tgrid_row.append(color_idx)
\t\t\tvar btn := Button.new()
\t\t\tbtn.custom_minimum_size = Vector2(TILE_SIZE, TILE_SIZE)
\t\t\tbtn.add_theme_stylebox_override("normal", _make_style(BASE_COLORS[color_idx]))
\t\t\tbtn.add_theme_stylebox_override("hover", _make_style(BASE_COLORS[color_idx].lightened(0.2)))
\t\t\tbtn.add_theme_stylebox_override("pressed", _make_style(BASE_COLORS[color_idx].darkened(0.2)))
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
\tvar pts := matched.size() * 5
\tGameManager.add_score(pts)
\t_level_score += pts
\tfor coord in matched:
\t\tgrid[coord.x][coord.y] = -1
\t_collapse_columns()
\t_refill()
\t_refresh_visuals()
\t_update_target_label()
\tif _level_score >= score_target:
\t\tLevelManager.advance_level()


func _flood_fill(row: int, col: int, target: int, result: Array) -> void:
\tif row < 0 or row >= grid_rows or col < 0 or col >= grid_cols:
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
\tfor col in grid_cols:
\t\tvar write_row := grid_rows - 1
\t\tfor row in range(grid_rows - 1, -1, -1):
\t\t\tif grid[row][col] != -1:
\t\t\t\tgrid[write_row][col] = grid[row][col]
\t\t\t\tif write_row != row:
\t\t\t\t\tgrid[row][col] = -1
\t\t\t\twrite_row -= 1


func _refill() -> void:
\tfor row in grid_rows:
\t\tfor col in grid_cols:
\t\t\tif grid[row][col] == -1:
\t\t\t\tgrid[row][col] = randi() % color_count


func _refresh_visuals() -> void:
\tfor row in grid_rows:
\t\tfor col in grid_cols:
\t\t\tvar color_idx: int = grid[row][col]
\t\t\tvar btn: Button = _buttons[row][col]
\t\t\tbtn.add_theme_stylebox_override("normal", _make_style(BASE_COLORS[color_idx]))
\t\t\tbtn.add_theme_stylebox_override("hover", _make_style(BASE_COLORS[color_idx].lightened(0.2)))


func _update_target_label() -> void:
\tvar remaining := max(0, score_target - _level_score)
\t$TargetLabel.text = "Target: " + str(remaining) + " pts"


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

    # ── level generation ─────────────────────────────────────────────────

    def _write_level(self, level_num: int) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        ground = self._hex_to_godot_color(self.spec.color_ground)

        cols = 5 + level_num
        rows = 5 + level_num
        color_count = min(3 + level_num, 6)
        score_target = 100 + level_num * 100

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/puzzle_grid.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Game" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("1")
grid_cols = {cols}
grid_rows = {rows}
color_count = {color_count}
score_target = {score_target}

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
columns = {cols}
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

[node name="TargetLabel" type="Label" parent="."]
layout_mode = 1
anchors_preset = 1
anchor_left = 1.0
anchor_right = 1.0
offset_left = -200.0
offset_top = 100.0
offset_right = -20.0
offset_bottom = 130.0
theme_override_font_sizes/font_size = 22
text = "Target: {score_target} pts"
horizontal_alignment = 2

[node name="LevelTitle" type="Label" parent="."]
layout_mode = 1
anchors_preset = 5
anchor_left = 0.5
anchor_right = 0.5
offset_left = -100.0
offset_top = 10.0
offset_right = 100.0
offset_bottom = 40.0
theme_override_font_sizes/font_size = 26
text = "Level {level_num}"
horizontal_alignment = 1

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')

        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
