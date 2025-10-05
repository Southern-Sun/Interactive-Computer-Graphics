#version 300 es

layout(location=0) in vec4 position;
layout(location=1) in vec4 color;

uniform float seconds;

out vec4 vColor;

void main() {
    vColor = color;
    // Move from world coordinates to image coordinates (-1 to 1)
    vec4 image_position = vec4(position.x / 3.0, position.y / 3.0, position.zw);
    gl_Position = vec4(
        image_position.xy*cos(seconds*0.6180339887498949),
        image_position.zw
    );
}
