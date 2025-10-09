
const IlliniBlue = new Float32Array([0.075, 0.16, 0.292, 1])
const IlliniOrange = new Float32Array([1, 0.373, 0.02, 1])
const IdentityMatrix = new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])

/**
 * Given the source code of a vertex and fragment shader, compiles them,
 * and returns the linked program.
 */
function compileShader(vs_source, fs_source) {
    const vs = gl.createShader(gl.VERTEX_SHADER)
    gl.shaderSource(vs, vs_source)
    gl.compileShader(vs)
    if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(vs))
        throw Error("Vertex shader compilation failed")
    }

    const fs = gl.createShader(gl.FRAGMENT_SHADER)
    gl.shaderSource(fs, fs_source)
    gl.compileShader(fs)
    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(fs))
        throw Error("Fragment shader compilation failed")
    }

    const program = gl.createProgram()
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error(gl.getProgramInfoLog(program))
        throw Error("Linking failed")
    }
    
    const uniforms = {}
    for(let i=0; i<gl.getProgramParameter(program, gl.ACTIVE_UNIFORMS); i+=1) {
        let info = gl.getActiveUniform(program, i)
        uniforms[info.name] = gl.getUniformLocation(program, info.name)
    }
    program.uniforms = uniforms

    return program
}

/**
 * Sends per-vertex data to the GPU and connects it to a VS input
 * 
 * @param data    a 2D array of per-vertex data (e.g. [[x,y,z,w],[x,y,z,w],...])
 * @param loc     the layout location of the vertex shader's `in` attribute
 * @param mode    (optional) gl.STATIC_DRAW, gl.DYNAMIC_DRAW, etc
 * 
 * @returns the ID of the buffer in GPU memory; useful for changing data later
 */
function supplyDataBuffer(data, loc, mode) {
    if (mode === undefined) mode = gl.STATIC_DRAW
    
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    const f32 = new Float32Array(data.flat())
    gl.bufferData(gl.ARRAY_BUFFER, f32, mode)
    
    gl.vertexAttribPointer(loc, data[0].length, gl.FLOAT, false, 0, 0)
    gl.enableVertexAttribArray(loc)
    
    return buf;
}

/**
 * Creates a Vertex Array Object and puts into it all of the data in the given
 * JSON structure, which should have the following form:
 * 
 * ````
 * {"triangles": a list of of indices of vertices
 * ,"attributes":
 *  [ a list of 1-, 2-, 3-, or 4-vectors, one per vertex to go in location 0
 *  , a list of 1-, 2-, 3-, or 4-vectors, one per vertex to go in location 1
 *  , ...
 *  ]
 * }
 * ````
 * 
 * @returns an object with four keys:
 *  - mode = the 1st argument for gl.drawElements
 *  - count = the 2nd argument for gl.drawElements
 *  - type = the 3rd argument for gl.drawElements
 *  - vao = the vertex array object for use with gl.bindVertexArray
 */
function setup_geometry(geometry) {
    var triangleArray = gl.createVertexArray()
    gl.bindVertexArray(triangleArray)

    for(let i=0; i<geometry.attributes.length; i+=1) {
        let data = geometry.attributes[i]
        // console.log(data)
        supplyDataBuffer(data, i)
    }

    var indices = new Uint16Array(geometry.triangles.flat())
    // console.log(indices)
    var indexBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer)
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, indices, gl.STATIC_DRAW)

    return {
        mode: gl.TRIANGLES,
        count: indices.length,
        type: gl.UNSIGNED_SHORT,
        vao: triangleArray
    }
}

/** Converts information about orbital & spin periods in seconds to frequencies we can use
 * for rotation
 */
function period(period_in_seconds) {
    if (period_in_seconds == 0) {
        return 0
    }
    return 2 * Math.PI / period_in_seconds
}


