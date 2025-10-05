#version 300 es

out vec4 position;

void main() {
    int x = int((
        (gl_VertexID + 1) % 6
    ) / 3) * 2 - 1;

    int y = (gl_VertexID % 2) * 2 - 1;

    gl_Position = vec4(x, y, 0, 1);
    position = gl_Position;
}
