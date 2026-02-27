extends Control


func _ready() -> void:
	var label := Label.new()
	label.text = "Godot Game Creator - Hello World!"
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 32)
	label.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(label)
	print("Godot Game Creator initialized successfully!")
