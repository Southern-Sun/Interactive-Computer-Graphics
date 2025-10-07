#version 300 es

layout(location=0) in vec4 position;
layout(location=1) in vec4 color;

// These matrices are constants
uniform mat4 rigid_matrix;
uniform mat4 rotation_matrix;

out vec4 vColor;

void main() {
    vColor = color;
    gl_Position = rigid_matrix * rotation_matrix * position;
}
