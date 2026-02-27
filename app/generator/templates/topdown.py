"""Top-Down Adventure — multi-room dungeon, 4-directional animated player, enemies, items.

Levels are distinct dungeon rooms with increasing complexity:
- Level 1: Small room with a few enemies and items
- Level 2: Larger room with more enemies and obstacles
- Level 3: Boss room with a stronger enemy
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class TopdownTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_player()
        if self.spec.has_enemies:
            self._write_enemy()
        if self.spec.has_collectibles:
            self._write_collectible()
        self._write_level_goal()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — 4-directional top-down character with animated attacks.

enum State {{ IDLE, WALK, ATTACK }}

const SPEED := 200.0
const ATTACK_DURATION := 0.25
const ATTACK_RANGE := 36.0
const ATTACK_DAMAGE := 1

var state: State = State.IDLE
var facing := "down"
var _attack_timer := 0.0

@onready var anim_sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\tvar color := Color("{self.spec.color_primary}")
\tanim_sprite.sprite_frames = SpriteGenerator.create_topdown_frames(color, color.lightened(0.5))
\tanim_sprite.play("idle_down")


func _physics_process(delta: float) -> void:
\tif state == State.ATTACK:
\t\t_attack_timer -= delta
\t\tif _attack_timer <= 0.0:
\t\t\tstate = State.IDLE
\t\tvelocity = velocity.move_toward(Vector2.ZERO, SPEED * delta * 4)
\t\tmove_and_slide()
\t\treturn

\tvar input_dir := Vector2(
\t\tInput.get_axis("move_left", "move_right"),
\t\tInput.get_axis("move_up", "move_down"),
\t).normalized()

\tvelocity = input_dir * SPEED

\tif input_dir != Vector2.ZERO:
\t\tstate = State.WALK
\t\tif abs(input_dir.x) > abs(input_dir.y):
\t\t\tfacing = "right" if input_dir.x > 0 else "left"
\t\telse:
\t\t\tfacing = "down" if input_dir.y > 0 else "up"
\telse:
\t\tstate = State.IDLE

\tif Input.is_action_just_pressed("action"):
\t\tstate = State.ATTACK
\t\t_attack_timer = ATTACK_DURATION
\t\t_do_attack()

\t_update_animation()
\tmove_and_slide()


func _update_animation() -> void:
\tvar prefix: String
\tmatch state:
\t\tState.IDLE:   prefix = "idle"
\t\tState.WALK:   prefix = "walk"
\t\tState.ATTACK: prefix = "attack"
\t\t_:            prefix = "idle"
\tvar anim_name := prefix + "_" + facing
\tif anim_sprite.animation != anim_name:
\t\tanim_sprite.play(anim_name)


func _do_attack() -> void:
\tvar attack_dir := Vector2.ZERO
\tmatch facing:
\t\t"up":    attack_dir = Vector2.UP
\t\t"down":  attack_dir = Vector2.DOWN
\t\t"left":  attack_dir = Vector2.LEFT
\t\t"right": attack_dir = Vector2.RIGHT
\tvar space := get_world_2d().direct_space_state
\tvar query := PhysicsRayQueryParameters2D.create(
\t\tglobal_position, global_position + attack_dir * ATTACK_RANGE)
\tquery.exclude = [get_rid()]
\tvar result := space.intersect_ray(query)
\tif result and result.collider.has_method("take_hit"):
\t\tresult.collider.take_hit(ATTACK_DAMAGE)
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="CircleShape2D" id="pcol"]
radius = 12.0

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.8, 1.8)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(2.0, 2.0)
position_smoothing_enabled = true
''')

    def _write_enemy(self) -> None:
        self._write("scripts/enemy.gd", f'''extends CharacterBody2D
## Patrol enemy that chases when player is nearby.

const SPEED := 55.0
const CHASE_SPEED := 90.0
const CHASE_RANGE := 140.0
const DAMAGE := 15
const COOLDOWN := 1.0

var _direction := Vector2.RIGHT
var _origin := Vector2.ZERO
var _patrol_range := 100.0
var _cd := 0.0
var _hp := 3

@onready var anim_sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\t_origin = global_position
\tvar color := Color("{self.spec.color_secondary}")
\tanim_sprite.sprite_frames = SpriteGenerator.create_topdown_frames(color, color.lightened(0.3))
\tanim_sprite.play("walk_right")


func _physics_process(delta: float) -> void:
\t_cd = max(0.0, _cd - delta)
\tvar player := _find_player()
\tif player and global_position.distance_to(player.global_position) < CHASE_RANGE:
\t\tvar dir := global_position.direction_to(player.global_position)
\t\tvelocity = dir * CHASE_SPEED
\t\tif _cd <= 0.0 and global_position.distance_to(player.global_position) < 22.0:
\t\t\tGameManager.take_damage(DAMAGE)
\t\t\t_cd = COOLDOWN
\telse:
\t\tvelocity = _direction * SPEED
\t\tif global_position.distance_to(_origin) > _patrol_range:
\t\t\t_direction = (_origin - global_position).normalized()
\t_update_anim()
\tmove_and_slide()


func _update_anim() -> void:
\tvar dir_name := "right"
\tif abs(velocity.x) > abs(velocity.y):
\t\tdir_name = "right" if velocity.x > 0 else "left"
\telse:
\t\tdir_name = "down" if velocity.y > 0 else "up"
\tvar anim_name := "walk_" + dir_name
\tif anim_sprite.animation != anim_name:
\t\tanim_sprite.play(anim_name)


func _find_player() -> CharacterBody2D:
\tfor child in get_parent().get_children():
\t\tif child.name == "Player":
\t\t\treturn child as CharacterBody2D
\treturn null


func take_hit(damage: int) -> void:
\t_hp -= damage
\tif _hp <= 0:
\t\tGameManager.add_score(30)
\t\tqueue_free()
\telse:
\t\tmodulate = Color.RED
\t\tawait get_tree().create_timer(0.15).timeout
\t\tmodulate = Color.WHITE
''')
        self._write("scenes/enemy.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="CircleShape2D" id="ecol"]
radius = 10.0

[node name="Enemy" type="CharacterBody2D"]
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.5, 1.5)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    def _write_collectible(self) -> None:
        self._write("scripts/collectible.gd", '''extends Area2D

const SCORE_VALUE := 10

var _base_scale := 1.0


func _ready() -> void:
\tbody_entered.connect(_on_body_entered)


func _process(_delta: float) -> void:
\tvar s := _base_scale + sin(Time.get_ticks_msec() / 1000.0 * 4.0) * 0.1
\tscale = Vector2(s, s)


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D:
\t\tGameManager.add_score(SCORE_VALUE)
\t\tqueue_free()
''')
        self._write("scenes/collectible.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/collectible.gd" id="1"]

[sub_resource type="CircleShape2D" id="ccol"]
radius = 8.0

[node name="Collectible" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]
modulate = Color(1, 0.85, 0.1, 1)
scale = Vector2(0.15, 0.15)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ccol")
''')

    def _write_level_goal(self) -> None:
        self._write("scripts/level_goal.gd", '''extends Area2D


func _ready() -> void:
\tbody_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D and body.has_method("_do_attack"):
\t\tGameManager.add_score(50)
\t\tLevelManager.advance_level()
''')
        self._write("scenes/level_goal.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/level_goal.gd" id="1"]

[sub_resource type="RectangleShape2D" id="gcol"]
size = Vector2(28, 28)

[node name="LevelGoal" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="ColorRect" parent="."]
offset_left = -14.0
offset_top = -14.0
offset_right = 14.0
offset_bottom = 14.0
color = Color(0.2, 1.0, 0.4, 0.8)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("gcol")
''')

    def _write_level(self, level_num: int) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        ground = self._hex_to_godot_color(self.spec.color_ground)
        room_size = 200 + level_num * 80
        enemy_count = level_num * 2 if self.spec.has_enemies else 0
        coin_count = max(2, 5 - level_num) if self.spec.has_collectibles else 0

        ext_res = '''[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]
[ext_resource type="PackedScene" path="res://scenes/level_goal.tscn" id="goal"]'''
        loads = 5
        if self.spec.has_enemies:
            ext_res += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
            loads += 1
        if self.spec.has_collectibles:
            ext_res += '\n[ext_resource type="PackedScene" path="res://scenes/collectible.tscn" id="coin"]'
            loads += 1

        enemies = ""
        for i in range(enemy_count):
            angle = i * (6.28 / max(1, enemy_count))
            ex = int(room_size * 0.5 * __import__('math').cos(angle))
            ey = int(room_size * 0.5 * __import__('math').sin(angle))
            enemies += f'''
[node name="Enemy{i+1}" parent="World" instance=ExtResource("enemy")]
position = Vector2({ex}, {ey})
'''

        coins = ""
        for i in range(coin_count):
            cx = -room_size // 3 + i * (room_size * 2 // 3 // max(1, coin_count))
            cy = -room_size // 3 + (i % 2) * (room_size // 2)
            coins += f'''
[node name="Coin{i+1}" parent="World" instance=ExtResource("coin")]
position = Vector2({cx}, {cy})
'''

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps={loads + 1} format=3]

{ext_res}

[sub_resource type="RectangleShape2D" id="wall_h"]
size = Vector2({room_size * 2 + 40}, 16)

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
offset_left = -{room_size}.0
offset_top = -{room_size}.0
offset_right = {room_size}.0
offset_bottom = {room_size}.0
color = Color{ground}

[node name="WallTop" type="StaticBody2D" parent="World"]
position = Vector2(0, -{room_size})

[node name="WTCol" type="CollisionShape2D" parent="World/WallTop"]
shape = SubResource("wall_h")

[node name="WTSprite" type="ColorRect" parent="World/WallTop"]
offset_left = -{room_size + 20}.0
offset_top = -8.0
offset_right = {room_size + 20}.0
offset_bottom = 8.0
color = Color(0.3, 0.22, 0.18, 1)

[node name="WallBottom" type="StaticBody2D" parent="World"]
position = Vector2(0, {room_size})

[node name="WBCol" type="CollisionShape2D" parent="World/WallBottom"]
shape = SubResource("wall_h")

[node name="WBSprite" type="ColorRect" parent="World/WallBottom"]
offset_left = -{room_size + 20}.0
offset_top = -8.0
offset_right = {room_size + 20}.0
offset_bottom = 8.0
color = Color(0.3, 0.22, 0.18, 1)

[node name="Player" parent="World" instance=ExtResource("player")]
position = Vector2(0, {room_size - 40})
{enemies}{coins}
[node name="Goal" parent="World" instance=ExtResource("goal")]
position = Vector2(0, -{room_size - 40})

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')
        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
