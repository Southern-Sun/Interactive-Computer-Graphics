#version 300 es
precision highp float;

in vec4 position;
uniform float seconds;

out vec4 fragColor;

void main() {
    float x = float(position.x);
    float y = float(position.y);

    float radius = length(position);
    float angle = atan(position.y, position.x);

    float red = 0.5 + 0.5 * sin(6.0 * angle + 3.0 * radius - 1.3 * seconds);
    float green = 0.5 + 0.5 * sin(4.0 * angle - 5.0 * radius + 0.9 * seconds);
    float blue = 0.5 + 0.5 * sin(3.0 * angle + 7.0 * radius + 1.7 * seconds);

    fragColor = vec4(red, green, blue, 1);
}
