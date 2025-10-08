
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
        console.log(data)
        supplyDataBuffer(data, i)
    }

    var indices = new Uint16Array(geometry.triangles.flat())
    console.log(indices)
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
    gl.uniform4fv(program.uniforms.color, [.7, .4, .2, 1])

    // Slow down the animation here
    seconds = seconds / 2

    // Setup our parameters -- Spins & Orbits are periods in seconds
    const TERRAIN_SPIN = 10
    const CAMERA_RADIUS = 3.0
    const CAMERA_ORBIT = period(10.0) * seconds
    const EYE = [
        CAMERA_RADIUS * Math.cos(CAMERA_ORBIT),
        CAMERA_RADIUS * Math.sin(CAMERA_ORBIT),
        1.5
    ]

    var light_direction = [1, 1, 1]
    var halfway_vector = normalize(add(light_direction, EYE))
    gl.uniform3fv(program.uniforms.light_direction, normalize(light_direction))
    gl.uniform3fv(program.uniforms.light_color, [1, 1, 1])
    gl.uniform3fv(program.uniforms.halfway, halfway_vector)

    // Set our perspective matrix
    gl.uniformMatrix4fv(program.uniforms.perspective, false, perspective_matrix)
    var view_matrix = m4view(EYE, [0, 0, 0], [0, 0, 1])

    gl.bindVertexArray(terrain.vao)

    terrain_model = m4rotZ(period(TERRAIN_SPIN))
    gl.uniformMatrix4fv(program.uniforms.model_view, false, m4mul(view_matrix, terrain_model))
    gl.drawElements(terrain.mode, terrain.count, terrain.type, 0)
}

function add_terrain_fault(grid, delta) {
    var point = [Math.random() * 2 - 1, Math.random() * 2 - 1, 0]
    var normal = [Math.random() * 2 - 1, Math.random() * 2 - 1, 0]

    for (let i = 0; i < grid.length; i++) {
        let direction = dot(sub(grid[i], point), normal) >= 0 ? 1 : -1
        grid[i] = [grid[i][0], grid[i][1], grid[i][2] - delta * direction]
    }

    return grid
}

/** Generate the terrain given fractures and grid size */
function generate_terrain(gridsize, faults) {
    const HIGHEST_PEAK = 1
    xy_to_index = (x, y) => { return x * gridsize + y }
    var grid = [[], []]
    var elements = []
    for (let x = 0; x < gridsize; x++) {
        for (let y = 0; y < gridsize; y++) {
            // Position
            // Create points on the XY plane. Z is our height, which we will set to 1 by default
            // Position is the distance through the grid mapped to -1 to 1
            let z = Math.sqrt(Math.sin(y/gridsize * Math.PI) + Math.sin(x/gridsize * Math.PI))
            if (isNaN(z)) { console.log(x, y) }
            grid[0].push([x/gridsize * 2 - 1, y/gridsize * 2 - 1, 0])

            // Normals
            grid[1].push([0, 0, 0])

            if (y === (gridsize-1) || x === (gridsize-1)) {
                // Case: last col/row, no elements to draw
                continue
            }
            elements.push([xy_to_index(x, y), xy_to_index(x + 1, y), xy_to_index(x, y + 1)])
            elements.push([xy_to_index(x + 1, y), xy_to_index(x + 1, y + 1), xy_to_index(x, y + 1)])
        }
    }

    // Add faults here before we bother with computing normals
    for (let i = 0; i < faults; i++) {
        let delta = 1 / (i + 5)
        grid[0] = add_terrain_fault(grid[0], delta)
    }

    // Normalize the grid heights
    heights = grid[0].map(point => point[2])
    max_height = Math.max(...heights)
    min_height = Math.min(...heights)
    for (let i = 0; i < grid[0].length; i++) {
        new_height = (grid[0][i][2] - .5 * (max_height + min_height)) / (max_height - min_height)
        new_height = new_height * HIGHEST_PEAK
        grid[0][i] = [grid[0][i][0], grid[0][i][1], new_height]
    }

    // Compute normals (old -- model)
    // for (let i = 0; i < elements.length; i++) {
    //     edge1 = sub(grid[0][elements[i][1]], grid[0][elements[i][0]])
    //     edge2 = sub(grid[0][elements[i][2]], grid[0][elements[i][0]])
    //     normal = cross(edge1, edge2)

    //     for (let j = 0; j < 3; j++) {
    //         // Add the computed normal to each of the points' normal attribute
    //         grid[1][elements[i][j]] = add(grid[1][elements[i][j]], normal)
    //     }
    // }
    // Compute normals (new -- grid-based)
    for (let i = 0; i < grid[0].length; i++) {
        clamp = (value) => { return Math.max(Math.min(value, gridsize - 1), 0)}
        let x = Math.floor(i / gridsize)
        let y = i % gridsize
        var north = grid[0][clamp((x-1)) * gridsize + y]
        var east = grid[0][x * gridsize + clamp(y + 1)]
        var south = grid[0][clamp(x+1) * gridsize + y]
        var west = grid[0][x * gridsize + clamp(y - 1)]

        grid[1][i] = cross(sub(north, south), sub(west, east))
    }

    // normalize normals
    for (let i = 0; i < grid[1].length; i++) {
        grid[1][i] = normalize(grid[1][i])
    }

    return {
        attributes: grid,
        triangles: elements
    }
}

function add_fault(grid) {
    return grid
}

/** Compute any time-varying or animated aspects of the scene */
function tick(milliseconds) {
    let seconds = milliseconds / 1000;
    if (terrain != null) {
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

    window.terrain = null
    document.querySelector('#submit').addEventListener('click', event => {
        const gridsize = Number(document.querySelector('#gridsize').value) || 2
        const faults = Number(document.querySelector('#faults').value) || 0
        // TODO: generate a new gridsize-by-gridsize grid here, then apply faults to it
        window.terrain = setup_geometry(generate_terrain(gridsize, faults))
    })
    
    fillScreen()
    window.addEventListener('resize', fillScreen)
    requestAnimationFrame(tick)
})
