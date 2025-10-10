#version 300 es
precision highp float;

uniform vec4 color;
uniform sampler2D texture;

uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 halfway;

in vec3 vnormal;
in vec2 vtexture_coord;

out vec4 fragColor;

void main() {
    vec3 normal = normalize(vnormal);
    float blinn = pow(max(dot(normal, halfway), 0.0), 150.0);
    float lambert = dot(normal, light_direction);
    fragColor = vec4(
        color.rgb * lambert * light_color
        + light_color * blinn,
        color.a
    );
}
