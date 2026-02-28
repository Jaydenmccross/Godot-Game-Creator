extends CharacterBody2D
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
	var color := GameManager.color_secondary.darkened(0.15)
	sprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
	sprite.play("idle_right")


func _physics_process(delta: float) -> void:
	var grav: float = ProjectSettings.get_setting("physics/2d/default_gravity")
	velocity.y += grav * delta
	_timer -= delta

	match _state:
		"idle":
			velocity.x = move_toward(velocity.x, 0, 200 * delta)
			var player := _find_player()
			if player and global_position.distance_to(player.global_position) < DETECT_RANGE:
				_charge_dir = global_position.direction_to(player.global_position)
				_state = "windup"
				_timer = 0.4
		"windup":
			velocity.x = 0
			modulate = Color(1.5, 0.5, 0.5)
			if _timer <= 0:
				_state = "charging"
				_timer = CHARGE_DURATION
				modulate = Color.WHITE
		"charging":
			velocity.x = _charge_dir.x * CHARGE_SPEED
			if _timer <= 0 or is_on_wall():
				_state = "rest"
				_timer = REST_DURATION
				if is_on_wall():
					ScreenEffects.shake(4.0, 0.15)
		"rest":
			velocity.x = move_toward(velocity.x, 0, 300 * delta)
			if _timer <= 0:
				_state = "idle"

	sprite.play("run_right" if velocity.x > 0 else "run_left" if velocity.x < -5 else "idle_right")
	move_and_slide()

	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		if col.get_collider().has_method("take_damage") and _state == "charging":
			var kb := _charge_dir
			col.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
	_hp -= dmg
	if _hp <= 0:
		GameManager.add_score(50)
		queue_free()
	else:
		var tw := create_tween()
		tw.tween_property(self, "modulate", Color.RED, 0.05)
		tw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _find_player() -> Node2D:
	for c in get_tree().get_nodes_in_group("player"):
		return c
	return null