/** Draw one frame */
function draw(seconds) {
    gl.clearColor(...IlliniBlue) // f(...[1,2,3]) means f(1,2,3)
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
    gl.useProgram(program)

    // Default brown color
    gl.uniform4fv(program.uniforms.color, IlliniOrange)

    // Slow down the animation here
    seconds = seconds / 2

    // Setup our parameters -- Spins & Orbits are periods in seconds
    const CAMERA_RADIUS = 2.0
    const CAMERA_ORBIT = period(10.0) * seconds
    const EYE = [
        CAMERA_RADIUS * Math.cos(CAMERA_ORBIT),
        CAMERA_RADIUS * Math.sin(CAMERA_ORBIT),
        2
    ]

    var light_direction = [0, 0, 1]
    var halfway_vector = normalize(add(light_direction, EYE))
    gl.uniform3fv(program.uniforms.light_direction, normalize(light_direction))
    gl.uniform3fv(program.uniforms.light_color, [1, 1, 1])
    gl.uniform3fv(program.uniforms.halfway, halfway_vector)

    // Set our perspective matrix
    gl.uniformMatrix4fv(program.uniforms.perspective, false, perspective_matrix)
    var view_matrix = m4view(EYE, [0, 0, 0], [0, 0, 1])

    gl.bindVertexArray(geometry.vao)

    terrain_model = IdentityMatrix
    gl.uniformMatrix4fv(program.uniforms.model_view, false, m4mul(view_matrix, terrain_model))
    gl.drawElements(geometry.mode, geometry.count, geometry.type, 0)
}

/** Generate the object given rings & slices */
function generate_object(rings, slices, is_torus) {
    if (is_torus) {
        return generate_torus(rings, slices)
    }
    return generate_sphere(rings, slices)
}

function generate_sphere(rings, slices) {
    var attributes = [[], []]
    var triangles = []

    // One way we can approach this is by rotating origin point with a matrix.
    // First, we have two static points, top and bottom
    var top = [0, 0, 1, 1]
    var bottom = [0, 0, -1, 1]
    attributes[0].push(top)
    attributes[0].push(bottom)
    attributes[1].push(normalize(top))
    attributes[1].push(normalize(bottom))

    // Next, we can rotate top n slices upwards, moving PI/n+1 radians each time (one half rotation)
    var ring_matrix = m4rotX(Math.PI / (rings + 1))
    var last_point = bottom
    for (let i = 0; i < rings; i++) {
        last_point = m4mul(ring_matrix, last_point)
        attributes[0].push(last_point)
        attributes[1].push(normalize(last_point))
        
        // Then, for each step in the slice rotation, anchor on that point and rotate in Z for 2*PI
        var slice_matrix = m4rotZ(Math.PI * 2 / slices)
        var last_slice = last_point
        // j = 1 since we already saved our first point
        for (let j = 1; j < slices; j++) {
            last_slice = m4mul(slice_matrix, last_slice)
            attributes[0].push(last_slice)
            attributes[1].push(normalize(last_slice))
        }
    }

    // Finally, we need to connect our geometry. We know that the first two points [0], [1] are top
    // and bottom. Then, each ring has slice # of points as it moves up. The first and last case are
    // degenerate - they connect every point in the first & last ring to the bottom & top.
    // After those cases, each point in the ring should make two triangles with the ring above it

    // Degenerate case: bottom & top
    const bottom_slice_offset = 2
    const top_slice_offset = bottom_slice_offset + (rings - 1) * slices
    for (let i = 0; i < slices; i++) {
        let top_triangle = [
            0,
            top_slice_offset + (i + 1) % slices,
            top_slice_offset + i
        ]
        triangles.push(top_triangle)
        let bottom_triangle = [
            1,
            bottom_slice_offset + i,
            bottom_slice_offset + (i + 1) % slices
        ]
        triangles.push(bottom_triangle)
    }

    for (let ring = 0; ring < (rings - 1); ring++) {
        for (let i = 0; i < slices; i++) {
            // We need two triangles for every 4 points
            let bottom_ring_first_point = bottom_slice_offset + i + ring * slices
            let bottom_ring_second_point = bottom_slice_offset + (i + 1) % slices + ring * slices
            let top_ring_first_point = bottom_ring_first_point + slices
            let top_ring_second_point = bottom_ring_second_point + slices

            triangles.push([
                bottom_ring_first_point,
                top_ring_second_point,
                bottom_ring_second_point
            ])
            triangles.push([
                bottom_ring_first_point,
                top_ring_first_point,
                top_ring_second_point
            ])
        }
    }

    return_value = {
        attributes: attributes,
        triangles: triangles
    }
    console.log(return_value)
    return return_value
}

