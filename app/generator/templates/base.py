"""Base template providing common scenes and scripts shared by all genres.

Follows GDquest design patterns:
- State machines for character behaviour
- Signal-based communication
- Typed GDScript (static typing)
- Clean node hierarchy
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import GameSpec


class BaseTemplate(ABC):
    def __init__(self, spec: GameSpec, project_dir: Path) -> None:
        self.spec = spec
        self.dir = project_dir

    def generate(self) -> None:
        self._write_game_manager()
        self._write_main_menu()
        self._write_hud()
        self._write_game_over()
        self._write_pause_menu()
        self.generate_game_scene()

    def _write(self, rel_path: str, content: str) -> None:
        p = self.dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def _write_game_manager(self) -> None:
        self._write("scripts/autoload/game_manager.gd", f'''extends Node

signal score_changed(new_score: int)
signal health_changed(new_health: int)
signal game_over

var score: int = 0:
\tset(value):
\t\tscore = value
\t\tscore_changed.emit(score)

var health: int = 100:
\tset(value):
\t\thealth = max(0, value)
\t\thealth_changed.emit(health)
\t\tif health <= 0:
\t\t\tgame_over.emit()

var is_paused: bool = false


func reset() -> void:
\tscore = 0
\thealth = 100
\tis_paused = false


func add_score(amount: int) -> void:
\tscore += amount


func take_damage(amount: int) -> void:
\thealth -= amount


func heal(amount: int) -> void:
\thealth = min(100, health + amount)


func go_to_scene(path: String) -> void:
\tget_tree().paused = false
\tis_paused = false
\tget_tree().change_scene_to_file(path)
''')

    def _write_main_menu(self) -> None:
        spec = self.spec
        self._write("scenes/main_menu.tscn", f'''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/main_menu.gd" id="1"]

[node name="MainMenu" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2
script = ExtResource("1")

[node name="Background" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
color = Color{self._hex_to_godot_color(spec.color_bg)}

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -200.0
offset_top = -150.0
offset_right = 200.0
offset_bottom = 150.0
grow_horizontal = 2
grow_vertical = 2
theme_override_constants/separation = 24

[node name="Title" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 48
text = "{spec.name}"
horizontal_alignment = 1

[node name="Subtitle" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 18
text = "A {spec.theme.title()} {spec.genre.value.replace('_', ' ').title()}"
horizontal_alignment = 1
modulate = Color(0.7, 0.7, 0.7, 1)

[node name="Spacer" type="Control" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 30)

[node name="PlayButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 22
text = "Play Game"

[node name="QuitButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 22
text = "Quit"
''')
        self._write("scripts/main_menu.gd", '''extends Control


func _ready() -> void:
\t$VBox/PlayButton.pressed.connect(_on_play)
\t$VBox/QuitButton.pressed.connect(_on_quit)
\tGameManager.reset()


func _on_play() -> void:
\tGameManager.go_to_scene("res://scenes/game.tscn")


func _on_quit() -> void:
\tget_tree().quit()
''')

    def _write_hud(self) -> None:
        self._write("scenes/hud.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/hud.gd" id="1"]

[node name="HUD" type="CanvasLayer"]
script = ExtResource("1")

[node name="TopBar" type="HBoxContainer" parent="."]
anchors_preset = 10
anchor_right = 1.0
offset_bottom = 40.0
theme_override_constants/separation = 40

[node name="ScoreLabel" type="Label" parent="TopBar"]
layout_mode = 2
theme_override_font_sizes/font_size = 24
text = "Score: 0"

[node name="HealthLabel" type="Label" parent="TopBar"]
layout_mode = 2
theme_override_font_sizes/font_size = 24
text = "Health: 100"

[node name="HealthBar" type="ProgressBar" parent="TopBar"]
layout_mode = 2
custom_minimum_size = Vector2(200, 0)
size_flags_vertical = 4
max_value = 100.0
value = 100.0
show_percentage = false
''')
        self._write("scripts/hud.gd", '''extends CanvasLayer


func _ready() -> void:
\tGameManager.score_changed.connect(_on_score_changed)
\tGameManager.health_changed.connect(_on_health_changed)
\t_on_score_changed(GameManager.score)
\t_on_health_changed(GameManager.health)


func _on_score_changed(new_score: int) -> void:
\t$TopBar/ScoreLabel.text = "Score: " + str(new_score)


func _on_health_changed(new_health: int) -> void:
\t$TopBar/HealthLabel.text = "Health: " + str(new_health)
\t$TopBar/HealthBar.value = new_health
''')

    def _write_game_over(self) -> None:
        self._write("scenes/game_over.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/game_over.gd" id="1"]

[node name="GameOver" type="Control"]
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
color = Color(0.05, 0.05, 0.1, 0.9)

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -200.0
offset_top = -120.0
offset_right = 200.0
offset_bottom = 120.0
theme_override_constants/separation = 20

[node name="Title" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 48
text = "Game Over"
horizontal_alignment = 1

[node name="FinalScore" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 24
text = "Score: 0"
horizontal_alignment = 1

[node name="RetryButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
text = "Try Again"

[node name="MenuButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
text = "Main Menu"
''')
        self._write("scripts/game_over.gd", '''extends Control


func _ready() -> void:
\t$VBox/FinalScore.text = "Score: " + str(GameManager.score)
\t$VBox/RetryButton.pressed.connect(_on_retry)
\t$VBox/MenuButton.pressed.connect(_on_menu)


func _on_retry() -> void:
\tGameManager.reset()
\tGameManager.go_to_scene("res://scenes/game.tscn")


func _on_menu() -> void:
\tGameManager.go_to_scene("res://scenes/main_menu.tscn")
''')

    def _write_pause_menu(self) -> None:
        self._write("scenes/pause_menu.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/pause_menu.gd" id="1"]

[node name="PauseMenu" type="Control"]
visible = false
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
color = Color(0, 0, 0, 0.6)

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -150.0
offset_top = -100.0
offset_right = 150.0
offset_bottom = 100.0
theme_override_constants/separation = 16

[node name="Title" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 36
text = "Paused"
horizontal_alignment = 1

[node name="ResumeButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 44)
text = "Resume"

[node name="MenuButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 44)
text = "Main Menu"
''')
        self._write("scripts/pause_menu.gd", '''extends Control


func _ready() -> void:
\t$VBox/ResumeButton.pressed.connect(_on_resume)
\t$VBox/MenuButton.pressed.connect(_on_menu)
\tprocess_mode = Node.PROCESS_MODE_ALWAYS


func _input(event: InputEvent) -> void:
\tif event.is_action_pressed("pause"):
\t\t_toggle_pause()


func _toggle_pause() -> void:
\tvar paused := not get_tree().paused
\tget_tree().paused = paused
\tvisible = paused
\tGameManager.is_paused = paused


func _on_resume() -> void:
\t_toggle_pause()


func _on_menu() -> void:
\tget_tree().paused = false
\tGameManager.go_to_scene("res://scenes/main_menu.tscn")
''')

    @abstractmethod
    def generate_game_scene(self) -> None:
        ...

    @staticmethod
    def _hex_to_godot_color(hex_str: str) -> str:
        h = hex_str.lstrip("#")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return f"({r:.3f}, {g:.3f}, {b:.3f}, 1)"
