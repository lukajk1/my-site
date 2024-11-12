const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
const width = 330.;
const height = 330.;

renderer.setSize(width, height);
//renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Create a plane to apply the shader
const geometry = new THREE.PlaneGeometry(2, 2); // Plane covers the entire view

// vertex shader outputs vertex positions in clip space. outputs xyz and w for perspective division (?)
const vertexShader = `
    void main() {
        gl_Position = vec4(position, 1.0);
    }
`;

// frag shader calculates pixel color, running for each in parallel. outputs rbga (vec4).
const fragmentShader = `
    uniform float u_time;
    uniform float u_height;
    uniform float u_width;

    const int MAX_STEPS = 70;
    const float MAX_DIST = 100.0;
    const float SURF_DIST_MARGIN = .01;

    //struct Sphere {
    //    vec3 pos;
    //    float radius;
    //    vec3 col;
    //}

    //Sphere MakeSphere(vec3 pos, float radius, vec3 col) {
    //    Sphere mySphere;
    //    mySphere.pos = pos;
    //    mySphere.radius = radius;
    //    mySphere.col = col;
    //    return mySphere;
    //}

    float getDistFromSceneObjs(vec3 pos) {
        vec4 sphere = vec4(0, 1.45, 4.5, 1);

        float distFromSphereOrigin = length(pos - sphere.xyz) - sphere.w;
        float distFromPlane = pos.y;

        float dist = min(distFromSphereOrigin, distFromPlane);
        return dist;
    }

    float rayMarch(vec3 rayOrigin, vec3 rayDir) {
        float distOffset = 0.0;

        for(int i=0; i<MAX_STEPS; i++) {
            vec3 currentPos = rayOrigin + rayDir * distOffset;
            float distToSurface = getDistFromSceneObjs(currentPos);
            distOffset += distToSurface;

            if (distOffset > MAX_DIST || distToSurface < SURF_DIST_MARGIN) break;
        }

        return distOffset;
    }

    void main() {
        vec2 uv = vec2((gl_FragCoord.x / u_width)-.5, (gl_FragCoord.y / u_height)-.5);

        vec3 rayOrigin = vec3(0, 1.3, 0);
        vec3 rayDir = normalize(vec3(uv.x, uv.y, 1));
        /* z is depth, x width, y height naturally. So these vectors are angled based on the current
        screencoords */

        float distToSurf = rayMarch(rayOrigin, rayDir);
        vec3 hitPoint = rayOrigin + rayDir * distToSurf;

        //float oscillating = 0.5 * (sin(iTime) + 1.); // oscillates smoothly between 0 and 1

        float distFromCam = length(hitPoint - rayOrigin);
        float scaledDistFromCam = distFromCam / 11.2;

        //col = vec3(scaledDistFromCam, .5, .8);

        scaledDistFromCam = distFromCam;
        vec3 col = vec3(sin(scaledDistFromCam-(u_time/1.4)), 0.3, 0.5);
        //vec3 col = vec3(1, 0.5, 1); 

        gl_FragColor = vec4(col, 1.0);
    }


`;

const shaderMaterial = new THREE.ShaderMaterial({
    vertexShader: vertexShader,
    fragmentShader: fragmentShader,
    uniforms: {
        u_time: { value: 1.0 },
        u_width: { value: width },
        u_height: { value: height }
    }
});

const plane = new THREE.Mesh(geometry, shaderMaterial);
const plane2 = new THREE.Mesh(geometry, shaderMaterial);
scene.add(plane);
scene.add(plane2);
camera.position.z = 1; // Position the camera to see the plane

function animate(time) {
    time *= 0.001; // Convert time to seconds

    shaderMaterial.uniforms.u_time.value = time;
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}
animate();
