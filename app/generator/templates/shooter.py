"""Space Shooter template — vertical scrolling, bullets, enemy waves."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class ShooterTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_player()
        self._write_bullet()
        self._write_game_scene()
        if self.spec.has_enemies:
            self._write_enemy()

    def _write_player(self) -> None:
        self._write("scripts/player.gd", f'''extends Area2D
## {self.spec.player_name} — Space shooter ship with shooting.

const SPEED := 400.0
const FIRE_RATE := 0.18

var _fire_timer := 0.0
var bullet_scene: PackedScene = preload("res://scenes/bullet.tscn")


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
''')
        self._write("scenes/player.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(32, 40)

[node name="Player" type="Area2D"]
script = ExtResource("1")

[node name="Sprite2D" type="Sprite2D" parent="."]
modulate = Color{self._hex_to_godot_color(self.spec.color_primary)}
scale = Vector2(0.5, 0.5)
rotation = -1.5708

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("pcol")

[node name="Body" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-16, 20, 0, -24, 16, 20)
color = Color{self._hex_to_godot_color(self.spec.color_primary)}
''')

    def _write_bullet(self) -> None:
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
        self._write("scenes/bullet.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/bullet.gd" id="1"]

[sub_resource type="RectangleShape2D" id="bcol"]
size = Vector2(4, 14)

[node name="Bullet" type="Area2D"]
script = ExtResource("1")

[node name="Sprite" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-2, 7, 0, -9, 2, 7)
color = Color(1, 1, 0.4, 1)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("bcol")
''')

    def _write_enemy(self) -> None:
        self._write("scripts/enemy.gd", f'''extends Area2D
## Descending enemy ship that damages the player on contact.

const SPEED := 120.0
const SCORE_VALUE := 10

var _wave_offset := 0.0


func _ready() -> void:
\tadd_to_group("enemies")
\t_wave_offset = randf() * TAU
\tarea_entered.connect(_on_area_entered)


func _process(delta: float) -> void:
\tposition.y += SPEED * delta
\tposition.x += sin(Time.get_ticks_msec() / 1000.0 * 2.0 + _wave_offset) * 1.5
\tif position.y > 760:
\t\tqueue_free()


func _on_area_entered(other: Area2D) -> void:
\tif other.name == "Player":
\t\tGameManager.take_damage(20)
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
color = Color{self._hex_to_godot_color(self.spec.color_secondary)}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    def _write_game_scene(self) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        enemy_spawner = ""
        loads = 4
        ext_extra = ""
        if self.spec.has_enemies:
            loads += 1
            ext_extra += '\n[ext_resource type="PackedScene" path="res://scenes/enemy.tscn" id="enemy"]'
            enemy_spawner = '\n[node name="EnemySpawner" type="Timer" parent="."]\nwait_time = 1.2\nautostart = true'

        self._write("scenes/game.tscn", f'''[gd_scene load_steps={loads + 1} format=3]

[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/player.tscn" id="player"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]{ext_extra}

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
{enemy_spawner}
''')

        enemy_spawn_code = ""
        if self.spec.has_enemies:
            enemy_spawn_code = '''
var _enemy_scene: PackedScene = preload("res://scenes/enemy.tscn")


func _spawn_enemy() -> void:
\tvar e := _enemy_scene.instantiate()
\te.position = Vector2(randf_range(60, 1220), -40)
\tadd_child(e)
'''

        self._write("scripts/game_level.gd", f'''extends Node2D
{enemy_spawn_code}

func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
{"\\tif has_node(\"EnemySpawner\"):\\n\\t\\t$EnemySpawner.timeout.connect(_spawn_enemy)" if self.spec.has_enemies else ""}
\t_create_stars()


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")


func _create_stars() -> void:
\tfor i in 60:
\t\tvar star := ColorRect.new()
\t\tstar.size = Vector2(2, 2)
\t\tstar.color = Color(1, 1, 1, randf_range(0.3, 1.0))
\t\tstar.position = Vector2(randf_range(0, 1280), randf_range(0, 720))
\t\t$Stars.add_child(star)
''')
