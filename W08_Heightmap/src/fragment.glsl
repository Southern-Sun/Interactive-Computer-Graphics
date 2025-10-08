#version 300 es
precision highp float;

// uniform vec4 color;

uniform vec3 light_direction;
uniform vec3 light_color;
uniform vec3 halfway;

in vec3 vnormal;
in float vheight;

out vec4 fragColor;

void main() {
    // normalize height (which is -1 to 1)
    float BANDS = 3.0;
    float height = (vheight + 1.0) / 2.0 * BANDS;
    height = height - floor(height);
    // vec4 red = vec4(1.0, 0.0, 0.0, 1.0);
    // vec4 green = vec4(0.0, 1.0, 0.0, 1.0);
    // vec4 blue = vec4(0.0, 0.0, 1.0, 1.0);

    // vec4 top_color = red;
    // vec4 bottom_color = blue;
    // float t = mod(height, 6.0);
    // vec4 color = top_color * t + bottom_color * (1.0-t);

    // vec4 color = vec4(height, 0.0, 1.0-height, 1.0);

    // vec4 color = vec4(
    //     height > 0.0 ? height : 0.0,
    //     height > 0.0 ? 0.0 : 0.0 - height,
    //     height > 0.0 ? 1.0 - height : 1.0 + height,
    //     1.0
    // );

    // 0 = RED
    // 33 = GREEN
    // 66 = BLUE
    // vec4 color = vec4(
    //     // height > .33 ? (height > .67 ? [.67, 1.0] : [.33, .67]) : [0.0, .33],
    //     height > 1.0/3.0 ? (height > 2.0/3.0 ? (height - 2.0/3.0) * 3.0 : 0.0) : 1.0 - height * 3.0,
    //     height > 1.0/3.0 ? (height > 2.0/3.0 ? 0.0 : 1.0 - (height - 1.0/3.0) * 3.0) : height * 3.0,
    //     height > 1.0/3.0 ? (height > 2.0/3.0 ? 1.0 - (height - 2.0/3.0) * 3.0 : (height - 1.0/3.0) * 3.0) : 0.0,
    //     1.0
    // );

    // 0-33 = RED
    // 33-66 = GREEN
    // 66-100 = BLUE
    vec4 color = vec4(
        // height > .33 ? (height > .67 ? [.67, 1.0] : [.33, .67]) : [0.0, .33],
        height > 1.0/3.0 ? (height > 2.0/3.0 ? (height - 2.0/3.0) * 3.0 : 1.0 - (height - 1.0/3.0) * 3.0) : 1.0,
        height > 1.0/3.0 ? (height > 2.0/3.0 ? 1.0 - (height - 2.0/3.0) * 3.0 : 1.0) : height * 3.0,
        height > 1.0/3.0 ? (height > 2.0/3.0 ? 1.0 : (height - 1.0/3.0) * 3.0) : 1.0 - height * 3.0,
        1.0
    );

    vec3 normal = normalize(vnormal);
    float blinn = pow(max(dot(normal, halfway), 0.0), 150.0);
    float lambert = dot(normal, light_direction);
    fragColor = vec4(
        color.rgb * lambert * light_color
        + light_color * blinn,
        color.a
    );
}