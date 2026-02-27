"""Top-Down Adventure / RPG template — 8-directional movement, enemies, NPCs."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class TopdownTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_player()
        self._write_game_scene()
        if self.spec.has_enemies:
            self._write_enemy()
        if self.spec.has_collectibles:
            self._write_collectible()

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — Top-down 8-directional player controller.

enum State {{ IDLE, MOVE }}

const SPEED := 220.0

var state: State = State.IDLE
var facing := Vector2.DOWN

@onready var sprite: Sprite2D = $Sprite2D


func _physics_process(_delta: float) -> void:
\tvar input_dir := Vector2(
\t\tInput.get_axis("move_left", "move_right"),
\t\tInput.get_axis("move_up", "move_down"),
\t).normalized()

\tvelocity = input_dir * SPEED

\tif input_dir != Vector2.ZERO:
\t\tfacing = input_dir
\t\t_set_state(State.MOVE)
\telse:
\t\t_set_state(State.IDLE)

\tif sprite and input_dir.x != 0.0:
\t\tsprite.flip_h = input_dir.x < 0.0

\tmove_and_slide()


func _set_state(new_state: State) -> void:
\tif state == new_state:
\t\treturn
\tstate = new_state
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="CircleShape2D" id="player_col"]
radius = 14.0

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_primary)}
scale = Vector2(0.45, 0.45)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("player_col")

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(2.0, 2.0)
position_smoothing_enabled = true
''')

    def _write_game_scene(self) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        enemy_inst = ""
        coin_inst = ""
        ext_extra = ""
        loads = 5
        if self.spec.has_enemies:
            loads += 1
            ext_extra += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
            enemy_inst = """
[node name="Enemy1" parent="World" instance=ExtResource("enemy")]
position = Vector2(300, 200)

[node name="Enemy2" parent="World" instance=ExtResource("enemy")]
position = Vector2(-200, -180)
"""
        if self.spec.has_collectibles:
            loads += 1
            ext_extra += '\n[ext_resource type="PackedScene" path="res://scenes/collectible.tscn" id="coin"]'
            coin_inst = """
[node name="Coin1" parent="World" instance=ExtResource("coin")]
position = Vector2(120, -80)

[node name="Coin2" parent="World" instance=ExtResource("coin")]
position = Vector2(-150, 120)

[node name="Coin3" parent="World" instance=ExtResource("coin")]
position = Vector2(280, 80)
"""
        self._write("scenes/game.tscn", f'''[gd_scene load_steps={loads} format=3]

[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]{ext_extra}

[sub_resource type="RectangleShape2D" id="wall_h"]
size = Vector2(600, 16)

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
offset_left = -640.0
offset_top = -360.0
offset_right = 640.0
offset_bottom = 360.0
color = Color{bg}

[node name="World" type="Node2D" parent="."]

[node name="Floor" type="ColorRect" parent="World"]
offset_left = -280.0
offset_top = -240.0
offset_right = 280.0
offset_bottom = 240.0
color = Color(0.22, 0.28, 0.18, 1)

[node name="WallTop" type="StaticBody2D" parent="World"]
position = Vector2(0, -248)

[node name="WallTopCol" type="CollisionShape2D" parent="World/WallTop"]
shape = SubResource("wall_h")

[node name="WallTopSprite" type="ColorRect" parent="World/WallTop"]
offset_left = -300.0
offset_top = -8.0
offset_right = 300.0
offset_bottom = 8.0
color = Color(0.35, 0.25, 0.2, 1)

[node name="WallBottom" type="StaticBody2D" parent="World"]
position = Vector2(0, 248)

[node name="WallBotCol" type="CollisionShape2D" parent="World/WallBottom"]
shape = SubResource("wall_h")

[node name="WallBotSprite" type="ColorRect" parent="World/WallBottom"]
offset_left = -300.0
offset_top = -8.0
offset_right = 300.0
offset_bottom = 8.0
color = Color(0.35, 0.25, 0.2, 1)

[node name="Player" parent="World" instance=ExtResource("player")]
position = Vector2(0, 0)
{enemy_inst}{coin_inst}
[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')
        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

    def _write_enemy(self) -> None:
        self._write("scripts/enemy.gd", '''extends CharacterBody2D
## Patrol enemy that chases the player when nearby.

const SPEED := 60.0
const CHASE_SPEED := 100.0
const CHASE_RANGE := 150.0
const DAMAGE := 20
const DAMAGE_COOLDOWN := 1.0

var _direction := Vector2.RIGHT
var _origin := Vector2.ZERO
var _patrol_range := 120.0
var _cooldown := 0.0


func _ready() -> void:
\t_origin = global_position


func _physics_process(delta: float) -> void:
\t_cooldown = max(0.0, _cooldown - delta)
\tvar player := _find_player()
\tif player and global_position.distance_to(player.global_position) < CHASE_RANGE:
\t\tvelocity = global_position.direction_to(player.global_position) * CHASE_SPEED
\t\tif _cooldown <= 0.0 and global_position.distance_to(player.global_position) < 24.0:
\t\t\tGameManager.take_damage(DAMAGE)
\t\t\t_cooldown = DAMAGE_COOLDOWN
\telse:
\t\tvelocity = _direction * SPEED
\t\tif global_position.distance_to(_origin) > _patrol_range:
\t\t\t_direction = (_origin - global_position).normalized()
\tmove_and_slide()


func _find_player() -> CharacterBody2D:
\tfor child in get_parent().get_children():
\t\tif child.name == "Player":
\t\t\treturn child as CharacterBody2D
\treturn null
''')
        self._write("scenes/enemy.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="CircleShape2D" id="ecol"]
radius = 12.0

[node name="Enemy" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_secondary)}
scale = Vector2(0.35, 0.35)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    def _write_collectible(self) -> None:
        self._write("scripts/collectible.gd", '''extends Area2D

const SCORE_VALUE := 10
const PULSE_SPEED := 4.0


func _ready() -> void:
\tbody_entered.connect(_on_body_entered)


func _process(_delta: float) -> void:
\tvar s := 1.0 + sin(Time.get_ticks_msec() / 1000.0 * PULSE_SPEED) * 0.12
\tscale = Vector2(s, s)


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D:
\t\tGameManager.add_score(SCORE_VALUE)
\t\tqueue_free()
''')
        self._write("scenes/collectible.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/collectible.gd" id="1"]

[sub_resource type="CircleShape2D" id="ccol"]
radius = 10.0

[node name="Collectible" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]
modulate = Color(1, 0.85, 0.1, 1)
scale = Vector2(0.18, 0.18)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ccol")
''')
