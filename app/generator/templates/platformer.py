"""2D Platformer — procedural world generation, multi-biome, polished game feel.

Architecture:
  Each level scene contains a WorldGenerator node that builds the entire level
  at runtime using FastNoiseLite: noise-based terrain, floating platforms,
  scattered decorations (trees, rocks, grass), parallax backgrounds, enemies,
  collectibles, and a level exit. This produces large, varied, organic-feeling
  worlds — not hardcoded rectangles.

  Player has wall-jump, dash, coyote time, variable jump height, attack.
  Three enemy types: Walker, Flyer, Charger.  Boss every 5 levels.
  10 levels across 3 biomes: Forest, Cave, Sky.
"""

from __future__ import annotations
from app.generator.templates.base import BaseTemplate


class PlatformerTemplate(BaseTemplate):

    def generate_game_scenes(self) -> None:
        self._write_world_generator()
        self._write_player()
        self._write_enemy_walker()
        self._write_enemy_flyer()
        self._write_enemy_charger()
        self._write_collectible()
        self._write_level_exit()
        self._write_screen_effects()
        for i in range(self.spec.level_count):
            self._write_level_scene(i + 1)
        self._write("scripts/game_level.gd", '''extends Node2D

func _ready() -> void:
\tGameManager.game_over.connect(func(): GameManager.go_to_scene("res://scenes/game_over.tscn"))
''')

    # ═══════════════════════════════════════════════════════════════════
    #  WORLD GENERATOR — procedural terrain, platforms, decorations
    # ═══════════════════════════════════════════════════════════════════

    def _write_world_generator(self) -> None:
        self._write("scripts/world/world_generator.gd", '''extends Node2D
## Procedural world generator — builds entire level at runtime.

@export var biome: String = "forest"
@export var difficulty: int = 1
@export var level_seed: int = 0
@export var world_width: int = 250
@export var world_height: int = 50

const T := 16  # tile size

var _noise := FastNoiseLite.new()
var _detail_noise := FastNoiseLite.new()
var _heights: Array[float] = []

# Biome palettes
const BIOMES := {
\t"forest": {
\t\t"sky_top": Color(0.15, 0.25, 0.45),
\t\t"sky_bottom": Color(0.35, 0.55, 0.75),
\t\t"ground": Color(0.22, 0.42, 0.18),
\t\t"ground_deep": Color(0.35, 0.25, 0.15),
\t\t"platform": Color(0.45, 0.35, 0.25),
\t\t"foliage": Color(0.2, 0.55, 0.2),
\t\t"foliage_alt": Color(0.3, 0.65, 0.25),
\t\t"trunk": Color(0.35, 0.22, 0.12),
\t\t"accent": Color(0.9, 0.75, 0.1),
\t\t"fog": Color(0.4, 0.55, 0.5, 0.15),
\t\t"particle": Color(0.4, 0.7, 0.3, 0.5),
\t},
\t"cave": {
\t\t"sky_top": Color(0.05, 0.04, 0.08),
\t\t"sky_bottom": Color(0.1, 0.08, 0.15),
\t\t"ground": Color(0.3, 0.28, 0.32),
\t\t"ground_deep": Color(0.2, 0.18, 0.22),
\t\t"platform": Color(0.4, 0.35, 0.38),
\t\t"foliage": Color(0.25, 0.5, 0.55),
\t\t"foliage_alt": Color(0.4, 0.3, 0.6),
\t\t"trunk": Color(0.3, 0.25, 0.3),
\t\t"accent": Color(0.5, 0.3, 0.9),
\t\t"fog": Color(0.15, 0.12, 0.2, 0.25),
\t\t"particle": Color(0.4, 0.3, 0.8, 0.4),
\t},
\t"sky": {
\t\t"sky_top": Color(0.55, 0.7, 0.95),
\t\t"sky_bottom": Color(0.85, 0.9, 1.0),
\t\t"ground": Color(0.75, 0.85, 0.65),
\t\t"ground_deep": Color(0.55, 0.65, 0.5),
\t\t"platform": Color(0.8, 0.85, 0.9),
\t\t"foliage": Color(0.85, 0.6, 0.75),
\t\t"foliage_alt": Color(0.95, 0.8, 0.6),
\t\t"trunk": Color(0.7, 0.6, 0.5),
\t\t"accent": Color(1.0, 0.85, 0.3),
\t\t"fog": Color(0.9, 0.9, 1.0, 0.12),
\t\t"particle": Color(1.0, 1.0, 0.8, 0.4),
\t},
}


func _ready() -> void:
\t_noise.seed = level_seed if level_seed != 0 else randi()
\t_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX
\t_noise.frequency = 0.035
\t_detail_noise.seed = _noise.seed + 42
\t_detail_noise.frequency = 0.12
\t_generate()


func _generate() -> void:
\tvar b: Dictionary = BIOMES.get(biome, BIOMES["forest"])
\t_compute_heights(b)
\t_build_parallax_background(b)
\t_build_terrain(b)
\t_place_platforms(b)
\t_place_decorations(b)
\t_place_enemies()
\t_place_collectibles(b)
\t_place_exit(b)
\t_spawn_player()
\t_add_ambient_particles(b)
\t_add_camera_bounds()


# ── heightmap ──────────────────────────────────────────────────────
func _compute_heights(b: Dictionary) -> void:
\t_heights.clear()
\tfor x in world_width:
\t\tvar base := 0.6 * world_height * T
\t\tvar hill: float = _noise.get_noise_1d(float(x)) * 5.0 * T
\t\tvar detail: float = _detail_noise.get_noise_1d(float(x)) * 2.0 * T
\t\t_heights.append(base + hill + detail)


func _surface_y(world_x: float) -> float:
\tvar idx := clampi(int(world_x / T), 0, _heights.size() - 1)
\treturn _heights[idx]


# ── parallax background ───────────────────────────────────────────
func _build_parallax_background(b: Dictionary) -> void:
\tvar bg := ParallaxBackground.new()
\tbg.name = "ParallaxBG"

\t# sky gradient
\tvar sky_layer := ParallaxLayer.new()
\tsky_layer.motion_scale = Vector2.ZERO
\tvar sky := ColorRect.new()
\tsky.size = Vector2(1400, 800)
\tsky.position = Vector2(-200, -400)
\tsky.color = b["sky_top"]
\tsky_layer.add_child(sky)
\tbg.add_child(sky_layer)

\t# far mountain silhouettes
\tfor i in 3:
\t\tvar ml := ParallaxLayer.new()
\t\tml.motion_scale = Vector2(0.1 + i * 0.12, 0.05)
\t\tml.motion_mirroring = Vector2(1600, 0)
\t\tvar mountain := Polygon2D.new()
\t\tvar pts := PackedVector2Array()
\t\tpts.append(Vector2(0, 600))
\t\tvar n := FastNoiseLite.new()
\t\tn.seed = _noise.seed + 100 + i
\t\tn.frequency = 0.008 + i * 0.005
\t\tfor x in range(0, 1601, 16):
\t\t\tvar h := 200.0 + n.get_noise_1d(float(x)) * (120.0 - i * 25.0)
\t\t\tpts.append(Vector2(x, h + i * 80))
\t\tpts.append(Vector2(1600, 600))
\t\tmountain.polygon = pts
\t\tvar alpha := 0.15 + i * 0.08
\t\tmountain.color = b["sky_bottom"].lerp(b["ground"], 0.2 + i * 0.15)
\t\tmountain.color.a = alpha + 0.3
\t\tml.add_child(mountain)
\t\tbg.add_child(ml)

\tadd_child(bg)
\tmove_child(bg, 0)


# ── terrain ────────────────────────────────────────────────────────
func _build_terrain(b: Dictionary) -> void:
\tvar body := StaticBody2D.new()
\tbody.name = "Terrain"

\t# surface polygon
\tvar pts := PackedVector2Array()
\tvar bottom_y := world_height * T + 200.0
\tpts.append(Vector2(0, bottom_y))
\tfor x in world_width:
\t\tpts.append(Vector2(x * T, _heights[x]))
\tpts.append(Vector2((world_width - 1) * T, bottom_y))
\tvar col := CollisionPolygon2D.new()
\tcol.polygon = pts
\tbody.add_child(col)

\t# visual — surface layer
\tvar surface := Polygon2D.new()
\tsurface.polygon = pts
\tsurface.color = b["ground"]
\tbody.add_child(surface)

\t# grass line on top
\tvar grass := Line2D.new()
\tgrass.width = 4.0
\tgrass.default_color = b["foliage"]
\tfor x in world_width:
\t\tgrass.add_point(Vector2(x * T, _heights[x] - 1))
\tbody.add_child(grass)

\t# deep earth overlay
\tvar deep_pts := PackedVector2Array()
\tdeep_pts.append(Vector2(0, bottom_y))
\tfor x in world_width:
\t\tdeep_pts.append(Vector2(x * T, _heights[x] + 40))
\tdeep_pts.append(Vector2((world_width - 1) * T, bottom_y))
\tvar deep := Polygon2D.new()
\tdeep.polygon = deep_pts
\tdeep.color = b["ground_deep"]
\tbody.add_child(deep)

\tadd_child(body)


# ── floating platforms ─────────────────────────────────────────────
func _place_platforms(b: Dictionary) -> void:
\tvar plat_count := 15 + difficulty * 8
\tvar plat_noise := FastNoiseLite.new()
\tplat_noise.seed = _noise.seed + 200
\tplat_noise.frequency = 0.04
\tfor i in plat_count:
\t\tvar px := randf_range(T * 8, (world_width - 8) * T)
\t\tvar sy := _surface_y(px)
\t\tvar height_above := randf_range(60, 180 + difficulty * 15)
\t\tvar py := sy - height_above
\t\tvar pw := randf_range(48, 160 - difficulty * 5)

\t\tvar plat := StaticBody2D.new()
\t\tplat.position = Vector2(px, py)
\t\tvar shape := RectangleShape2D.new()
\t\tshape.size = Vector2(pw, 10)
\t\tvar cs := CollisionShape2D.new()
\t\tcs.shape = shape
\t\tplat.add_child(cs)

\t\t# organic-looking platform visual
\t\tvar vis := Polygon2D.new()
\t\tvar vpts := PackedVector2Array()
\t\tvar half := pw / 2.0
\t\tvpts.append(Vector2(-half + 4, -5))
\t\tvpts.append(Vector2(-half, 0))
\t\tvpts.append(Vector2(-half + 2, 6))
\t\tfor s in range(8):
\t\t\tvar sx: float = lerp(-half + 2, half - 2, float(s) / 7.0)
\t\t\tvar wobble: float = plat_noise.get_noise_1d(px + s * 20) * 3.0
\t\t\tvpts.append(Vector2(sx, 8 + wobble))
\t\tvpts.append(Vector2(half - 2, 6))
\t\tvpts.append(Vector2(half, 0))
\t\tvpts.append(Vector2(half - 4, -5))
\t\tvis.polygon = vpts
\t\tvis.color = b["platform"]
\t\tplat.add_child(vis)

\t\t# moss/grass detail on top
\t\tvar moss := Line2D.new()
\t\tmoss.width = 3.0
\t\tmoss.default_color = b["foliage"].lerp(b["platform"], 0.4)
\t\tfor s in range(6):
\t\t\tmoss.add_point(Vector2(lerp(-half + 6, half - 6, float(s) / 5.0), -5))
\t\tplat.add_child(moss)

\t\tadd_child(plat)


# ── decorations ────────────────────────────────────────────────────
func _place_decorations(b: Dictionary) -> void:
\tvar deco_group := Node2D.new()
\tdeco_group.name = "Decorations"

\tfor x_tile in range(2, world_width - 2):
\t\tvar wx := float(x_tile) * T
\t\tvar sy := _surface_y(wx)
\t\tvar r: float = _detail_noise.get_noise_2d(float(x_tile), 0.0)

\t\t# Trees
\t\tif r > 0.25 and x_tile % 3 == 0:
\t\t\t_make_tree(deco_group, Vector2(wx, sy), b)
\t\t# Rocks
\t\telif r < -0.3 and x_tile % 5 == 0:
\t\t\t_make_rock(deco_group, Vector2(wx, sy), b)
\t\t# Grass tufts
\t\telif abs(r) < 0.2:
\t\t\t_make_grass(deco_group, Vector2(wx, sy), b)
\t\t# Flowers (forest/sky only)
\t\telif biome != "cave" and r > 0.15 and x_tile % 4 == 0:
\t\t\t_make_flower(deco_group, Vector2(wx, sy), b)

\tadd_child(deco_group)


func _make_tree(parent: Node2D, pos: Vector2, b: Dictionary) -> void:
\tvar tree := Node2D.new()
\ttree.position = pos
\tvar h := randf_range(50, 100)
\tvar trunk_w := randf_range(5, 9)
\tvar trunk := Polygon2D.new()
\ttrunk.polygon = PackedVector2Array([
\t\tVector2(-trunk_w/2, 0), Vector2(trunk_w/2, 0),
\t\tVector2(trunk_w/2 - 1, -h), Vector2(-trunk_w/2 + 1, -h),
\t])
\ttrunk.color = b["trunk"]
\ttree.add_child(trunk)
\t# canopy layers
\tfor i in range(randi_range(2, 4)):
\t\tvar canopy := Polygon2D.new()
\t\tvar cr := randf_range(18, 35)
\t\tvar cy := -h - i * cr * 0.5
\t\tcanopy.polygon = _circle_poly(cr, 8)
\t\tcanopy.position = Vector2(randf_range(-5, 5), cy)
\t\tcanopy.color = b["foliage"].lerp(b["foliage_alt"], randf())
\t\ttree.add_child(canopy)
\tparent.add_child(tree)


func _make_rock(parent: Node2D, pos: Vector2, b: Dictionary) -> void:
\tvar rock := Polygon2D.new()
\tvar w := randf_range(12, 30)
\tvar h := randf_range(8, 20)
\trock.polygon = PackedVector2Array([
\t\tVector2(-w/2, 0), Vector2(-w/2 + 3, -h * 0.8),
\t\tVector2(-w/4, -h), Vector2(w/4, -h * 0.9),
\t\tVector2(w/2 - 2, -h * 0.6), Vector2(w/2, 0),
\t])
\trock.position = pos
\trock.color = b["ground_deep"].lightened(0.1)
\tparent.add_child(rock)


func _make_grass(parent: Node2D, pos: Vector2, b: Dictionary) -> void:
\tfor i in range(randi_range(2, 5)):
\t\tvar blade := Line2D.new()
\t\tblade.width = 1.5
\t\tvar bx := randf_range(-6, 6)
\t\tvar bh := randf_range(6, 16)
\t\tvar sway := randf_range(-4, 4)
\t\tblade.add_point(pos + Vector2(bx, 0))
\t\tblade.add_point(pos + Vector2(bx + sway, -bh))
\t\tblade.default_color = b["foliage"].lerp(b["foliage_alt"], randf())
\t\tparent.add_child(blade)


func _make_flower(parent: Node2D, pos: Vector2, b: Dictionary) -> void:
\tvar stem := Line2D.new()
\tstem.width = 1.5
\tstem.add_point(pos)
\tstem.add_point(pos + Vector2(randf_range(-2, 2), -randf_range(10, 20)))
\tstem.default_color = b["foliage"]
\tparent.add_child(stem)
\tvar bud := Polygon2D.new()
\tbud.polygon = _circle_poly(4, 6)
\tbud.position = stem.points[1]
\tbud.color = b["accent"].lerp(Color.WHITE, randf_range(0, 0.3))
\tparent.add_child(bud)


# ── enemies ────────────────────────────────────────────────────────
func _place_enemies() -> void:
\tvar enemy_count := 8 + difficulty * 5
\tvar walker_scene := preload("res://scenes/enemy_walker.tscn")
\tvar flyer_scene := preload("res://scenes/enemy_flyer.tscn")
\tvar charger_scene := preload("res://scenes/enemy_charger.tscn")
\tvar scenes := [walker_scene, walker_scene, flyer_scene, charger_scene]
\tfor i in enemy_count:
\t\tvar ex := randf_range(T * 15, (world_width - 10) * T)
\t\tvar sy := _surface_y(ex)
\t\tvar scene: PackedScene = scenes[i % scenes.size()]
\t\tif scene == flyer_scene:
\t\t\tsy -= randf_range(60, 150)
\t\telse:
\t\t\tsy -= 20
\t\tvar e := scene.instantiate()
\t\te.position = Vector2(ex, sy)
\t\tadd_child(e)


# ── collectibles ───────────────────────────────────────────────────
func _place_collectibles(b: Dictionary) -> void:
\tvar coin_scene := preload("res://scenes/collectible.tscn")
\tvar count := 20 + difficulty * 5
\tfor i in count:
\t\tvar cx := randf_range(T * 5, (world_width - 5) * T)
\t\tvar sy := _surface_y(cx)
\t\tvar cy := sy - randf_range(30, 160)
\t\tvar c := coin_scene.instantiate()
\t\tc.position = Vector2(cx, cy)
\t\tadd_child(c)


# ── level exit ─────────────────────────────────────────────────────
func _place_exit(b: Dictionary) -> void:
\tvar exit := preload("res://scenes/level_exit.tscn").instantiate()
\tvar ex := (world_width - 6) * T
\texit.position = Vector2(ex, _surface_y(ex) - 40)
\tadd_child(exit)


# ── player spawn ───────────────────────────────────────────────────
func _spawn_player() -> void:
\tvar player := preload("res://scenes/player.tscn").instantiate()
\t# Spawn well inside the terrain to avoid left-edge gap
\tvar sx: float = T * 12.0
\tplayer.position = Vector2(sx, _surface_y(sx) - 40)
\tadd_child(player)


# ── ambient particles ──────────────────────────────────────────────
func _add_ambient_particles(b: Dictionary) -> void:
\tvar particles := GPUParticles2D.new()
\tparticles.amount = 40
\tparticles.lifetime = 5.0
\tparticles.visibility_rect = Rect2(-800, -500, 1600, 1000)
\tparticles.position = Vector2(world_width * T / 2.0, world_height * T / 2.0)
\tvar mat := ParticleProcessMaterial.new()
\tmat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
\tmat.emission_box_extents = Vector3(800, 400, 0)
\tmat.gravity = Vector3(0, 15, 0)
\tmat.initial_velocity_min = 5.0
\tmat.initial_velocity_max = 15.0
\tmat.scale_min = 1.0
\tmat.scale_max = 3.0
\tmat.color = b["particle"]
\tparticles.process_material = mat
\tadd_child(particles)


# ── camera bounds ──────────────────────────────────────────────────
func _add_camera_bounds() -> void:
\t# invisible walls at edges
\tvar left_wall := StaticBody2D.new()
\tleft_wall.position = Vector2(-T, 0)
\tvar lshape := RectangleShape2D.new()
\tlshape.size = Vector2(T * 2, world_height * T * 2)
\tvar lcol := CollisionShape2D.new()
\tlcol.shape = lshape
\tleft_wall.add_child(lcol)
\tadd_child(left_wall)

\tvar right_wall := StaticBody2D.new()
\tright_wall.position = Vector2(world_width * T + T, 0)
\tvar rshape := RectangleShape2D.new()
\trshape.size = Vector2(T * 2, world_height * T * 2)
\tvar rcol := CollisionShape2D.new()
\trcol.shape = rshape
\tright_wall.add_child(rcol)
\tadd_child(right_wall)


# ── utility ────────────────────────────────────────────────────────
func _circle_poly(radius: float, segments: int) -> PackedVector2Array:
\tvar pts := PackedVector2Array()
\tfor i in segments:
\t\tvar angle := TAU * float(i) / float(segments)
\t\tpts.append(Vector2(cos(angle), sin(angle)) * radius)
\treturn pts
''')

