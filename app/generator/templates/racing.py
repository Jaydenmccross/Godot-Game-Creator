"""Racing Game — multi-level top-down racer with obstacles and timer.

Each level is a different track with increasing difficulty:
- Level 1: Wide road, few obstacles, generous timer
- Level 2: Narrower road, more obstacles, tighter timer
- Level 3+: Tight road, dense obstacles, fast scrolling
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class RacingTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_player()
        self._write_obstacle()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    # ── player vehicle (CharacterBody2D) ─────────────────────────────────

    def _write_player(self) -> None:
        primary = self._hex_to_godot_color(self.spec.color_primary)
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — Top-down racing vehicle.

const MAX_SPEED := 500.0
const ACCELERATION := 400.0
const BRAKE_FORCE := 600.0
const FRICTION := 200.0
const STEER_SPEED := 3.5

var speed := 0.0


func _physics_process(delta: float) -> void:
\tvar throttle := Input.get_axis("move_down", "move_up")
\tvar steer := Input.get_axis("move_left", "move_right")

\tif throttle > 0.0:
\t\tspeed = min(speed + ACCELERATION * delta, MAX_SPEED)
\telif throttle < 0.0:
\t\tspeed = max(speed - BRAKE_FORCE * delta, -MAX_SPEED * 0.4)
\telse:
\t\tspeed = move_toward(speed, 0.0, FRICTION * delta)

\tif abs(speed) > 10.0:
\t\trotation += steer * STEER_SPEED * delta * sign(speed)

\tvelocity = Vector2(0, -speed).rotated(rotation)
\tmove_and_slide()

\t_check_off_road()


func _check_off_road() -> void:
\tif position.x < 60 or position.x > 1220 or position.y < -80 or position.y > 800:
\t\tposition.x = clamp(position.x, 80, 1200)
\t\tposition.y = clamp(position.y, 0, 720)
\t\tspeed *= 0.5
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(20, 40)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Body" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-10, 20, -10, -16, -6, -20, 6, -20, 10, -16, 10, 20)
color = Color{primary}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")
''')

    # ── obstacle (StaticBody2D) ──────────────────────────────────────────

    def _write_obstacle(self) -> None:
        secondary = self._hex_to_godot_color(self.spec.color_secondary)
        self._write("scripts/obstacle.gd", '''extends StaticBody2D

var scroll_speed := 200.0


func _process(delta: float) -> void:
\tposition.y += scroll_speed * delta
\tif position.y > 800:
\t\tposition.y = -60
\t\tposition.x = randf_range(80, 1200)
''')
        self._write("scenes/obstacle.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/obstacle.gd" id="1"]

[sub_resource type="RectangleShape2D" id="ocol"]
size = Vector2(40, 40)

[node name="Obstacle" type="StaticBody2D"]
script = ExtResource("1")

[node name="Sprite" type="ColorRect" parent="."]
offset_left = -20.0
offset_top = -20.0
offset_right = 20.0
offset_bottom = 20.0
color = Color{secondary}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ocol")
''')

    # ── level generation ─────────────────────────────────────────────────

    def _write_level(self, level_num: int) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        ground = self._hex_to_godot_color(self.spec.color_ground)
        accent = self._hex_to_godot_color(self.spec.color_accent)

        obstacle_count = 3 + level_num * 2
        scroll_speed = 150 + level_num * 50
        goal_score = 20 + level_num * 15
        road_left = max(150, 250 - level_num * 30)
        road_right = min(1130, 1030 + level_num * 30)
        road_width = road_right - road_left

        obstacles = ""
        for i in range(obstacle_count):
            ox = road_left + 50 + (i * (road_width - 100)) // max(1, obstacle_count - 1)
            oy = -100 - i * 200
            obstacles += f'''
[node name="Obstacle{i+1}" parent="." instance=ExtResource("obstacle")]
position = Vector2({ox}, {oy})
'''

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps=6 format=3]

[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/obstacle.tscn" id="obstacle"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
offset_right = 1280.0
offset_bottom = 720.0
color = Color{bg}

[node name="Road" type="ColorRect" parent="."]
offset_left = {road_left}.0
offset_right = {road_right}.0
offset_bottom = 720.0
color = Color{ground}

[node name="CenterLine" type="ColorRect" parent="."]
offset_left = {(road_left + road_right) // 2 - 4}.0
offset_right = {(road_left + road_right) // 2 + 4}.0
offset_bottom = 720.0
color = Color(1, 1, 1, 0.3)

[node name="Player" parent="." instance=ExtResource("player")]
position = Vector2({(road_left + road_right) // 2}, 550)
{obstacles}
[node name="ScoreTimer" type="Timer" parent="."]
wait_time = 0.5
autostart = true

[node name="LevelGoalTimer" type="Timer" parent="."]
wait_time = {goal_score}
one_shot = true
autostart = true

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')

        self._write("scripts/game_level.gd", f'''extends Node2D

var _road_lines: Array = []
const SCROLL_SPEED: float = {scroll_speed}.0
const OBSTACLE_SPEED: float = {scroll_speed}.0


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
\t$ScoreTimer.timeout.connect(_on_score_tick)
\t$LevelGoalTimer.timeout.connect(_on_level_goal)
\t_create_road_lines()
\t_set_obstacle_speeds()


func _on_score_tick() -> void:
\tGameManager.add_score(1)


func _on_level_goal() -> void:
\tLevelManager.advance_level()


func _process(delta: float) -> void:
\tfor line in _road_lines:
\t\tline.position.y += SCROLL_SPEED * delta
\t\tif line.position.y > 740:
\t\t\tline.position.y -= 800


func _create_road_lines() -> void:
\tvar road := $Road
\tvar road_left := road.offset_left
\tvar road_right := road.offset_right
\tfor i in 10:
\t\tvar dash := ColorRect.new()
\t\tdash.size = Vector2(4, 30)
\t\tdash.color = Color(1, 1, 0.6, 0.4)
\t\tdash.position = Vector2(road_left + 20, i * 80.0)
\t\tadd_child(dash)
\t\t_road_lines.append(dash)
\t\tvar dash2 := ColorRect.new()
\t\tdash2.size = Vector2(4, 30)
\t\tdash2.color = Color(1, 1, 0.6, 0.4)
\t\tdash2.position = Vector2(road_right - 24, i * 80.0)
\t\tadd_child(dash2)
\t\t_road_lines.append(dash2)


func _set_obstacle_speeds() -> void:
\tfor child in get_children():
\t\tif child.has_method("_process") and child.name.begins_with("Obstacle"):
\t\t\tchild.scroll_speed = OBSTACLE_SPEED


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
