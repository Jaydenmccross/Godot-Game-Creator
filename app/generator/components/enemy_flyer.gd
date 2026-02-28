extends CharacterBody2D
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
	_origin = global_position
	var color := GameManager.color_secondary.lightened(0.2)
	sprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
	sprite.play("idle_right")


func _physics_process(delta: float) -> void:
	_time += delta
	var player := _find_player()

	if _diving:
		if is_on_floor() or _time > 2.0:
			_diving = false
			_time = 0.0
	else:
		# bob in place
		var bob := Vector2(sin(_time * 1.5) * FLOAT_SPEED, cos(_time * 2.0) * FLOAT_SPEED * 0.5)
		velocity = bob
		# dive at player if close
		if player and global_position.distance_to(player.global_position) < DETECT_RANGE:
			var dir: Vector2 = global_position.direction_to(player.global_position)
			velocity = dir * DIVE_SPEED
			_diving = true
			_time = 0.0

	move_and_slide()
	sprite.play("run_right" if velocity.x > 0 else "run_left")

	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		if col.get_collider().has_method("take_damage"):
			var kb: Vector2 = (col.get_collider().global_position - global_position).normalized()
			col.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
	_hp -= dmg
	if _hp <= 0:
		GameManager.add_score(35)
		queue_free()
	else:
		var tw := create_tween()
		tw.tween_property(self, "modulate", Color.RED, 0.05)
		tw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _find_player() -> Node2D:
	for c in get_tree().get_nodes_in_group("player"):
		return c
	return null