[sub_resource type="RectangleShape2D" id="pcol"]
size = Vector2(16, 38)

[node name="Player" type="CharacterBody2D" groups=["player"]]
collision_layer = 1
collision_mask = 1
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.5, 1.5)
offset = Vector2(0, -4)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, -2)
shape = SubResource("pcol")

[node name="Camera2D" type="Camera2D" parent="."]
zoom = Vector2(2.0, 2.0)
position_smoothing_enabled = true
position_smoothing_speed = 8.0
drag_horizontal_enabled = true
drag_vertical_enabled = true
drag_left_margin = 0.15
drag_right_margin = 0.15
drag_top_margin = 0.2
drag_bottom_margin = 0.3
''')

    # ═══════════════════════════════════════════════════════════════════
    #  ENEMIES — walker, flyer, charger
    # ═══════════════════════════════════════════════════════════════════

    def _write_enemy_walker(self) -> None:
        sc = self.spec.color_secondary
        self._write("scripts/enemies/enemy_walker.gd", f'''extends CharacterBody2D
## Patrol enemy — walks, turns at edges, damages player.

const SPEED := 70.0
const DAMAGE := 15
var _dir := 1.0
var _hp := 3

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var edge_ray: RayCast2D = $EdgeDetector


func _ready() -> void:
\tvar color := Color("{sc}")
\tsprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
\tsprite.play("run_right")
\t_dir = [-1.0, 1.0].pick_random()


