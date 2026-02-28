extends CharacterBody2D
## Patrol enemy — walks, turns at edges, damages player.

const SPEED := 70.0
const DAMAGE := 15
var _dir := 1.0
var _hp := 3

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var edge_ray: RayCast2D = $EdgeDetector


func _ready() -> void:
	var color := GameManager.color_secondary
	sprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.3))
	sprite.play("run_right")
	_dir = [-1.0, 1.0].pick_random()


func _physics_process(delta: float) -> void:
	var grav: float = ProjectSettings.get_setting("physics/2d/default_gravity")
	velocity.y += grav * delta
	velocity.x = _dir * SPEED

	move_and_slide()

	# turn at walls
	if is_on_wall():
		_dir *= -1
	# turn at edges (raycast checks for ground ahead)
	if is_on_floor() and edge_ray and not edge_ray.is_colliding():
		_dir *= -1

	edge_ray.target_position = Vector2(_dir * 20, 30)
	sprite.play("run_right" if _dir > 0 else "run_left")

	# damage player on contact
	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		if col.get_collider().has_method("take_damage"):
			var kb: Vector2 = (col.get_collider().global_position - global_position).normalized()
			col.get_collider().take_damage(DAMAGE, kb)


func take_hit(dmg: int, knockback: Vector2 = Vector2.ZERO) -> void:
	_hp -= dmg
	if _hp <= 0:
		GameManager.add_score(25)
		_death_effect()
		queue_free()
	else:
		velocity += knockback * 100
		var tw := create_tween()
		tw.tween_property(self, "modulate", Color.RED, 0.05)
		tw.tween_property(self, "modulate", Color.WHITE, 0.1)


func _death_effect() -> void:
	var particles := GPUParticles2D.new()
	particles.emitting = true
	particles.one_shot = true
	particles.amount = 12
	particles.lifetime = 0.5
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(0, -1, 0)
	mat.spread = 180.0
	mat.initial_velocity_min = 80.0
	mat.initial_velocity_max = 160.0
	mat.gravity = Vector3(0, 400, 0)
	mat.color = GameManager.color_secondary
	particles.process_material = mat
	particles.global_position = global_position
	get_parent().add_child(particles)
	await get_tree().create_timer(0.6).timeout
	particles.queue_free()
