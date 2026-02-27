"""Racing game template — top-down racer with obstacles and timer."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class RacingTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_player()
        self._write_obstacle()
        self._write_game_scene()

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — Top-down racing vehicle.

const MAX_SPEED := 500.0
const ACCELERATION := 400.0
const BRAKE_FORCE := 600.0
const FRICTION := 200.0
const STEER_SPEED := 3.5

var speed := 0.0
var steer_angle := 0.0

@onready var sprite: Sprite2D = $Sprite2D if has_node("Sprite2D") else null


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

\t_wrap_screen()


func _wrap_screen() -> void:
\tif position.y < -40:
\t\tposition.y = 760
\telif position.y > 760:
\t\tposition.y = -40
\tif position.x < -40:
\t\tposition.x = 1320
\telif position.x > 1320:
\t\tposition.x = -40
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(20, 40)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_primary)}
scale = Vector2(0.3, 0.3)

[node name="Body" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-10, 20, -10, -16, -6, -20, 6, -20, 10, -16, 10, 20)
color = Color{self._hex_to_godot_color(self.spec.color_primary)}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")
''')

    def _write_obstacle(self) -> None:
        self._write("scripts/obstacle.gd", '''extends StaticBody2D

const SCROLL_SPEED := 200.0


func _process(delta: float) -> void:
\tposition.y += SCROLL_SPEED * delta
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
color = Color{self._hex_to_godot_color(self.spec.color_secondary)}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ocol")
''')

    def _write_game_scene(self) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        self._write("scenes/game.tscn", f'''[gd_scene load_steps=5 format=3]

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
offset_left = 200.0
offset_right = 1080.0
offset_bottom = 720.0
color = Color(0.25, 0.25, 0.28, 1)

[node name="CenterLine" type="ColorRect" parent="."]
offset_left = 636.0
offset_right = 644.0
offset_bottom = 720.0
color = Color(1, 1, 1, 0.3)

[node name="Player" parent="." instance=ExtResource("player")]
position = Vector2(640, 550)

[node name="Obstacle1" parent="." instance=ExtResource("obstacle")]
position = Vector2(400, 100)

[node name="Obstacle2" parent="." instance=ExtResource("obstacle")]
position = Vector2(800, -100)

[node name="Obstacle3" parent="." instance=ExtResource("obstacle")]
position = Vector2(550, -300)

[node name="Obstacle4" parent="." instance=ExtResource("obstacle")]
position = Vector2(900, -500)

[node name="ScoreTimer" type="Timer" parent="."]
wait_time = 0.5
autostart = true

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')
        self._write("scripts/game_level.gd", '''extends Node2D

var _road_lines: Array = []


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
\t$ScoreTimer.timeout.connect(_on_score_tick)
\t_create_road_lines()


func _on_score_tick() -> void:
\tGameManager.add_score(1)


func _process(delta: float) -> void:
\tfor line in _road_lines:
\t\tline.position.y += 200.0 * delta
\t\tif line.position.y > 740:
\t\t\tline.position.y -= 800


func _create_road_lines() -> void:
\tfor i in 10:
\t\tvar dash := ColorRect.new()
\t\tdash.size = Vector2(4, 30)
\t\tdash.color = Color(1, 1, 0.6, 0.4)
\t\tdash.position = Vector2(400, i * 80.0)
\t\tadd_child(dash)
\t\t_road_lines.append(dash)
\t\tvar dash2 := ColorRect.new()
\t\tdash2.size = Vector2(4, 30)
\t\tdash2.color = Color(1, 1, 0.6, 0.4)
\t\tdash2.position = Vector2(876, i * 80.0)
\t\tadd_child(dash2)
\t\t_road_lines.append(dash2)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
