#version 300 es

layout(location=0) in vec4 position;
layout(location=1) in vec4 color;

uniform float seconds;

out vec4 vColor;

void main() {
    vColor = color;
    float sign_flip = float(gl_VertexID % 2 * 2 - 1);
    float offset = float(
        gl_VertexID % 2 * 5
        + gl_VertexID % 3 * 4
        + gl_VertexID % 4 * 3
        + gl_VertexID % 5 * 2
        + gl_VertexID % 6 * 1
    ) / 10.0;
    float magnitude = 0.1;
    float x = position.x + cos(seconds + offset) * sign_flip * magnitude; 
    float y = position.y + sin(seconds + offset) * sign_flip * magnitude;
    gl_Position = vec4(x, y, position.z, position.w * 5.0);
}
