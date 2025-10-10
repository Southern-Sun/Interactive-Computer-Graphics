#version 300 es
precision highp float;

uniform vec4 color;
uniform sampler2D texture_image;

uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 halfway;

in vec3 vnormal;
in vec2 vtexture_coord;

out vec4 fragColor;

void main() {
    vec4 tcolor = texture(texture_image, vtexture_coord);
    vec3 normal = normalize(vnormal);
    float lambert = dot(normal, light_direction);
    fragColor = vec4(
        tcolor.rgb * lambert,
        1.0
    );
}
