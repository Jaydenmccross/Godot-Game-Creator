"""2D Platformer template — GDquest-style state machine player, enemies, collectibles."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class PlatformerTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_player()
        self._write_game_scene()
        if self.spec.has_enemies:
            self._write_enemy()
        if self.spec.has_collectibles:
            self._write_collectible()

    # -- player ---------------------------------------------------------------

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — 2D platformer player using a state-machine pattern (GDquest style).

enum State {{ IDLE, RUN, JUMP, FALL }}

const SPEED := 300.0
const JUMP_VELOCITY := -480.0
const GRAVITY_SCALE := 1.0

var state: State = State.IDLE

@onready var sprite: Sprite2D = $Sprite2D
@onready var anim: AnimatedSprite2D = $AnimatedSprite2D if has_node("AnimatedSprite2D") else null


func _physics_process(delta: float) -> void:
\tvar gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity") * GRAVITY_SCALE
\tvelocity.y += gravity * delta

\tvar dir := Input.get_axis("move_left", "move_right")
\tvelocity.x = dir * SPEED

\tif dir != 0.0 and sprite:
\t\tsprite.flip_h = dir < 0.0

\t_update_state()
\tmove_and_slide()
\t_check_fall_death()


func _update_state() -> void:
\tif is_on_floor():
\t\tif Input.is_action_just_pressed("jump"):
\t\t\tvelocity.y = JUMP_VELOCITY
\t\t\t_set_state(State.JUMP)
\t\telif abs(velocity.x) > 10.0:
\t\t\t_set_state(State.RUN)
\t\telse:
\t\t\t_set_state(State.IDLE)
\telse:
\t\tif velocity.y > 0.0:
\t\t\t_set_state(State.FALL)


func _set_state(new_state: State) -> void:
\tif state == new_state:
\t\treturn
\tstate = new_state


func _check_fall_death() -> void:
\tif global_position.y > 800.0:
\t\tGameManager.take_damage(100)
\t\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_primary)}
scale = Vector2(0.5, 0.5)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("RectangleShape2D_player")

[sub_resource type="RectangleShape2D" id="RectangleShape2D_player"]
size = Vector2(28, 48)

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(1.5, 1.5)
position_smoothing_enabled = true
''')

    # -- game scene -----------------------------------------------------------

    def _write_game_scene(self) -> None:
        enemy_instance = ""
        collectible_instances = ""
        if self.spec.has_enemies:
            enemy_instance = """
[node name="Enemy1" parent="Level" instance=ExtResource("enemy")]
position = Vector2(500, 268)

[node name="Enemy2" parent="Level" instance=ExtResource("enemy")]
position = Vector2(900, 108)
"""
        if self.spec.has_collectibles:
            collectible_instances = """
[node name="Coin1" parent="Level" instance=ExtResource("coin")]
position = Vector2(300, 230)

[node name="Coin2" parent="Level" instance=ExtResource("coin")]
position = Vector2(450, 180)

[node name="Coin3" parent="Level" instance=ExtResource("coin")]
position = Vector2(650, 230)

[node name="Coin4" parent="Level" instance=ExtResource("coin")]
position = Vector2(800, 60)