func _physics_process(delta: float) -> void:
\tvar grav: float = ProjectSettings.get_setting("physics/2d/default_gravity")
\tvelocity.y += grav * delta
\tvelocity.x = _dir * SPEED

\tmove_and_slide()

\t# turn at walls
\tif is_on_wall():
\t\t_dir *= -1
\t# turn at edges (raycast checks for ground ahead)
\tif is_on_floor() and edge_ray and not edge_ray.is_colliding():
\t\t_dir *= -1

\tedge_ray.target_position = Vector2(_dir * 20, 30)
\tsprite.play("run_right" if _dir > 0 else "run_left")

\t# damage player on contact
\tfor i in get_slide_collision_count():
\t\tvar col := get_slide_collision(i)
\t\tif col.get_collider().has_method("take_damage"):
\t\t\tvar kb: Vector2 = (col.get_collider().global_position - global_position).normalized()
\t\t\tcol.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
\t_hp -= dmg
\tif _hp <= 0:
\t\tGameManager.add_score(25)
\t\t_death_effect()
\t\tqueue_free()
\telse:
\t\tvelocity += knockback * 100
\t\tvar tw := create_tween()
\t\ttw.tween_property(self, "modulate", Color.RED, 0.05)
\t\ttw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _death_effect() -> void:
\tvar particles := GPUParticles2D.new()
\tparticles.emitting = true
\tparticles.one_shot = true
\tparticles.amount = 12
\tparticles.lifetime = 0.5
\tvar mat := ParticleProcessMaterial.new()
\tmat.direction = Vector3(0, -1, 0)
\tmat.spread = 180.0
\tmat.initial_velocity_min = 80.0
\tmat.initial_velocity_max = 160.0
\tmat.gravity = Vector3(0, 400, 0)
\tmat.color = Color("{sc}")
\tparticles.process_material = mat
\tparticles.global_position = global_position
\tget_parent().add_child(particles)
\tawait get_tree().create_timer(0.6).timeout
\tparticles.queue_free()
''')
        self._write("scenes/enemy_walker.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemies/enemy_walker.gd" id="1"]

[sub_resource type="RectangleShape2D" id="ecol"]
size = Vector2(14, 32)

[node name="EnemyWalker" type="CharacterBody2D"]
collision_layer = 1
collision_mask = 1
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.2, 1.2)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")

[node name="EdgeDetector" type="RayCast2D" parent="."]
target_position = Vector2(20, 30)
''')

    def _write_enemy_flyer(self) -> None:
        sc = self.spec.color_secondary
        self._write("scripts/enemies/enemy_flyer.gd", f'''extends CharacterBody2D
## Flying enemy — bobs in air, dives at player.

const FLOAT_SPEED := 40.0
const DIVE_SPEED := 200.0
const DAMAGE := 20
const DETECT_RANGE := 250.0

var _hp := 2
var _origin := Vector2.ZERO
var _time := 0.0
var _diving := false

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\t_origin = global_position
\tvar color := Color("{sc}").lightened(0.2)
\tsprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
\tsprite.play("idle_right")


func _physics_process(delta: float) -> void:
\t_time += delta
\tvar player := _find_player()

\tif _diving:
\t\tif is_on_floor() or _time > 2.0:
\t\t\t_diving = false
\t\t\t_time = 0.0
\telse:
\t\t# bob in place
\t\tvar bob := Vector2(sin(_time * 1.5) * FLOAT_SPEED, cos(_time * 2.0) * FLOAT_SPEED * 0.5)
\t\tvelocity = bob
\t\t# dive at player if close
\t\tif player and global_position.distance_to(player.global_position) < DETECT_RANGE:
\t\t\tvar dir: Vector2 = global_position.direction_to(player.global_position)
\t\t\tvelocity = dir * DIVE_SPEED
\t\t\t_diving = true
\t\t\t_time = 0.0

\tmove_and_slide()
\tsprite.play("run_right" if velocity.x > 0 else "run_left")

\tfor i in get_slide_collision_count():
\t\tvar col := get_slide_collision(i)
\t\tif col.get_collider().has_method("take_damage"):
\t\t\tvar kb: Vector2 = (col.get_collider().global_position - global_position).normalized()
\t\t\tcol.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
\t_hp -= dmg
\tif _hp <= 0:
\t\tGameManager.add_score(35)
\t\tqueue_free()
\telse:
\t\tvar tw := create_tween()
\t\ttw.tween_property(self, "modulate", Color.RED, 0.05)
\t\ttw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _find_player() -> Node2D:
\tfor c in get_tree().get_nodes_in_group("player"):
\t\treturn c
\treturn null
''')
        self._write("scenes/enemy_flyer.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemies/enemy_flyer.gd" id="1"]

