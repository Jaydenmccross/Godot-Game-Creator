"""Base template: shared autoloads, menus, HUD, level management, animation,
input configuration, and multiplayer networking.

All genre templates inherit from this and override generate_game_scenes()
to produce genre-specific multi-level content.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import GameSpec, InputMethod, MultiplayerMode


class BaseTemplate(ABC):
    def __init__(self, spec: GameSpec, project_dir: Path) -> None:
        self.spec = spec
        self.dir = project_dir

    # ── public entry point ──────────────────────────────────────────────

    def generate(self) -> None:
        self._write_game_manager()
        self._write_level_manager()
        self._write_sprite_generator()
        self._write_input_config()
        if self.spec.multiplayer != MultiplayerMode.NONE:
            self._write_network_manager()
        self._write_main_menu()
        self._write_hud()
        self._write_game_over()
        self._write_pause_menu()
        self._write_level_complete()
        self.generate_game_scenes()

    def _write(self, rel_path: str, content: str) -> None:
        p = self.dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    # ── abstract: genre templates implement these ───────────────────────

    @abstractmethod
    def generate_game_scenes(self) -> None:
        """Generate all level scenes and genre-specific assets."""
        ...

    # ── game manager (score, health, state) ─────────────────────────────

    def _write_game_manager(self) -> None:
        self._write("scripts/autoload/game_manager.gd", '''extends Node

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

    # ── level manager (multi-level progression) ─────────────────────────

    def _write_level_manager(self) -> None:
        n = self.spec.level_count
        self._write("scripts/autoload/level_manager.gd", f'''extends Node
## Manages multi-level progression and scene transitions.

signal level_changed(level_index: int)

const LEVEL_SCENES: Array[String] = {self._level_scene_array(n)}
const TOTAL_LEVELS: int = {n}

var current_level: int = 0


func reset() -> void:
\tcurrent_level = 0


func get_current_scene() -> String:
\treturn LEVEL_SCENES[current_level]


func advance_level() -> void:
\tcurrent_level += 1
\tif current_level >= TOTAL_LEVELS:
\t\t# Game complete — show game over with victory
\t\tGameManager.go_to_scene("res://scenes/game_over.tscn")
\telse:
\t\tlevel_changed.emit(current_level)
\t\tGameManager.go_to_scene("res://scenes/level_complete.tscn")


func go_to_current_level() -> void:
\tGameManager.go_to_scene(get_current_scene())


func restart_level() -> void:
\tGameManager.go_to_scene(get_current_scene())
''')

    def _level_scene_array(self, n: int) -> str:
        paths = [f'"res://scenes/level_{i+1}.tscn"' for i in range(n)]
        return "[" + ", ".join(paths) + "]"

    # ── procedural sprite animation generator ───────────────────────────

    def _write_sprite_generator(self) -> None:
        self._write("scripts/autoload/sprite_generator.gd", '''extends Node
## Procedurally generates multi-directional animated sprites at runtime.
## Creates proper animation frames for idle, run, jump, fall, attack
## in all relevant directions so characters look natural.

const FRAME_SIZE := Vector2i(32, 48)
const TOPDOWN_SIZE := Vector2i(32, 32)


func create_platformer_frames(body_color: Color, detail_color: Color) -> SpriteFrames:
\t"""Create a full set of platformer character animations."""
\tvar sf := SpriteFrames.new()
\tsf.remove_animation("default")

\tvar anims := {
\t\t"idle_right": {&"frames": 4, &"speed": 4.0, &"loop": true},
\t\t"idle_left": {&"frames": 4, &"speed": 4.0, &"loop": true},
\t\t"run_right": {&"frames": 6, &"speed": 10.0, &"loop": true},
\t\t"run_left": {&"frames": 6, &"speed": 10.0, &"loop": true},
\t\t"jump_right": {&"frames": 2, &"speed": 4.0, &"loop": false},
\t\t"jump_left": {&"frames": 2, &"speed": 4.0, &"loop": false},
\t\t"fall_right": {&"frames": 2, &"speed": 4.0, &"loop": false},
\t\t"fall_left": {&"frames": 2, &"speed": 4.0, &"loop": false},
\t\t"attack_right": {&"frames": 3, &"speed": 12.0, &"loop": false},
\t\t"attack_left": {&"frames": 3, &"speed": 12.0, &"loop": false},
\t}

\tfor anim_name in anims:
\t\tvar info: Dictionary = anims[anim_name]
\t\tsf.add_animation(anim_name)
\t\tsf.set_animation_speed(anim_name, info[&"speed"])
\t\tsf.set_animation_loop(anim_name, info[&"loop"])
\t\tvar facing_left: bool = anim_name.ends_with("_left")
\t\tvar base_name: String = anim_name.replace("_left", "_right") if facing_left else anim_name
\t\tfor i in info[&"frames"]:
\t\t\tvar img := Image.create(FRAME_SIZE.x, FRAME_SIZE.y, false, Image.FORMAT_RGBA8)
\t\t\t_draw_platformer_frame(img, body_color, detail_color, base_name, i, facing_left)
\t\t\tsf.add_frame(anim_name, ImageTexture.create_from_image(img))
\treturn sf


func create_topdown_frames(body_color: Color, detail_color: Color) -> SpriteFrames:
\t"""Create 4-directional animations for top-down characters."""
\tvar sf := SpriteFrames.new()
\tsf.remove_animation("default")

\tvar dirs := ["down", "up", "left", "right"]
\tvar actions := ["idle", "walk", "attack"]
\tfor action in actions:
\t\tfor dir in dirs:
\t\t\tvar anim_name: String = action + "_" + dir
\t\t\tsf.add_animation(anim_name)
\t\t\tvar frame_count: int = 4 if action == "walk" else (3 if action == "attack" else 2)
\t\t\tvar speed: float = 8.0 if action == "walk" else (12.0 if action == "attack" else 3.0)
\t\t\tsf.set_animation_speed(anim_name, speed)
\t\t\tsf.set_animation_loop(anim_name, action != "attack")
\t\t\tfor i in frame_count:
\t\t\t\tvar img := Image.create(TOPDOWN_SIZE.x, TOPDOWN_SIZE.y, false, Image.FORMAT_RGBA8)
\t\t\t\t_draw_topdown_frame(img, body_color, detail_color, action, dir, i)
\t\t\t\tsf.add_frame(anim_name, ImageTexture.create_from_image(img))
\treturn sf


func _draw_platformer_frame(img: Image, body: Color, detail: Color, anim: String, frame: int, flip: bool) -> void:
\tvar w := img.get_width()
\tvar h := img.get_height()
\tvar cx := w / 2
\t# Head
\tfor y in range(4, 16):
\t\tfor x in range(cx - 6, cx + 6):
\t\t\timg.set_pixel(x, y, body)
\t# Eyes
\tvar eye_x: int = cx + 2 if not flip else cx - 4
\timg.set_pixel(eye_x, 8, Color.WHITE)
\timg.set_pixel(eye_x + 1, 8, Color.WHITE)
\t# Body
\tvar body_offset := 0
\tif anim.begins_with("run"):
\t\tbody_offset = int(sin(frame * 1.2) * 1.5)
\tfor y in range(16, 34 + body_offset):
\t\tfor x in range(cx - 5, cx + 5):
\t\t\timg.set_pixel(x, y, body.darkened(0.15))
\t# Legs — different poses per animation
\tif anim.begins_with("idle"):
\t\t_draw_legs_standing(img, cx, 34, detail, frame)
\telif anim.begins_with("run"):
\t\t_draw_legs_running(img, cx, 34, detail, frame, flip)
\telif anim.begins_with("jump"):
\t\t_draw_legs_jump(img, cx, 34, detail, frame)
\telif anim.begins_with("fall"):
\t\t_draw_legs_fall(img, cx, 34, detail, frame)
\telif anim.begins_with("attack"):
\t\t_draw_legs_standing(img, cx, 34, detail, 0)
\t\t_draw_attack_arm(img, cx, 20, detail, frame, flip)
\tif flip:
\t\timg.flip_x()


func _draw_legs_standing(img: Image, cx: int, y: int, color: Color, frame: int) -> void:
\tvar spread: int = 1 if frame % 2 == 0 else 2
\tfor ly in range(y, y + 12):
\t\timg.set_pixel(cx - 3 - spread, ly, color)
\t\timg.set_pixel(cx - 2 - spread, ly, color)
\t\timg.set_pixel(cx + 1 + spread, ly, color)
\t\timg.set_pixel(cx + 2 + spread, ly, color)


func _draw_legs_running(img: Image, cx: int, y: int, color: Color, frame: int, _flip: bool) -> void:
\tvar phase := frame % 6
\tvar offsets := [[-4, 3], [-2, 5], [0, 4], [3, -4], [5, -2], [4, 0]]
\tvar off: Array = offsets[phase]
\tfor ly in range(y, y + 12):
\t\tvar progress := float(ly - y) / 12.0
\t\tvar lx1 := cx - 3 + int(off[0] * progress)
\t\tvar lx2 := cx + 1 + int(off[1] * progress)
\t\tfor dx in range(2):
\t\t\tif lx1 + dx >= 0 and lx1 + dx < img.get_width():
\t\t\t\timg.set_pixel(lx1 + dx, ly, color)
\t\t\tif lx2 + dx >= 0 and lx2 + dx < img.get_width():
\t\t\t\timg.set_pixel(lx2 + dx, ly, color)


func _draw_legs_jump(img: Image, cx: int, y: int, color: Color, frame: int) -> void:
\tvar tuck: int = 2 if frame == 0 else 0
\tfor ly in range(y, y + 10 - tuck):
\t\timg.set_pixel(cx - 4, ly, color)
\t\timg.set_pixel(cx - 3, ly, color)
\t\timg.set_pixel(cx + 2, ly, color)
\t\timg.set_pixel(cx + 3, ly, color)


func _draw_legs_fall(img: Image, cx: int, y: int, color: Color, frame: int) -> void:
\tvar spread := 3 + frame
\tfor ly in range(y, y + 11):
\t\tvar lx := cx - 3 - int(spread * float(ly - y) / 11.0)
\t\tvar rx := cx + 2 + int(spread * float(ly - y) / 11.0)
\t\tif lx >= 0 and lx + 1 < img.get_width():
\t\t\timg.set_pixel(lx, ly, color)
\t\t\timg.set_pixel(lx + 1, ly, color)
\t\tif rx >= 0 and rx + 1 < img.get_width():
\t\t\timg.set_pixel(rx, ly, color)
\t\t\timg.set_pixel(rx + 1, ly, color)


func _draw_attack_arm(img: Image, cx: int, y: int, color: Color, frame: int, flip: bool) -> void:
\tvar arm_lengths: Array[int] = [4, 10, 7]
\tvar arm_offsets: Array[int] = [-2, -4, 0]
\tvar arm_len: int = arm_lengths[frame]
\tvar arm_y: int = y + arm_offsets[frame]
\tvar dir_x: int = 1 if not flip else -1
\tfor i in range(arm_len):
\t\tvar px := cx + 5 * dir_x + i * dir_x
\t\tif px >= 0 and px < img.get_width() and arm_y >= 0 and arm_y < img.get_height():
\t\t\timg.set_pixel(px, arm_y, color)
\t\t\tif arm_y + 1 < img.get_height():
\t\t\t\timg.set_pixel(px, arm_y + 1, color.lightened(0.3))


func _draw_topdown_frame(img: Image, body: Color, detail: Color, action: String, dir: String, frame: int) -> void:
\tvar w := img.get_width()
\tvar h := img.get_height()
\tvar cx := w / 2
\tvar cy := h / 2
\t# Body circle
\tfor y in range(h):
\t\tfor x in range(w):
\t\t\tvar dist := Vector2(x - cx, y - cy).length()
\t\t\tif dist < 10:
\t\t\t\timg.set_pixel(x, y, body if dist < 8 else body.darkened(0.3))
\t# Direction indicator (eyes or facing)
\tvar eye_offset := Vector2i.ZERO
\tmatch dir:
\t\t"down": eye_offset = Vector2i(0, 3)
\t\t"up": eye_offset = Vector2i(0, -3)
\t\t"left": eye_offset = Vector2i(-3, 0)
\t\t"right": eye_offset = Vector2i(3, 0)
\timg.set_pixel(cx + eye_offset.x - 1, cy + eye_offset.y, Color.WHITE)
\timg.set_pixel(cx + eye_offset.x + 1, cy + eye_offset.y, Color.WHITE)
\t# Walk bob
\tif action == "walk":
\t\tvar bob_y := int(sin(frame * 1.8) * 1.5)
\t\tfor x in range(cx - 3, cx + 3):
\t\t\tif cy + 10 + bob_y < h:
\t\t\t\timg.set_pixel(x, cy + 10 + bob_y, detail)
\t# Attack — weapon swing
\tif action == "attack":
\t\tvar arm_dir := eye_offset * 2
\t\tvar swing := frame * 3
\t\tfor i in range(6 + swing):
\t\t\tvar px := cx + arm_dir.x + (arm_dir.x * i / 3)
\t\t\tvar py := cy + arm_dir.y + (arm_dir.y * i / 3)
\t\t\tif px >= 0 and px < w and py >= 0 and py < h:
\t\t\t\timg.set_pixel(px, py, detail)
''')

    # ── input configuration ─────────────────────────────────────────────

    def _write_input_config(self) -> None:
        controller = self.spec.input_method in (InputMethod.CONTROLLER, InputMethod.BOTH)
        keyboard = self.spec.input_method in (InputMethod.KEYBOARD, InputMethod.BOTH)
        self._write("scripts/autoload/input_config.gd", f'''extends Node
## Runtime input configuration — adds controller / keyboard mappings.

const USE_KEYBOARD: bool = {"true" if keyboard else "false"}
const USE_CONTROLLER: bool = {"true" if controller else "false"}


func _ready() -> void:
\tif USE_CONTROLLER:
\t\t_add_joypad_mappings()


func _add_joypad_mappings() -> void:
\t# Left stick → movement
\tvar axes := {{
\t\t"move_left":  [JOY_AXIS_LEFT_X, -1.0],
\t\t"move_right": [JOY_AXIS_LEFT_X,  1.0],
\t\t"move_up":    [JOY_AXIS_LEFT_Y, -1.0],
\t\t"move_down":  [JOY_AXIS_LEFT_Y,  1.0],
\t}}
\tfor action_name in axes:
\t\tvar axis_info: Array = axes[action_name]
\t\tvar ev := InputEventJoypadMotion.new()
\t\tev.axis = axis_info[0]
\t\tev.axis_value = axis_info[1]
\t\tInputMap.action_add_event(action_name, ev)

\t# D-pad
\tvar dpads := {{
\t\t"move_up": JOY_BUTTON_DPAD_UP,
\t\t"move_down": JOY_BUTTON_DPAD_DOWN,
\t\t"move_left": JOY_BUTTON_DPAD_LEFT,
\t\t"move_right": JOY_BUTTON_DPAD_RIGHT,
\t}}
\tfor action_name in dpads:
\t\tvar ev := InputEventJoypadButton.new()
\t\tev.button_index = dpads[action_name]
\t\tInputMap.action_add_event(action_name, ev)

\t# A = jump, X = action, B = secondary, Start = pause
\tvar buttons := {{
\t\t"jump": JOY_BUTTON_A,
\t\t"action": JOY_BUTTON_X,
\t\t"pause": JOY_BUTTON_START,
\t}}
\tfor action_name in buttons:
\t\tvar ev := InputEventJoypadButton.new()
\t\tev.button_index = buttons[action_name]
\t\tInputMap.action_add_event(action_name, ev)
''')

    # ── network manager (multiplayer) ───────────────────────────────────

    def _write_network_manager(self) -> None:
        mode = self.spec.multiplayer
        self._write("scripts/autoload/network_manager.gd", f'''extends Node
## Multiplayer networking using Godot's high-level ENet multiplayer.

signal player_connected(peer_id: int)
signal player_disconnected(peer_id: int)
signal connection_succeeded
signal connection_failed

const DEFAULT_PORT: int = 28960
const MAX_PLAYERS: int = 8
const MODE: String = "{mode.value}"

var players: Dictionary = {{}}
var my_info: Dictionary = {{"name": "Player"}}

var peer: ENetMultiplayerPeer = null


func host_game(port: int = DEFAULT_PORT) -> Error:
\tpeer = ENetMultiplayerPeer.new()
\tvar err := peer.create_server(port, MAX_PLAYERS)
\tif err != OK:
\t\treturn err
\tmultiplayer.multiplayer_peer = peer
\tmultiplayer.peer_connected.connect(_on_peer_connected)
\tmultiplayer.peer_disconnected.connect(_on_peer_disconnected)
\tplayers[1] = my_info
\tprint("Hosting on port ", port)
\treturn OK


func join_game(address: String, port: int = DEFAULT_PORT) -> Error:
\tpeer = ENetMultiplayerPeer.new()
\tvar err := peer.create_client(address, port)
\tif err != OK:
\t\treturn err
\tmultiplayer.multiplayer_peer = peer
\tmultiplayer.peer_connected.connect(_on_peer_connected)
\tmultiplayer.peer_disconnected.connect(_on_peer_disconnected)
\tmultiplayer.connected_to_server.connect(_on_connected)
\tmultiplayer.connection_failed.connect(_on_connection_failed)
\treturn OK


func disconnect_game() -> void:
\tif peer:
\t\tpeer.close()
\t\tpeer = null
\t\tmultiplayer.multiplayer_peer = null
\tplayers.clear()


func is_host() -> bool:
\treturn multiplayer.is_server() if multiplayer.multiplayer_peer else false


func _on_peer_connected(id: int) -> void:
\tplayers[id] = {{"name": "Player " + str(id)}}
\tplayer_connected.emit(id)
\tprint("Player connected: ", id)


func _on_peer_disconnected(id: int) -> void:
\tplayers.erase(id)
\tplayer_disconnected.emit(id)


func _on_connected() -> void:
\tplayers[multiplayer.get_unique_id()] = my_info
\tconnection_succeeded.emit()


func _on_connection_failed() -> void:
\tconnection_failed.emit()
''')

    # ── main menu (with multiplayer lobby) ──────────────────────────────

    def _write_main_menu(self) -> None:
        spec = self.spec
        has_mp = spec.multiplayer != MultiplayerMode.NONE

        mp_buttons = ""
        if has_mp:
            mp_buttons = """
