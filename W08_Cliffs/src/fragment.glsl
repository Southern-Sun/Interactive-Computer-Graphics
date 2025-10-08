#version 300 es
precision highp float;

uniform vec4 shallow_color;
uniform vec4 steep_color;

uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 halfway;

in vec3 vnormal;

out vec4 fragColor;

void main() {
    vec3 normal = normalize(vnormal);
    bool is_shallow = normal.z > .6;
    vec4 color = is_shallow ? shallow_color : steep_color;
    float SHINE_SIZE = is_shallow ? 250.0 : 100.0;
    float SHINE_INTENSITY = is_shallow ? 2.0 : .5;

    float blinn = pow(max(dot(normal, halfway), 0.0), SHINE_SIZE);
    float lambert = dot(normal, light_direction);
    fragColor = vec4(
        color.rgb * lambert * light_color
        + light_color * blinn * SHINE_INTENSITY,
        color.a
    );
}