function generate_torus(rings, slices) {
    var attributes = [[], []]
    var triangles = []

    const TORUS_THICKNESS = .5
    const TORUS_RADIUS = 1
    // One way we can approach this is by rotating point with a matrix.
    // First, we have one static point, the offest for the torus
    var anchor = [0, 0, 0, 1]
    var radius_matrix = m4trans(TORUS_RADIUS, 0, 0)

    // Next, we rotate this point around the origin to create our torus center
    for (let i = 0; i < slices; i++) {
        let slice_matrix = m4mul(
            m4rotZ(Math.PI * 2 / slices * i),
            radius_matrix
        )
        // Center point of the current slice:
        let slice_center = m4mul(slice_matrix, anchor)
        let offset_matrix = m4trans(0, 0, TORUS_THICKNESS)
        
        for (let ring = 0; ring < rings; ring++) {
            let ring_matrix = m4rotY(Math.PI * 2 / rings * ring)
            // Offset the point, then rotate around the ring, then rotate around the slice
            let current_point = m4mul(slice_matrix, ring_matrix, offset_matrix, anchor)
            attributes[0].push(current_point)
            // Normal is the vector between this point and the slice center
            attributes[1].push(normalize(sub(current_point, slice_center)))
        }
    }

    // Now, we need to connect the geometry. 
    // Each point in the ring should make two triangles with the ring above it, same as sphere
    for (let slice = 0; slice < slices; slice++) {
        for (let ring = 0; ring < rings; ring++) {
            ring1_first = ring + slice * rings
            ring1_second = (ring + 1) % rings + slice * rings
            ring2_first = (ring1_first + rings) % (slices * rings)
            ring2_second = (ring1_second + rings) % (slices * rings)

            triangles.push([ring1_first, ring2_first, ring2_second])
            triangles.push([ring1_first, ring2_second, ring1_second])
        }
    }

    return_value = {
        attributes: attributes,
        triangles: triangles
    }
    console.log(return_value)
    return return_value
}

/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
    let seconds = milliseconds / 1000;
    if (geometry != null) {
        draw(seconds)
    }
    requestAnimationFrame(tick)
}

/** Resizes the canvas to completely fill the screen */
function fillScreen() {
    let canvas = document.querySelector('canvas')
    document.body.style.margin = '0'
    canvas.style.width = '100vw'
    canvas.style.height = '100vh'
    canvas.width = canvas.clientWidth
    canvas.height = canvas.clientHeight
    canvas.style.width = ''
    canvas.style.height = ''
    if (window.gl) {
        gl.viewport(0,0, canvas.width, canvas.height)
        window.perspective_matrix = m4perspNegZ(1, 20, 1.5, canvas.width, canvas.height)
    }
}

/** Compile, link, set up geometry */
window.addEventListener('load', async (event) => {
    window.gl = document.querySelector('canvas').getContext('webgl2',
        // optional configuration object: see https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/getContext
        {antialias: false, depth:true, preserveDrawingBuffer:true}
    )
    let vs = await fetch('src/vertex.glsl').then(res => res.text())
    let fs = await fetch('src/fragment.glsl').then(res => res.text())
    window.program = compileShader(vs,fs)
    gl.enable(gl.DEPTH_TEST)
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

    window.geometry = null
    document.querySelector('#submit').addEventListener('click', event => {
        const rings = Number(document.querySelector('#rings').value) || 1
        const slices = Number(document.querySelector('#slices').value) || 3
        const is_torus = document.querySelector("#torus").checked
        // TODO: generate a new gridsize-by-gridsize grid here, then apply faults to it
        window.geometry = setup_geometry(generate_object(rings, slices, is_torus))
    })
    
    fillScreen()
    window.addEventListener('resize', fillScreen)
    requestAnimationFrame(tick)
})