[node name="Coin5" parent="Level" instance=ExtResource("coin")]
position = Vector2(1050, 160)
"""

        load_steps = 4
        ext_resources = '''[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]'''
        if self.spec.has_enemies:
            load_steps += 1
            ext_resources += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
        if self.spec.has_collectibles:
            load_steps += 1
            ext_resources += '\n[ext_resource type="PackedScene" path="res://scenes/collectible.tscn" id="coin"]'

        bg_color = self._hex_to_godot_color(self.spec.color_bg)

        self._write("scenes/game.tscn", f'''[gd_scene load_steps={load_steps + 3} format=3]

{ext_resources}

[sub_resource type="RectangleShape2D" id="ground_shape"]
size = Vector2(2400, 32)

[sub_resource type="RectangleShape2D" id="plat_shape"]
size = Vector2(200, 16)

[sub_resource type="RectangleShape2D" id="plat_shape2"]
size = Vector2(160, 16)

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
offset_right = 2400.0
offset_bottom = 800.0
color = Color{bg_color}

[node name="Level" type="Node2D" parent="."]

[node name="Ground" type="StaticBody2D" parent="Level"]
position = Vector2(1200, 316)

[node name="GroundCollision" type="CollisionShape2D" parent="Level/Ground"]
shape = SubResource("ground_shape")

[node name="GroundSprite" type="ColorRect" parent="Level/Ground"]
offset_left = -1200.0
offset_top = -16.0
offset_right = 1200.0
offset_bottom = 16.0
color = Color(0.25, 0.55, 0.22, 1)

[node name="Platform1" type="StaticBody2D" parent="Level"]
position = Vector2(400, 220)

[node name="P1Col" type="CollisionShape2D" parent="Level/Platform1"]
shape = SubResource("plat_shape")

[node name="P1Sprite" type="ColorRect" parent="Level/Platform1"]
offset_left = -100.0
offset_top = -8.0
offset_right = 100.0
offset_bottom = 8.0
color = Color(0.4, 0.35, 0.3, 1)

[node name="Platform2" type="StaticBody2D" parent="Level"]
position = Vector2(750, 160)

[node name="P2Col" type="CollisionShape2D" parent="Level/Platform2"]
shape = SubResource("plat_shape2")

[node name="P2Sprite" type="ColorRect" parent="Level/Platform2"]
offset_left = -80.0
offset_top = -8.0
offset_right = 80.0
offset_bottom = 8.0
color = Color(0.4, 0.35, 0.3, 1)

[node name="Platform3" type="StaticBody2D" parent="Level"]
position = Vector2(1050, 120)

[node name="P3Col" type="CollisionShape2D" parent="Level/Platform3"]
shape = SubResource("plat_shape")

[node name="P3Sprite" type="ColorRect" parent="Level/Platform3"]
offset_left = -100.0
offset_top = -8.0
offset_right = 100.0
offset_bottom = 8.0
color = Color(0.4, 0.35, 0.3, 1)

[node name="Player" parent="Level" instance=ExtResource("player")]
position = Vector2(100, 260)
{enemy_instance}{collectible_instances}
[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')
        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

    # -- enemy ----------------------------------------------------------------

    def _write_enemy(self) -> None:
        self._write("scripts/enemy.gd", '''extends CharacterBody2D
## Simple patrol enemy — walks back and forth on platforms.

const SPEED := 80.0
const GRAVITY_SCALE := 1.0

var direction := 1.0
var _patrol_distance := 200.0
var _origin_x := 0.0

@onready var sprite: Sprite2D = $Sprite2D


func _ready() -> void:
\t_origin_x = global_position.x


func _physics_process(delta: float) -> void:
\tvar gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")
\tvelocity.y += gravity * delta
\tvelocity.x = direction * SPEED

\tmove_and_slide()

\tif global_position.x > _origin_x + _patrol_distance:
\t\tdirection = -1.0
\telif global_position.x < _origin_x - _patrol_distance:
\t\tdirection = 1.0

\tif sprite:
\t\tsprite.flip_h = direction < 0.0

\tfor i in get_slide_collision_count():
\t\tvar col := get_slide_collision(i)
\t\tvar collider := col.get_collider()
\t\tif collider is CharacterBody2D and collider.has_method("_check_fall_death"):
\t\t\tGameManager.take_damage(25)
''')
        self._write("scenes/enemy.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="RectangleShape2D" id="enemy_shape"]
size = Vector2(24, 24)

[node name="Enemy" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_secondary)}
scale = Vector2(0.35, 0.35)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("enemy_shape")
''')

    # -- collectible ----------------------------------------------------------

    def _write_collectible(self) -> None:
        self._write("scripts/collectible.gd", '''extends Area2D
## Collectible coin — awards points on pickup.

const SCORE_VALUE := 10
const BOB_SPEED := 3.0
const BOB_HEIGHT := 6.0

var _base_y := 0.0


func _ready() -> void:
\t_base_y = position.y
\tbody_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
\tposition.y = _base_y + sin(Time.get_ticks_msec() / 1000.0 * BOB_SPEED) * BOB_HEIGHT


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D:
\t\tGameManager.add_score(SCORE_VALUE)
\t\tqueue_free()
''')
        self._write("scenes/collectible.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/collectible.gd" id="1"]

[sub_resource type="CircleShape2D" id="coin_shape"]
radius = 12.0

[node name="Collectible" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]
modulate = Color(1, 0.85, 0.1, 1)
scale = Vector2(0.2, 0.2)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("coin_shape")
''')
