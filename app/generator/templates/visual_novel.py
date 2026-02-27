"""Visual Novel — multi-level story chapters with dialogue and choices.

Each level is a distinct story chapter:
- Level 1: Introduction — meet the world and characters
- Level 2: Rising action — conflict and choices
- Level 3+: Climax and resolution — deeper branching, higher stakes
"""

from __future__ import annotations

from app.generator.templates.base import BaseTemplate


class VisualNovelTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_dialogue_script()
        for i in range(self.spec.level_count):
            self._write_level(i + 1)

    # ── dialogue system script ───────────────────────────────────────────

    def _write_dialogue_script(self) -> None:
        self._write("scripts/dialogue_system.gd", '''extends Control
## Visual novel dialogue system with branching choices.

var story: Array[Dictionary] = []
var current_index: int = 0

@onready var speaker_label: Label = $DialogueBox/VBox/SpeakerLabel
@onready var text_label: RichTextLabel = $DialogueBox/VBox/TextLabel
@onready var choices_box: VBoxContainer = $DialogueBox/VBox/ChoicesBox
@onready var continue_hint: Label = $DialogueBox/VBox/ContinueHint


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)
\t_show_current()


func _input(event: InputEvent) -> void:
\tif event.is_action_pressed("action") and choices_box.get_child_count() == 0:
\t\t_advance()


func _show_current() -> void:
\tif current_index >= story.size():
\t\tLevelManager.advance_level()
\t\treturn

\tvar entry: Dictionary = story[current_index]
\tvar speaker: String = entry.get("speaker", "")

\tif speaker == "END":
\t\tLevelManager.advance_level()
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


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

    # ── level generation (chapters) ──────────────────────────────────────

    def _write_level(self, level_num: int) -> None:
        bg = self._hex_to_godot_color(self.spec.color_bg)
        primary = self._hex_to_godot_color(self.spec.color_primary)
        secondary = self._hex_to_godot_color(self.spec.color_secondary)
        accent = self._hex_to_godot_color(self.spec.color_accent)

        theme = self.spec.theme.title()
        player = self.spec.player_name

        story_data = self._build_chapter_story(level_num, theme, player)

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/dialogue_system.gd" id="1"]
[ext_resource type="Script" path="res://scripts/chapter_{level_num}_data.gd" id="data"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Game" type="Control"]
layout_mode = 3
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
script = ExtResource("data")

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

[node name="ChapterTitle" type="Label" parent="."]
layout_mode = 1
anchors_preset = 5
anchor_left = 0.5
anchor_right = 0.5
offset_left = -200.0
offset_top = 20.0
offset_right = 200.0
offset_bottom = 60.0
theme_override_font_sizes/font_size = 28
text = "Chapter {level_num}"
horizontal_alignment = 1
modulate = Color{accent}

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
text = "..."
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

        self._write(f"scripts/chapter_{level_num}_data.gd", f'''extends "res://scripts/dialogue_system.gd"
## Chapter {level_num} story data for the {theme.lower()} visual novel.


func _ready() -> void:
\tstory = {story_data}
\tsuper._ready()
''')

        self._write("scripts/game_level.gd", '''extends Node2D


func _ready() -> void:
\tGameManager.game_over.connect(_on_game_over)


func _on_game_over() -> void:
\tGameManager.go_to_scene("res://scenes/game_over.tscn")
''')

    def _build_chapter_story(self, level_num: int, theme: str, player: str) -> str:
        if level_num == 1:
            return f'''[
\t{{"speaker": "Narrator", "text": "In a world of {theme.lower()}, a new adventure begins..."}},
\t{{"speaker": "Narrator", "text": "You are {player}, and today your journey starts."}},
\t{{"speaker": "{player}", "text": "Where am I? This place looks... incredible."}},
\t{{"speaker": "Narrator", "text": "A mysterious figure appears before you."}},
\t{{"speaker": "Guide", "text": "Welcome, {player}. I have been waiting for you."}},
\t{{"speaker": "Narrator", "text": "The guide offers two paths. Which will you choose?"}},
\t{{
\t\t"speaker": "Choice",
\t\t"choices": [
\t\t\t{{"text": "Take the bright path", "next": 7}},
\t\t\t{{"text": "Take the shadowed path", "next": 10}},
\t\t],
\t}},
\t{{"speaker": "{player}", "text": "The bright path feels warm and welcoming."}},
\t{{"speaker": "Guide", "text": "A wise choice. The light will guide you well."}},
\t{{"speaker": "Narrator", "text": "Chapter 1 complete. Score +50!", "score": 50, "next": 13}},
\t{{"speaker": "{player}", "text": "The shadowed path is eerie, but I feel drawn to it."}},
\t{{"speaker": "Guide", "text": "Bold indeed. Not many dare walk the shadows."}},
\t{{"speaker": "Narrator", "text": "You found a hidden treasure! Score +100!", "score": 100, "next": 13}},
\t{{"speaker": "Narrator", "text": "And so, {player}'s first chapter comes to a close."}},
\t{{"speaker": "END", "text": ""}},
]'''
        elif level_num == 2:
            return f'''[
\t{{"speaker": "Narrator", "text": "Chapter 2 — The {theme.lower()} world grows darker..."}},
\t{{"speaker": "{player}", "text": "Something has changed. The air feels heavy."}},
\t{{"speaker": "Guide", "text": "{player}, a great challenge lies ahead."}},
\t{{"speaker": "Narrator", "text": "A fork in the road presents itself once more."}},
\t{{
\t\t"speaker": "Choice",
\t\t"choices": [
\t\t\t{{"text": "Stand and fight", "next": 5}},
\t\t\t{{"text": "Seek allies first", "next": 8}},
\t\t],
\t}},
\t{{"speaker": "{player}", "text": "I will face whatever comes!"}},
\t{{"speaker": "Narrator", "text": "Your bravery inspires those around you. Score +75!", "score": 75}},
\t{{"speaker": "Narrator", "text": "The battle is won, but at a cost.", "next": 11}},
\t{{"speaker": "{player}", "text": "Let me find companions for this journey."}},
\t{{"speaker": "Narrator", "text": "You gather a loyal party. Score +60!", "score": 60}},
\t{{"speaker": "Guide", "text": "Together you are stronger. Well done.", "next": 11}},
\t{{"speaker": "Narrator", "text": "{player}'s second chapter draws to a close."}},
\t{{"speaker": "END", "text": ""}},
]'''
        else:
            return f'''[
\t{{"speaker": "Narrator", "text": "Chapter {level_num} — The {theme.lower()} saga continues..."}},
\t{{"speaker": "{player}", "text": "I have come so far. What awaits me now?"}},
\t{{"speaker": "Guide", "text": "The final trial of this chapter awaits, {player}."}},
\t{{"speaker": "Narrator", "text": "Before you stands a great door with two symbols."}},
\t{{
\t\t"speaker": "Choice",
\t\t"choices": [
\t\t\t{{"text": "Touch the sun symbol", "next": 5}},
\t\t\t{{"text": "Touch the moon symbol", "next": 8}},
\t\t],
\t}},
\t{{"speaker": "Narrator", "text": "Warmth floods through you as golden light fills the room."}},
\t{{"speaker": "{player}", "text": "The power of the sun... it is incredible!"}},
\t{{"speaker": "Narrator", "text": "You gained the Sun's Blessing! Score +{50 * level_num}!", "score": {50 * level_num}, "next": 11}},
\t{{"speaker": "Narrator", "text": "Silver moonlight bathes the chamber in calm."}},
\t{{"speaker": "{player}", "text": "The moon grants clarity and wisdom."}},
\t{{"speaker": "Narrator", "text": "You gained the Moon's Insight! Score +{40 * level_num}!", "score": {40 * level_num}, "next": 11}},
\t{{"speaker": "Narrator", "text": "Chapter {level_num} is complete. Your story grows ever deeper."}},
\t{{"speaker": "END", "text": ""}},
]'''