[sub_resource type="CircleShape2D" id="ecol"]
radius = 12.0

[node name="EnemyFlyer" type="CharacterBody2D"]
collision_layer = 1
collision_mask = 1
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.0, 1.0)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    def _write_enemy_charger(self) -> None:
        sc = self.spec.color_secondary
        self._write("scripts/enemies/enemy_charger.gd", f'''extends CharacterBody2D
## Charges at player when detected, rests between charges.

const IDLE_SPEED := 30.0
const CHARGE_SPEED := 320.0
const DAMAGE := 25
const DETECT_RANGE := 200.0
const CHARGE_DURATION := 0.6
const REST_DURATION := 1.5

var _hp := 4
var _state := "idle"
var _timer := 0.0
var _charge_dir := Vector2.ZERO

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
\tvar color := Color("{sc}").darkened(0.15)
\tsprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
\tsprite.play("idle_right")


func _physics_process(delta: float) -> void:
\tvar grav: float = ProjectSettings.get_setting("physics/2d/default_gravity")
\tvelocity.y += grav * delta
\t_timer -= delta

\tmatch _state:
\t\t"idle":
\t\t\tvelocity.x = move_toward(velocity.x, 0, 200 * delta)
\t\t\tvar player := _find_player()
\t\t\tif player and global_position.distance_to(player.global_position) < DETECT_RANGE:
\t\t\t\t_charge_dir = global_position.direction_to(player.global_position)
\t\t\t\t_state = "windup"
\t\t\t\t_timer = 0.4
\t\t"windup":
\t\t\tvelocity.x = 0
\t\t\tmodulate = Color(1.5, 0.5, 0.5)
\t\t\tif _timer <= 0:
\t\t\t\t_state = "charging"
\t\t\t\t_timer = CHARGE_DURATION
\t\t\t\tmodulate = Color.WHITE
\t\t"charging":
\t\t\tvelocity.x = _charge_dir.x * CHARGE_SPEED
\t\t\tif _timer <= 0 or is_on_wall():
\t\t\t\t_state = "rest"
\t\t\t\t_timer = REST_DURATION
\t\t\t\tif is_on_wall():
\t\t\t\t\tScreenEffects.shake(4.0, 0.15)
\t\t"rest":
\t\t\tvelocity.x = move_toward(velocity.x, 0, 300 * delta)
\t\t\tif _timer <= 0:
\t\t\t\t_state = "idle"

\tsprite.play("run_right" if velocity.x > 0 else "run_left" if velocity.x < -5 else "idle_right")
\tmove_and_slide()

\tfor i in get_slide_collision_count():
\t\tvar col := get_slide_collision(i)
\t\tif col.get_collider().has_method("take_damage") and _state == "charging":
\t\t\tvar kb := _charge_dir
\t\t\tcol.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
\t_hp -= dmg
\tif _hp <= 0:
\t\tGameManager.add_score(50)
\t\tqueue_free()
\telse:
\t\tvar tw := create_tween()
\t\ttw.tween_property(self, "modulate", Color.RED, 0.05)
\t\ttw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _find_player() -> Node2D:
\tfor c in get_tree().get_nodes_in_group("player"):
\t\treturn c
\treturn null
''')
        self._write("scenes/enemy_charger.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/enemies/enemy_charger.gd" id="1"]

