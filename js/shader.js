const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
const width = 190.0;
const height = 190.0;

renderer.setSize(width, height);
document.body.appendChild(renderer.domElement);

// Create a plane to apply the shader
const geometry = new THREE.PlaneGeometry(2, 2); // Plane covers the entire view

// Optimized vertex shader (no changes needed here)
const vertexShader = `
    void main() {
        gl_Position = vec4(position, 1.0);
    }
`;

// Optimized fragment shader
const fragmentShader = `
    uniform float u_time;
    uniform float u_height;
    uniform float u_width;

    #define PI 3.14159265358979323846
    #define MAX_ITERATIONS 100.0
    #define ESCAPE_RADIUS_SQUARED 4.0

    vec2 squareC(vec2 c) {
        return vec2(c.x * c.x - c.y * c.y, 2.0 * c.x * c.y);
    }

    void main() {
        // Compute the normalized screen coordinates (from -0.5 to 0.5)
        vec2 uv = (gl_FragCoord.xy / vec2(u_width, u_height)) - 0.5;
        vec2 coordsC = uv * 0.8; // Apply zoom (adjust as needed)

        // Initialize the Mandelbrot calculation
        vec2 num = coordsC;
        float oscillator = 0.015 * sin(u_time / 3.0 - PI / 2.0) + 0.56;
        float c = -oscillator;

        float i;
        for (i = 0.0; i < MAX_ITERATIONS; i++) {
            num = squareC(num) + c;
            if (dot(num, num) > ESCAPE_RADIUS_SQUARED) break;
        }

        // Color based on the number of iterations (smoothstep for better anti-aliasing)
        float val = smoothstep(0.0, 1.0, i / MAX_ITERATIONS);
        vec3 col = vec3(val, 0.2 + (val / 9.0), 0.3);
        gl_FragColor = vec4(col, 1.0);
    }
`;

// Shader material with uniforms
const shaderMaterial = new THREE.ShaderMaterial({
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    uniforms: {
        u_time: { value: 1.0 },
        u_width: { value: width },
        u_height: { value: height }
    }
});

// Create a plane mesh and add it to the scene
const plane = new THREE.Mesh(geometry, shaderMaterial);
scene.add(plane);
camera.position.z = 1; // Position the camera to see the plane

// Animation loop
let lastTime = 0;
function animate(time) {
    time *= 0.001; // Convert time to seconds

    // Update u_time only once every ~16ms (60fps limit)
    if (time - lastTime >= 1 / 60) {
        lastTime = time;
        shaderMaterial.uniforms.u_time.value = time;
        renderer.render(scene, camera);
    }

    requestAnimationFrame(animate);
}

// Start the animation
animate();
