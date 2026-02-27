"""2D Platformer — multi-level, animated sprites, state-machine player.

Each level is a distinct scene with increasing difficulty:
- Level 1: Tutorial — few enemies, wide platforms, many collectibles
- Level 2: Challenge — moving platforms, more enemies, tighter gaps
- Level 3: Gauntlet — dense enemies, narrow platforms, level-end goal
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class PlatformerTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_player()
        if self.spec.has_enemies:
            self._write_enemy()
        if self.spec.has_collectibles:
            self._write_collectible()
        self._write_level_goal()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    # ── player with animated sprite ──────────────────────────────────────

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends CharacterBody2D
## {self.spec.player_name} — platformer player with animated sprite and state machine.

enum State {{ IDLE, RUN, JUMP, FALL, ATTACK }}

const SPEED := 300.0
const JUMP_VELOCITY := -480.0
const ATTACK_DURATION := 0.3

var state: State = State.IDLE
var facing_right: bool = true
var _attack_timer := 0.0

@onready var anim_sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\tvar color := Color("{self.spec.color_primary}")
\tvar detail := color.lightened(0.4)
\tanim_sprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, detail)
\tanim_sprite.play("idle_right")


func _physics_process(delta: float) -> void:
\tvar gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")
\tvelocity.y += gravity * delta

\t# Attack cooldown
\tif state == State.ATTACK:
\t\t_attack_timer -= delta
\t\tif _attack_timer <= 0.0:
\t\t\tstate = State.IDLE

\tvar dir := Input.get_axis("move_left", "move_right")
\tif state != State.ATTACK:
\t\tvelocity.x = dir * SPEED
\telse:
\t\tvelocity.x = move_toward(velocity.x, 0, SPEED * delta * 3)

\tif dir > 0.0:
\t\tfacing_right = true
\telif dir < 0.0:
\t\tfacing_right = false

\t_update_state()
\t_update_animation()
\tmove_and_slide()
\t_check_fall_death()


func _update_state() -> void:
\tif state == State.ATTACK:
\t\treturn
\tif Input.is_action_just_pressed("action"):
\t\tstate = State.ATTACK
\t\t_attack_timer = ATTACK_DURATION
\t\t_do_attack()
\t\treturn
\tif is_on_floor():
\t\tif Input.is_action_just_pressed("jump"):
\t\t\tvelocity.y = JUMP_VELOCITY
\t\t\tstate = State.JUMP
\t\telif abs(velocity.x) > 10.0:
\t\t\tstate = State.RUN
\t\telse:
\t\t\tstate = State.IDLE
\telse:
\t\tstate = State.FALL if velocity.y > 0.0 else State.JUMP


func _update_animation() -> void:
\tvar suffix := "_right" if facing_right else "_left"
\tvar anim_name: String
\tmatch state:
\t\tState.IDLE:    anim_name = "idle" + suffix
\t\tState.RUN:     anim_name = "run" + suffix
\t\tState.JUMP:    anim_name = "jump" + suffix
\t\tState.FALL:    anim_name = "fall" + suffix
\t\tState.ATTACK:  anim_name = "attack" + suffix
\t\t_:             anim_name = "idle" + suffix
\tif anim_sprite.animation != anim_name:
\t\tanim_sprite.play(anim_name)


func _do_attack() -> void:
\tvar attack_range := 40.0
\tvar attack_dir := Vector2.RIGHT if facing_right else Vector2.LEFT
\tvar space := get_world_2d().direct_space_state
\tvar query := PhysicsRayQueryParameters2D.create(
\t\tglobal_position, global_position + attack_dir * attack_range)
\tquery.exclude = [get_rid()]
\tvar result := space.intersect_ray(query)
\tif result and result.collider.has_method("take_hit"):
\t\tresult.collider.take_hit(1)


func _check_fall_death() -> void:
\tif global_position.y > 800.0:
\t\tGameManager.take_damage(100)
\t\tLevelManager.restart_level()
''')

        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(20, 40)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.5, 1.5)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(1.5, 1.5)
position_smoothing_enabled = true
limit_bottom = 400
''')

    # ── enemy ────────────────────────────────────────────────────────────

    def _write_enemy(self) -> None:
        self._write("scripts/enemy.gd", f'''extends CharacterBody2D
## Patrol enemy — walks back and forth, damages player on touch.

const SPEED := 80.0
const DAMAGE := 20
const DAMAGE_COOLDOWN := 1.0

var direction := 1.0
var _patrol_range := 180.0
var _origin_x := 0.0
var _cooldown := 0.0
var _hp := 2

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\t_origin_x = global_position.x
\tvar color := Color("{self.spec.color_secondary}")
\tsprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
\tsprite.play("run_right")


func _physics_process(delta: float) -> void:
\tvar gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")
\tvelocity.y += gravity * delta
\tvelocity.x = direction * SPEED
\t_cooldown = max(0.0, _cooldown - delta)

\tmove_and_slide()

\tif global_position.x > _origin_x + _patrol_range:
\t\tdirection = -1.0
\t\tsprite.play("run_left")
\telif global_position.x < _origin_x - _patrol_range:
\t\tdirection = 1.0
\t\tsprite.play("run_right")

\tfor i in get_slide_collision_count():
\t\tvar col := get_slide_collision(i)
\t\tvar collider := col.get_collider()
\t\tif collider is CharacterBody2D and collider.has_method("_check_fall_death"):
\t\t\tif _cooldown <= 0.0:
\t\t\t\tGameManager.take_damage(DAMAGE)
\t\t\t\t_cooldown = DAMAGE_COOLDOWN


func take_hit(damage: int) -> void:
\t_hp -= damage
\tif _hp <= 0:
\t\tGameManager.add_score(25)
\t\tqueue_free()
\telse:
\t\tmodulate = Color.RED
\t\tawait get_tree().create_timer(0.15).timeout
\t\tmodulate = Color.WHITE
''')
        self._write("scenes/enemy.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="RectangleShape2D" id="ecol"]
size = Vector2(18, 36)

[node name="Enemy" type="CharacterBody2D"]
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.2, 1.2)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    # ── collectible ──────────────────────────────────────────────────────

    def _write_collectible(self) -> None:
        self._write("scripts/collectible.gd", '''extends Area2D
## Collectible — awards points on pickup with bobbing animation.

const SCORE_VALUE := 10
const BOB_SPEED := 3.0
const BOB_HEIGHT := 6.0

var _base_y := 0.0


func _ready() -> void:
\t_base_y = position.y
\tbody_entered.connect(_on_body_entered)


func _process(_delta: float) -> void:
\tposition.y = _base_y + sin(Time.get_ticks_msec() / 1000.0 * BOB_SPEED) * BOB_HEIGHT


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D:
\t\tGameManager.add_score(SCORE_VALUE)
\t\tqueue_free()
''')
        self._write("scenes/collectible.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/collectible.gd" id="1"]

[sub_resource type="CircleShape2D" id="ccol"]
radius = 12.0

[node name="Collectible" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]
modulate = Color(1, 0.85, 0.1, 1)
scale = Vector2(0.2, 0.2)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ccol")
''')

    # ── level goal (triggers level transition) ───────────────────────────

    def _write_level_goal(self) -> None:
        self._write("scripts/level_goal.gd", '''extends Area2D
## Level exit — triggers transition to next level when touched.


func _ready() -> void:
\tbody_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
\tif body is CharacterBody2D and body.has_method("_check_fall_death"):
\t\tGameManager.add_score(50)
\t\tLevelManager.advance_level()
''')
        self._write("scenes/level_goal.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/level_goal.gd" id="1"]

[sub_resource type="RectangleShape2D" id="gcol"]
size = Vector2(32, 64)

[node name="LevelGoal" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="ColorRect" parent="."]
offset_left = -16.0
offset_top = -32.0
offset_right = 16.0
offset_bottom = 32.0
color = Color(0.2, 1.0, 0.4, 0.8)

[node name="Flag" type="ColorRect" parent="."]
offset_left = -2.0
offset_top = -48.0
offset_right = 2.0
offset_bottom = 32.0
color = Color(1, 1, 1, 0.6)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("gcol")
''')

    # ── level generation ─────────────────────────────────────────────────

    def _write_level(self, level_num: int) -> None:
        """Generate a distinct level scene based on level number."""
        bg = self._hex_to_godot_color(self.spec.color_bg)
        ground_color = self._hex_to_godot_color(self.spec.color_ground)

        difficulty_scale = level_num
        ground_width = max(1600, 3200 - level_num * 400)
        plat_count = 3 + level_num * 2
        enemy_count = level_num * 2 if self.spec.has_enemies else 0
        coin_count = max(3, 8 - level_num) if self.spec.has_collectibles else 0

        ext_resources = '''[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]
[ext_resource type="PackedScene" path="res://scenes/level_goal.tscn" id="goal"]'''

        load_steps = 5
        if self.spec.has_enemies:
            ext_resources += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
            load_steps += 1
        if self.spec.has_collectibles:
            ext_resources += '\n[ext_resource type="PackedScene" path="res://scenes/collectible.tscn" id="coin"]'
            load_steps += 1

        platforms = ""
        plat_y_base = 260
        for i in range(plat_count):
            px = 200 + i * int(ground_width / (plat_count + 1))
            py = plat_y_base - (i % 3) * 60 - (i // 3) * 40
            pw = max(80, 180 - difficulty_scale * 20)
            platforms += f'''
[node name="Platform{i+1}" type="StaticBody2D" parent="Level"]
position = Vector2({px}, {py})

[node name="P{i+1}Col" type="CollisionShape2D" parent="Level/Platform{i+1}"]
shape = SubResource("plat_shape")

[node name="P{i+1}Sprite" type="ColorRect" parent="Level/Platform{i+1}"]
offset_left = -{pw//2}.0
offset_top = -8.0
offset_right = {pw//2}.0
offset_bottom = 8.0
color = Color(0.4, 0.35, 0.3, 1)
'''

        enemies = ""
        for i in range(enemy_count):
            ex = 300 + i * int(ground_width / (enemy_count + 1))
            ey = 268
            enemies += f'''
[node name="Enemy{i+1}" parent="Level" instance=ExtResource("enemy")]
position = Vector2({ex}, {ey})
'''

        coins = ""
        for i in range(coin_count):
            cx = 200 + i * int(ground_width / (coin_count + 1))
            cy = 200 - (i % 3) * 40
            coins += f'''
[node name="Coin{i+1}" parent="Level" instance=ExtResource("coin")]
position = Vector2({cx}, {cy})
'''

        goal_x = ground_width - 100

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps={load_steps + 2} format=3]

{ext_resources}

[sub_resource type="RectangleShape2D" id="ground_shape"]
size = Vector2({ground_width}, 32)

[sub_resource type="RectangleShape2D" id="plat_shape"]
size = Vector2(180, 16)

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
offset_right = {ground_width}.0
offset_bottom = 800.0
color = Color{bg}

[node name="Level" type="Node2D" parent="."]

[node name="Ground" type="StaticBody2D" parent="Level"]
position = Vector2({ground_width//2}, 316)

[node name="GroundCol" type="CollisionShape2D" parent="Level/Ground"]
shape = SubResource("ground_shape")

[node name="GroundSprite" type="ColorRect" parent="Level/Ground"]
offset_left = -{ground_width//2}.0
offset_top = -16.0
offset_right = {ground_width//2}.0
offset_bottom = 16.0
color = Color{ground_color}
{platforms}
[node name="Player" parent="Level" instance=ExtResource("player")]
position = Vector2(80, 260)
{enemies}{coins}
[node name="Goal" parent="Level" instance=ExtResource("goal")]
position = Vector2({goal_x}, 270)

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')

        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')
