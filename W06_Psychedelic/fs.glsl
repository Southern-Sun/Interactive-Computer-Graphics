#version 300 es
precision highp float;

in vec4 position;
uniform float seconds;

out vec4 fragColor;

void main() {
    float x = float(position.x);
    float y = float(position.y);
    float red = sin(seconds * (
        5.0 
        + 4.0 * x 
        + 3.0 * y
        + 2.0 * x * x 
        + 1.0 * x * y 
        + 2.0 * y * y
        + 3.0 * x * x * x
        + 4.0 * x * x * y
        + 5.0 * x * y * y
        + 6.0 * y * y * y
        + 7.0 * x * x * x * x
        + 8.0 * x * x * x * y
        + 9.0 * x * x * y * y
        + 8.0 * x * y * y * y
        + 7.0 * y * y * y * y
    ));
    fragColor = vec4(red, 0, 0, 1);
}
