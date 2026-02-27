"""Visual Novel template — dialogue system with choices and branching."""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class VisualNovelTemplate(BaseTemplate):

    def generate_game_scene(self) -> None:
        self._write_game_scene()
        self._write_dialogue_system()

    def _write_game_scene(self) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        primary = self._hex_to_godot_color(self.spec.color_primary)
        self._write("scenes/game.tscn", f'''[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/game_level.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Game" type="Control"]
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
color = Color{bg}

[node name="CharacterSprite" type="ColorRect" parent="."]
layout_mode = 1
anchors_preset = 7
anchor_left = 0.5
anchor_top = 1.0
anchor_right = 0.5
anchor_bottom = 1.0
offset_left = -60.0
offset_top = -360.0
offset_right = 60.0
offset_bottom = -80.0
color = Color{primary}

[node name="DialogueBox" type="PanelContainer" parent="."]
layout_mode = 1
anchors_preset = 12
anchor_top = 1.0
anchor_right = 1.0
anchor_bottom = 1.0
offset_left = 40.0
offset_top = -200.0
offset_right = -40.0
offset_bottom = -20.0

[node name="VBox" type="VBoxContainer" parent="DialogueBox"]
layout_mode = 2
theme_override_constants/separation = 10

[node name="SpeakerLabel" type="Label" parent="DialogueBox/VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 20
text = "Narrator"

[node name="TextLabel" type="RichTextLabel" parent="DialogueBox/VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 80)
theme_override_font_sizes/normal_font_size = 18
text = "Welcome to the story..."
scroll_active = false

[node name="ChoicesBox" type="VBoxContainer" parent="DialogueBox/VBox"]
layout_mode = 2
theme_override_constants/separation = 8

[node name="ContinueHint" type="Label" parent="DialogueBox/VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 14
text = "Click or press Action to continue"
horizontal_alignment = 2
modulate = Color(0.6, 0.6, 0.6, 1)

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')

    def _write_dialogue_system(self) -> None:
        theme = self.spec.theme.title()
        player = self.spec.player_name
        self._write("scripts/game_level.gd", f'''extends Control
## Visual novel dialogue system with branching choices.

var story: Array[Dictionary] = [
\t{{"speaker": "Narrator", "text": "In a world of {theme.lower()}, a new adventure begins..."}},
\t{{"speaker": "Narrator", "text": "You are {player}, and today your journey starts."}},
\t{{"speaker": "{player}", "text": "Where am I? This place looks... incredible."}},
\t{{"speaker": "Narrator", "text": "Before you lies two paths. Which will you choose?"}},
\t{{
\t\t"speaker": "Choice",
\t\t"choices": [
\t\t\t{{"text": "Take the bright path", "next": 5}},
\t\t\t{{"text": "Take the dark path", "next": 8}},
\t\t],
\t}},
\t{{"speaker": "{player}", "text": "The bright path feels warm and welcoming."}},
\t{{"speaker": "Narrator", "text": "You chose wisely. The light guides your way forward."}},
\t{{"speaker": "Narrator", "text": "Your adventure continues... Score +50!", "score": 50, "next": 11}},
\t{{"speaker": "{player}", "text": "The dark path is eerie, but I feel drawn to it."}},
\t{{"speaker": "Narrator", "text": "Shadows dance around you, but you press on bravely."}},
\t{{"speaker": "Narrator", "text": "You discovered a hidden treasure! Score +100!", "score": 100, "next": 11}},
\t{{"speaker": "Narrator", "text": "And so, {player}'s first chapter comes to a close."}},
\t{{"speaker": "Narrator", "text": "Thank you for playing! Your story has just begun."}},
\t{{"speaker": "END", "text": ""}},
]

var current_index: int = 0

@onready var speaker_label: Label = $DialogueBox/VBox/SpeakerLabel
@onready var text_label: RichTextLabel = $DialogueBox/VBox/TextLabel
@onready var choices_box: VBoxContainer = $DialogueBox/VBox/ChoicesBox
@onready var continue_hint: Label = $DialogueBox/VBox/ContinueHint


func _ready() -> void:
\t_show_current()


func _input(event: InputEvent) -> void:
\tif event.is_action_pressed("action") and choices_box.get_child_count() == 0:
\t\t_advance()


func _show_current() -> void:
\tif current_index >= story.size():
\t\tGameManager.go_to_scene("res://scenes/game_over.tscn")
\t\treturn

\tvar entry: Dictionary = story[current_index]
\tvar speaker: String = entry.get("speaker", "")

\tif speaker == "END":
\t\tGameManager.go_to_scene("res://scenes/game_over.tscn")
\t\treturn

\tif entry.has("score"):
\t\tGameManager.add_score(entry["score"])

\t_clear_choices()

\tif entry.has("choices"):
\t\tspeaker_label.text = "Choose:"
\t\ttext_label.text = ""
\t\tcontinue_hint.visible = false
\t\tfor choice in entry["choices"]:
\t\t\tvar btn := Button.new()
\t\t\tbtn.text = choice["text"]
\t\t\tbtn.custom_minimum_size = Vector2(0, 40)
\t\t\tbtn.pressed.connect(_on_choice.bind(choice["next"]))
\t\t\tchoices_box.add_child(btn)
\telse:
\t\tspeaker_label.text = speaker
\t\ttext_label.text = entry.get("text", "")
\t\tcontinue_hint.visible = true


func _advance() -> void:
\tvar entry: Dictionary = story[current_index]
\tif entry.has("next"):
\t\tcurrent_index = entry["next"]
\telse:
\t\tcurrent_index += 1
\t_show_current()


func _on_choice(target_index: int) -> void:
\tcurrent_index = target_index
\t_show_current()


func _clear_choices() -> void:
\tfor child in choices_box.get_children():
\t\tchild.queue_free()
''')