[sub_resource type="RectangleShape2D" id="ecol"]
size = Vector2(20, 32)

[node name="EnemyCharger" type="CharacterBody2D"]
collision_layer = 1
collision_mask = 1
script = ExtResource("1")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
scale = Vector2(1.4, 1.4)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ecol")
''')

    # ═══════════════════════════════════════════════════════════════════
    #  COLLECTIBLE, EXIT, SCREEN EFFECTS
    # ═══════════════════════════════════════════════════════════════════

    def _write_collectible(self) -> None:
        self._write("scripts/collectible.gd", '''extends Area2D

const SCORE := 10
var _base_y := 0.0


func _ready() -> void:
\t_base_y = position.y
\tbody_entered.connect(_on_pickup)
\t# golden glow
\tvar glow := PointLight2D.new()
\tglow.color = Color(1, 0.85, 0.2, 0.6)
\tglow.texture_scale = 0.15
\tglow.energy = 0.5
\tadd_child(glow)


func _process(_d: float) -> void:
\tvar t: float = Time.get_ticks_msec() / 1000.0
\tposition.y = _base_y + sin(t * 1.5) * 4.0
\trotation = sin(t * 1.0) * 0.15


func _on_pickup(body: Node2D) -> void:
\tif body is CharacterBody2D and body.has_method("take_damage"):
\t\tGameManager.add_score(SCORE)
\t\tqueue_free()
''')
        self._write("scenes/collectible.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/collectible.gd" id="1"]

[sub_resource type="CircleShape2D" id="ccol"]
radius = 10.0

[node name="Collectible" type="Area2D"]
collision_layer = 4
collision_mask = 1
script = ExtResource("1")

[node name="Visual" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-6, -3, 0, -8, 6, -3, 6, 3, 0, 8, -6, 3)
color = Color(1, 0.85, 0.15, 1)

[node name="Shine" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-3, -1, 0, -4, 3, -1, 3, 1, 0, 4, -3, 1)
color = Color(1, 1, 0.7, 0.6)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("ccol")
''')

    def _write_level_exit(self) -> None:
        self._write("scripts/level_exit.gd", '''extends Area2D

var _activated := false


func _ready() -> void:
\tbody_entered.connect(_on_enter)
\t# pulsing glow
\tvar glow := PointLight2D.new()
\tglow.color = Color(0.2, 1.0, 0.4, 0.8)
\tglow.texture_scale = 0.4
\tglow.energy = 0.7
\tadd_child(glow)


func _process(_d: float) -> void:
\tvar s := 1.0 + sin(Time.get_ticks_msec() / 1000.0 * 2.0) * 0.1
\tscale = Vector2(s, s)


func _on_enter(body: Node2D) -> void:
\tif _activated:
\t\treturn
\tif body is CharacterBody2D and body.has_method("take_damage"):
\t\t_activated = true
\t\tGameManager.add_score(100)
\t\tLevelManager.advance_level()
''')
        self._write("scenes/level_exit.tscn", '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/level_exit.gd" id="1"]

[sub_resource type="RectangleShape2D" id="gcol"]
size = Vector2(30, 60)

[node name="LevelExit" type="Area2D"]
collision_layer = 4
collision_mask = 1
script = ExtResource("1")

[node name="Portal" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-15, 30, -12, -20, -6, -30, 6, -30, 12, -20, 15, 30)
color = Color(0.15, 0.9, 0.4, 0.7)

[node name="Inner" type="Polygon2D" parent="."]
polygon = PackedVector2Array(-8, 25, -6, -15, -2, -22, 2, -22, 6, -15, 8, 25)
color = Color(0.4, 1.0, 0.7, 0.5)

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = SubResource("gcol")
''')

    def _write_screen_effects(self) -> None:
        self._write("scripts/autoload/screen_effects.gd", '''extends CanvasLayer
## Screen effects — shake, flash. Access via the ScreenEffects autoload singleton.

var _shake_strength := 0.0
var _shake_decay := 0.0
var _flash_rect: ColorRect


func _ready() -> void:
\t_flash_rect = ColorRect.new()
\t_flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
\t_flash_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
\t_flash_rect.color = Color.TRANSPARENT
\tadd_child(_flash_rect)


func _process(delta: float) -> void:
\tvar cam = get_viewport().get_camera_2d()
\tif _shake_strength > 0.01:
\t\t_shake_strength = lerp(_shake_strength, 0.0, _shake_decay * delta * 60.0)
\t\tif cam:
\t\t\tcam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * _shake_strength
\telse:
\t\tif cam:
\t\t\tcam.offset = cam.offset.lerp(Vector2.ZERO, delta * 10.0)


func shake(strength: float, duration: float) -> void:
\t_shake_strength = strength
\t_shake_decay = 1.0 / max(duration, 0.01)


func flash(color: Color, duration: float) -> void:
\t_flash_rect.color = color
\tvar tween = create_tween()
\ttween.tween_property(_flash_rect, "color:a", 0.0, duration)
''')

    # ═══════════════════════════════════════════════════════════════════
    #  LEVEL SCENES — each configures the world generator differently
    # ═══════════════════════════════════════════════════════════════════

    def _write_level_scene(self, level_num: int) -> None:
        biomes = ["forest", "forest", "forest", "cave", "cave", "cave", "sky", "sky", "sky", "sky"]
        biome = biomes[min(level_num - 1, len(biomes) - 1)]
        width = 180 + level_num * 30
        seed_val = level_num * 1000 + 42

        self._write(f"scenes/level_{level_num}.tscn", f'''[gd_scene load_steps=4 format=3]

[ext_resource type="Script" path="res://scripts/world/world_generator.gd" id="1"]
[ext_resource type="PackedScene" path="res://scenes/hud.tscn" id="hud"]
[ext_resource type="PackedScene" path="res://scenes/pause_menu.tscn" id="pause"]

[node name="Level{level_num}" type="Node2D"]

[node name="WorldGenerator" type="Node2D" parent="."]
script = ExtResource("1")
biome = "{biome}"
difficulty = {level_num}
level_seed = {seed_val}
world_width = {width}

[node name="HUD" parent="." instance=ExtResource("hud")]

[node name="PauseMenu" parent="." instance=ExtResource("pause")]
''')
