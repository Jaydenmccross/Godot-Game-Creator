extends CharacterBody2D

enum State { IDLE, RUN, JUMP, FALL, WALL_SLIDE, DASH, ATTACK, HURT }

const SPEED := 280.0
const JUMP_VELOCITY := -420.0
const WALL_JUMP_VELOCITY := Vector2(280, -380)
const DASH_SPEED := 600.0
const DASH_DURATION := 0.15
const COYOTE_TIME := 0.12
const JUMP_BUFFER := 0.1
const ATTACK_DURATION := 0.22
const ATTACK_RANGE := 48.0
const HURT_DURATION := 0.35
const WALL_SLIDE_SPEED := 60.0

var state: State = State.IDLE
var facing_right := true
var _coyote_timer := 0.0
var _jump_buffer_timer := 0.0
var _dash_timer := 0.0
var _attack_timer := 0.0
var _hurt_timer := 0.0
var _dash_dir := Vector2.ZERO
var _invincible := false
var _was_on_floor := false

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var cam: Camera2D = $Camera2D


func _ready() -> void:
	# Primary Color is dynamically fed by project setup
	var color := Color(GlobalColors.primary_color)
	sprite.sprite_frames = SpriteGenerator.create_platformer_frames(color, color.lightened(0.4))
	sprite.play("idle_right")


func _physics_process(delta: float) -> void:
	var gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity")

	_coyote_timer = max(0.0, _coyote_timer - delta)
	_jump_buffer_timer = max(0.0, _jump_buffer_timer - delta)

	if Input.is_action_just_pressed("jump"):
		_jump_buffer_timer = JUMP_BUFFER

	if is_on_floor():
		_coyote_timer = COYOTE_TIME
	_was_on_floor = is_on_floor()

	match state:
		State.IDLE, State.RUN:
			_state_grounded(delta, gravity)
		State.JUMP, State.FALL:
			_state_airborne(delta, gravity)
		State.WALL_SLIDE:
			_state_wall_slide(delta, gravity)
		State.DASH:
			_state_dash(delta)
		State.ATTACK:
			_state_attack(delta, gravity)
		State.HURT:
			_state_hurt(delta, gravity)

	_update_animation()
	move_and_slide()

	if global_position.y > 1200:
		GameManager.take_damage(100)
		LevelManager.restart_level()


func _state_grounded(delta: float, grav: float) -> void:
	var dir := Input.get_axis("move_left", "move_right")
	velocity.x = dir * SPEED
	velocity.y += grav * delta
	_update_facing(dir)

	if _jump_buffer_timer > 0.0:
		velocity.y = JUMP_VELOCITY
		_jump_buffer_timer = 0.0
		state = State.JUMP
	elif Input.is_action_just_pressed("action"):
		_start_attack()
	elif not is_on_floor():
		state = State.FALL
	elif abs(dir) > 0.1:
		state = State.RUN
	else:
		state = State.IDLE


func _state_airborne(delta: float, grav: float) -> void:
	var dir := Input.get_axis("move_left", "move_right")
	velocity.x = dir * SPEED
	velocity.y += grav * delta
	_update_facing(dir)

	if state == State.JUMP and Input.is_action_just_released("jump") and velocity.y < 0:
		velocity.y *= 0.4

	if _coyote_timer > 0.0 and _jump_buffer_timer > 0.0:
		velocity.y = JUMP_VELOCITY
		_coyote_timer = 0.0
		_jump_buffer_timer = 0.0
		state = State.JUMP

	if is_on_wall() and dir != 0.0 and velocity.y > 0:
		state = State.WALL_SLIDE

	if Input.is_action_just_pressed("action"):
		_start_attack()

	if is_on_floor():
		state = State.IDLE
	elif velocity.y > 0:
		state = State.FALL


func _state_wall_slide(delta: float, grav: float) -> void:
	velocity.y = min(velocity.y + grav * delta, WALL_SLIDE_SPEED)
	var dir := Input.get_axis("move_left", "move_right")

	if Input.is_action_just_pressed("jump"):
		var wall_normal := get_wall_normal()
		velocity = Vector2(wall_normal.x * WALL_JUMP_VELOCITY.x, WALL_JUMP_VELOCITY.y)
		facing_right = wall_normal.x > 0
		state = State.JUMP
	elif is_on_floor():
		state = State.IDLE
	elif not is_on_wall() or dir == 0.0:
		state = State.FALL


func _state_dash(delta: float) -> void:
	_dash_timer -= delta
	velocity = _dash_dir * DASH_SPEED
	if _dash_timer <= 0.0:
		state = State.FALL if not is_on_floor() else State.IDLE


func _state_attack(delta: float, grav: float) -> void:
	_attack_timer -= delta
	velocity.x = move_toward(velocity.x, 0, SPEED * delta * 5)
	velocity.y += grav * delta
	if _attack_timer <= 0.0:
		state = State.IDLE if is_on_floor() else State.FALL


func _state_hurt(delta: float, grav: float) -> void:
	_hurt_timer -= delta
	velocity.y += grav * delta
	velocity.x = move_toward(velocity.x, 0, SPEED * delta * 3)
	if _hurt_timer <= 0.0:
		_invincible = false
		modulate.a = 1.0
		state = State.IDLE if is_on_floor() else State.FALL


func _start_attack() -> void:
	state = State.ATTACK
	_attack_timer = ATTACK_DURATION
	var dir := Vector2.RIGHT if facing_right else Vector2.LEFT
	var space := get_world_2d().direct_space_state
	var query := PhysicsRayQueryParameters2D.create(global_position, global_position + dir * ATTACK_RANGE)
	query.exclude = [get_rid()]
	var result := space.intersect_ray(query)
	if result and result.collider.has_method("take_hit"):
		result.collider.take_hit(1, dir)
		ScreenEffects.shake(3.0, 0.1)


func take_damage(amount: int, knockback_dir: Vector2 = Vector2.ZERO) -> void:
	if _invincible or state == State.HURT:
		return
	GameManager.take_damage(amount)
	state = State.HURT
	_hurt_timer = HURT_DURATION
	_invincible = true
	velocity = knockback_dir.normalized() * 150 + Vector2(0, -120)
	ScreenEffects.shake(4.0, 0.15)
	_start_invincibility_blink()


func _start_invincibility_blink() -> void:
	var blink_count := 0
	while blink_count < 6 and _invincible:
		modulate.a = 0.3
		await get_tree().create_timer(0.1).timeout
		modulate.a = 1.0
		await get_tree().create_timer(0.1).timeout
		blink_count += 1
	modulate.a = 1.0


func _update_facing(dir: float) -> void:
	if dir > 0.1:
		facing_right = true
	elif dir < -0.1:
		facing_right = false


func _update_animation() -> void:
	var suffix := "_right" if facing_right else "_left"
	var anim: String
	match state:
		State.IDLE:       anim = "idle" + suffix
		State.RUN:        anim = "run" + suffix
		State.JUMP:       anim = "jump" + suffix
		State.FALL:       anim = "fall" + suffix
		State.WALL_SLIDE: anim = "fall" + suffix
		State.DASH:       anim = "run" + suffix
		State.ATTACK:     anim = "attack" + suffix
		State.HURT:       anim = "fall" + suffix
		_:                anim = "idle" + suffix
	if sprite.animation != anim:
		sprite.play(anim)
