#version 300 es
layout(location=0) in vec4 position;
layout(location=1) in vec3 normal;

uniform mat4 model_view;
uniform mat4 perspective;

out vec3 vnormal;

void main() {
    gl_Position = perspective * model_view * position;
    vnormal = normal;
    // The following makes the object spin under the light rather than the light following it
    // vnormal = mat3(model_view) * normal;
}