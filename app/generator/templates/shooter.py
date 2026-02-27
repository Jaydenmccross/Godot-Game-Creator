"""Space Shooter — multi-level vertical scrolling, bullets, enemy waves.

Each level is a wave with increasing enemy density:
- Level 1: Few slow enemies, gentle introduction
- Level 2: More enemies, faster sine-wave patterns
- Level 3+: Dense waves, faster descent, tighter dodging
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class ShooterTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_player()
        self._write_bullet()
        if self.spec.has_enemies:
            self._write_enemy()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    # ── player ship (Area2D triangle) ────────────────────────────────────

    def _write_player(self) -> None:
        primary = self._hex_to_godot_color(self.spec.color_primary)
        self._write("scripts/player.gd", f'''extends Area2D
## {self.spec.player_name} — Space shooter ship with shooting.

const SPEED := 400.0
const FIRE_RATE := 0.18

var _fire_timer := 0.0
var bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")


func _ready() -> void:
\tarea_entered.connect(_on_area_entered)


func _process(delta: float) -> void:
\tvar dir := Vector2(
\t\tInput.get_axis("move_left", "move_right"),
\t\tInput.get_axis("move_up", "move_down"),
\t).normalized()
\tposition += dir * SPEED * delta
\tposition.x = clamp(position.x, 20, 1260)
\tposition.y = clamp(position.y, 20, 700)

\t_fire_timer -= delta
\tif Input.is_action_pressed("action") and _fire_timer <= 0.0:
\t\t_shoot()
\t\t_fire_timer = FIRE_RATE


func _shoot() -> void:
\tvar b := bullet_scene.instantiate()
\tb.position = global_position + Vector2(0, -30)
\tget_parent().add_child(b)


func _on_area_entered(other: Area2D) -> void:
\tif other.is_in_group("enemies"):
\t\tGameManager.take_damage(20)
\t\tother.queue_free()
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(32, 40)

[node name="Player" type="Area2D"]
script = ExtResource("1")

[node name="Body" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-16, 20, 0, -24, 16, 20)
color = Color{primary}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")
''')

    # ── bullet projectile ────────────────────────────────────────────────

    def _write_bullet(self) -> None:
        accent = self._hex_to_godot_color(self.spec.color_accent)
        self._write("scripts/bullet.gd", '''extends Area2D

const SPEED := 700.0


func _ready() -> void:
\tarea_entered.connect(_on_hit)


func _process(delta: float) -> void:
\tposition.y -= SPEED * delta
\tif position.y < -20:
\t\tqueue_free()


func _on_hit(other: Area2D) -> void:
\tif other.is_in_group("enemies"):
\t\tGameManager.add_score(10)
\t\tother.queue_free()
\t\tqueue_free()
''')
        self._write("scenes/bullet.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/bullet.gd" id="1"]

[sub_resource type="RectangleShape2D" id="bcol"]
size = Vector2(4, 14)

[node name="Bullet" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-2, 7, 0, -9, 2, 7)
color = Color{accent}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("bcol")
''')

    # ── enemy ship (sine-wave descent) ───────────────────────────────────

    def _write_enemy(self) -> None:
        secondary = self._hex_to_godot_color(self.spec.color_secondary)
        self._write("scripts/enemy.gd", '''extends Area2D
## Descending enemy ship — sine-wave pattern, damages player on contact.

var speed := 120.0
var wave_amplitude := 1.5
var _wave_offset := 0.0


func _ready() -> void:
\tadd_to_group("enemies")
\t_wave_offset = randf() * TAU


func _process(delta: float) -> void:
\tposition.y += speed * delta
\tposition.x += sin(Time.get_ticks_msec() / 1000.0 * 2.0 + _wave_offset) * wave_amplitude
\tif position.y > 760:
\t\tqueue_free()
''')
        self._write("scenes/enemy.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemy.gd" id="1"]

[sub_resource type="RectangleShape2D" id="ecol"]
size = Vector2(28, 28)

[node name="Enemy" type="Area2D"]
script = ExtResource("1")

[node name="Body" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-14, -14, 0, 18, 14, -14)
color = Color{secondary}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    # ── level generation ─────────────────────────────────────────────────

    def _write_level(self, level_num: int) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        ground = self._hex_to_godot_color(self.spec.color_ground)
        accent = self._hex_to_godot_color(self.spec.color_accent)

        kills_to_clear = 5 + level_num * 5
        spawn_interval = max(0.4, 1.4 - level_num * 0.2)
        enemy_speed = 100 + level_num * 30
        wave_amp = 1.0 + level_num * 0.5

        ext_res = '''[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]'''
        load_steps = 4

        if self.spec.has_enemies:
            ext_res += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
            load_steps += 1

        enemy_spawner = ""
        if self.spec.has_enemies:
            enemy_spawner = f'''
[node name="EnemySpawner" type="Timer" parent="."]
wait_time = {spawn_interval}
autostart = true
'''

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps={load_steps + 1} format=3]

{ext_res}

[node name="Game" type="Node2D"]
script = ExtResource("1")

[node name="BG" type="ColorRect" parent="."]
offset_right = 1280.0
offset_bottom = 720.0
color = Color{bg}

[node name="Stars" type="Node2D" parent="."]

[node name="Player" parent="." instance=ExtResource("player")]
position = Vector2(640, 600)

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
{enemy_spawner}''')

        enemy_spawn_code = ""
        spawner_connect = ""
        if self.spec.has_enemies:
            enemy_spawn_code = f'''
var _enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")
var _kills: int = 0
const KILLS_TO_CLEAR: int = {kills_to_clear}
const ENEMY_SPEED: float = {enemy_speed}.0
const WAVE_AMP: float = {wave_amp}
'''
            spawner_connect = '''\tif has_node("EnemySpawner"):
\t\t$EnemySpawner.timeout.connect(_spawn_enemy)'''

        self._write("scripts/game_level.gd", f'''extends Node2D
{enemy_spawn_code}

func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
{spawner_connect}
\t_create_stars()
\tget_tree().node_added.connect(_on_node_added)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")


func _create_stars() -> void:
\tfor i in 60:
\t\tvar star := ColorRect.new()
\t\tstar.size = Vector2(2, 2)
\t\tstar.color = Color(1, 1, 1, randf_range(0.3, 1.0))
\t\tstar.position = Vector2(randf_range(0, 1280), randf_range(0, 720))
\t\t$Stars.add_child(star)

{"" if not self.spec.has_enemies else """
func _spawn_enemy() -> void:
\tvar e := _enemy_scene.instantiate()
\te.position = Vector2(randf_range(60, 1220), -40)
\te.speed = ENEMY_SPEED
\te.wave_amplitude = WAVE_AMP
\tadd_child(e)


func _on_node_added(node: Node) -> void:
\tif node.is_in_group("enemies"):
\t\tnode.tree_exiting.connect(_on_enemy_killed)


func _on_enemy_killed() -> void:
\t_kills += 1
\tif _kills >= KILLS_TO_CLEAR:
\t\tLevelManager.advance_level()
"""}''')