[node name="Spacer2" type="Control" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 10)

[node name="HostButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 20
text = "Host Game"

[node name="JoinButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 20
text = "Join Game"

[node name="IPInput" type="LineEdit" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 40)
placeholder_text = "Enter IP address..."
alignment = 1
"""

        mp_script = ""
        if has_mp:
            mp_script = '''
\t$VBox/HostButton.pressed.connect(_on_host)
\t$VBox/JoinButton.pressed.connect(_on_join)
\tNetworkManager.connection_succeeded.connect(_on_connected)
\tNetworkManager.connection_failed.connect(_on_connect_failed)


func _on_host() -> void:
\tvar err := NetworkManager.host_game()
\tif err == OK:
\t\tLevelManager.reset()
\t\tGameManager.reset()
\t\tLevelManager.go_to_current_level()


func _on_join() -> void:
\tvar ip := $VBox/IPInput.text.strip_edges()
\tif ip.is_empty():
\t\tip = "127.0.0.1"
\tNetworkManager.join_game(ip)


func _on_connected() -> void:
\tLevelManager.reset()
\tGameManager.reset()
\tLevelManager.go_to_current_level()


func _on_connect_failed() -> void:
\tprint("Connection failed")
'''

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
offset_top = -200.0
offset_right = 200.0
offset_bottom = 200.0
grow_horizontal = 2
grow_vertical = 2
theme_override_constants/separation = 16

[node name="Title" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 48
text = "{spec.name}"
horizontal_alignment = 1

[node name="Subtitle" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 16
text = "A {spec.theme.title()} {spec.genre.value.replace('_', ' ').title()}"
horizontal_alignment = 1
modulate = Color(0.7, 0.7, 0.7, 1)

[node name="Spacer" type="Control" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 20)

[node name="PlayButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 22
text = "Play Game"
{mp_buttons}
[node name="QuitButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 20
text = "Quit"
''')
        self._write("scripts/main_menu.gd", f'''extends Control


func _ready() -> void:
\t$VBox/PlayButton.pressed.connect(_on_play)
\t$VBox/QuitButton.pressed.connect(_on_quit)
\tGameManager.reset()
\tLevelManager.reset()
{mp_script}

func _on_play() -> void:
\tLevelManager.go_to_current_level()


func _on_quit() -> void:
\tget_tree().quit()
''')

    # ── HUD ─────────────────────────────────────────────────────────────

    def _write_hud(self) -> None:
        self._write("scenes/hud.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/hud.gd" id="1"]

[node name="HUD" type="CanvasLayer"]
script = ExtResource("1")

[node name="TopBar" type="HBoxContainer" parent="."]
anchors_preset = 10
anchor_right = 1.0
offset_left = 10.0
offset_bottom = 40.0
theme_override_constants/separation = 30

[node name="ScoreLabel" type="Label" parent="TopBar"]
layout_mode = 2
theme_override_font_sizes/font_size = 22
text = "Score: 0"

[node name="HealthLabel" type="Label" parent="TopBar"]
layout_mode = 2
theme_override_font_sizes/font_size = 22
text = "Health: 100"

[node name="HealthBar" type="ProgressBar" parent="TopBar"]
layout_mode = 2
custom_minimum_size = Vector2(180, 0)
size_flags_vertical = 4
max_value = 100.0
value = 100.0
show_percentage = false

[node name="LevelLabel" type="Label" parent="TopBar"]
layout_mode = 2
theme_override_font_sizes/font_size = 22
text = "Level: 1"
''')
        self._write("scripts/hud.gd", '''extends CanvasLayer


func _ready() -> void:
\tGameManager.score_changed.connect(_on_score_changed)
\tGameManager.health_changed.connect(_on_health_changed)
\tLevelManager.level_changed.connect(_on_level_changed)
\t_on_score_changed(GameManager.score)
\t_on_health_changed(GameManager.health)
\t_on_level_changed(LevelManager.current_level)


func _on_score_changed(new_score: int) -> void:
\t$TopBar/ScoreLabel.text = "Score: " + str(new_score)


func _on_health_changed(new_health: int) -> void:
\t$TopBar/HealthLabel.text = "Health: " + str(new_health)
\t$TopBar/HealthBar.value = new_health


func _on_level_changed(level_idx: int) -> void:
\t$TopBar/LevelLabel.text = "Level: " + str(level_idx + 1)
''')

    # ── game over ───────────────────────────────────────────────────────

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
\tvar completed := LevelManager.current_level >= LevelManager.TOTAL_LEVELS
\tif completed:
\t\t$VBox/Title.text = "Victory!"
\t\t$VBox/RetryButton.text = "Play Again"
\t$VBox/FinalScore.text = "Final Score: " + str(GameManager.score)
\t$VBox/RetryButton.pressed.connect(_on_retry)
\t$VBox/MenuButton.pressed.connect(_on_menu)


func _on_retry() -> void:
\tGameManager.reset()
\tLevelManager.reset()
\tLevelManager.go_to_current_level()


func _on_menu() -> void:
\tGameManager.go_to_scene("res://scenes/main_menu.tscn")
''')

    # ── pause menu ──────────────────────────────────────────────────────

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

[node name="RestartButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 44)
text = "Restart Level"

[node name="MenuButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 44)
text = "Main Menu"
''')
        self._write("scripts/pause_menu.gd", '''extends Control


func _ready() -> void:
\t$VBox/ResumeButton.pressed.connect(_on_resume)
\t$VBox/RestartButton.pressed.connect(_on_restart)
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


func _on_restart() -> void:
\tget_tree().paused = false
\tLevelManager.restart_level()


func _on_menu() -> void:
\tget_tree().paused = false
\tGameManager.go_to_scene("res://scenes/main_menu.tscn")
''')

    # ── level complete screen ───────────────────────────────────────────

    def _write_level_complete(self) -> None:
        self._write("scenes/level_complete.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/level_complete.gd" id="1"]

[node name="LevelComplete" type="Control"]
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
color = Color(0.02, 0.05, 0.15, 0.92)

[node name="VBox" type="VBoxContainer" parent="."]
layout_mode = 1
anchors_preset = 8
anchor_left = 0.5
anchor_top = 0.5
anchor_right = 0.5
anchor_bottom = 0.5
offset_left = -200.0
offset_top = -100.0
offset_right = 200.0
offset_bottom = 100.0
theme_override_constants/separation = 20

[node name="Title" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 42
text = "Level Complete!"
horizontal_alignment = 1

[node name="ScoreLabel" type="Label" parent="VBox"]
layout_mode = 2
theme_override_font_sizes/font_size = 22
text = "Score: 0"
horizontal_alignment = 1

[node name="NextButton" type="Button" parent="VBox"]
layout_mode = 2
custom_minimum_size = Vector2(0, 50)
theme_override_font_sizes/font_size = 20
text = "Next Level"
''')
        self._write("scripts/level_complete.gd", '''extends Control


func _ready() -> void:
\t$VBox/ScoreLabel.text = "Score: " + str(GameManager.score)
\t$VBox/NextButton.pressed.connect(_on_next)


func _on_next() -> void:
\tLevelManager.go_to_current_level()
''')

    # ── utility ─────────────────────────────────────────────────────────

    @staticmethod
    def _hex_to_godot_color(hex_str: str) -> str:
        h = hex_str.lstrip("#")
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return f"({r:.3f}, {g:.3f}, {b:.3f}, 1)"
