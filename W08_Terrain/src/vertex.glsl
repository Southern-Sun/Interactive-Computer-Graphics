#version 300 es
layout(location=0) in vec4 position;

uniform mat4 model_view;
uniform mat4 perspective;

void main() {
    gl_Position = perspective * model_view * position;
}